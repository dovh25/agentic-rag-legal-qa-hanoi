import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParsedClause:
    clause_number: str  # e.g., "1", "2"
    clause_title: str
    text: str
    points: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ParsedArticle:
    article_number: str  # e.g., "79", "14"
    article_title: str  # e.g., "Thu hồi đất để phát triển kinh tế..."
    chapter_number: str | None = None
    chapter_title: str | None = None
    full_text: str = ""
    clauses: list[ParsedClause] = field(default_factory=list)


@dataclass
class ParsedDocument:
    doc_id: str
    document_title: str
    document_number: str
    document_type: str
    issuing_body: str
    effective_date: str
    source_url: str
    administrative_area: list[str]
    articles: list[ParsedArticle] = field(default_factory=list)


class VietnameseLegalParser:
    """Parser for Vietnamese legal documents conforming to official legislative structures."""

    # Regex patterns for Vietnamese legislative documents
    CHAPTER_WITH_TITLE = re.compile(
        r"^(?:Chương|CHƯƠNG)\s+([IVXLCDM\d]+)[:\.\s\-]+([^\n]+)", re.IGNORECASE
    )
    CHAPTER_STANDALONE = re.compile(r"^(?:Chương|CHƯƠNG)\s+([IVXLCDM\d]+)\.?$", re.IGNORECASE)
    ARTICLE_PATTERN = re.compile(r"^(?:Điều|ĐIỀU)\s+(\d+)[\.:\s\-]+([^\n]+)", re.IGNORECASE)
    CLAUSE_PATTERN = re.compile(r"^(\d+)\.\s+([^\n]+)", re.MULTILINE)
    POINT_PATTERN = re.compile(r"^([a-zđ])\)\s+([^\n]+)", re.MULTILINE)

    def parse(self, text: str, metadata: dict[str, Any]) -> ParsedDocument:
        """Parse raw text into hierarchical articles and clauses."""
        doc = ParsedDocument(
            doc_id=metadata.get("doc_id", ""),
            document_title=metadata.get("document_title", ""),
            document_number=metadata.get("document_number", ""),
            document_type=metadata.get("document_type", "luat"),
            issuing_body=metadata.get("issuing_body", ""),
            effective_date=metadata.get("effective_date", ""),
            source_url=metadata.get("source_url", ""),
            administrative_area=metadata.get("administrative_area", ["Hà Nội"]),
        )

        lines = text.split("\n")
        current_chapter_num: str | None = None
        current_chapter_title: str | None = None
        waiting_for_chapter_title: bool = False

        current_article: ParsedArticle | None = None
        article_lines: list[str] = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Capture chapter title if previous line was standalone chapter number
            if waiting_for_chapter_title:
                waiting_for_chapter_title = False
                if not self.ARTICLE_PATTERN.match(line_str):
                    current_chapter_title = line_str
                    continue

            # Check Chapter with title on same line
            chap_match = self.CHAPTER_WITH_TITLE.match(line_str)
            if chap_match:
                current_chapter_num = chap_match.group(1).strip()
                current_chapter_title = chap_match.group(2).strip()
                waiting_for_chapter_title = False
                continue

            # Check Standalone Chapter (number only)
            chap_standalone = self.CHAPTER_STANDALONE.match(line_str)
            if chap_standalone:
                current_chapter_num = chap_standalone.group(1).strip()
                current_chapter_title = None
                waiting_for_chapter_title = True
                continue

            # Check Article
            art_match = self.ARTICLE_PATTERN.match(line_str)
            if art_match:
                if current_article:
                    current_article.full_text = "\n".join(article_lines).strip()
                    current_article.clauses = self._parse_clauses(article_lines)
                    doc.articles.append(current_article)

                art_num = art_match.group(1).strip()
                art_title = art_match.group(2).strip()
                current_article = ParsedArticle(
                    article_number=art_num,
                    article_title=art_title,
                    chapter_number=current_chapter_num,
                    chapter_title=current_chapter_title,
                )
                article_lines = [line_str]
            else:
                if current_article:
                    article_lines.append(line_str)

        # Flush last article
        if current_article:
            current_article.full_text = "\n".join(article_lines).strip()
            current_article.clauses = self._parse_clauses(article_lines)
            doc.articles.append(current_article)

        return doc

    def _parse_clauses(self, lines: list[str]) -> list[ParsedClause]:
        """Extract Khoản (clauses) and Điểm (points) within an article."""
        clauses: list[ParsedClause] = []
        current_clause: ParsedClause | None = None
        clause_lines: list[str] = []

        # Skip the first line which is the Article title
        body_lines = lines[1:] if len(lines) > 1 else lines

        for line in body_lines:
            clause_match = self.CLAUSE_PATTERN.match(line)
            if clause_match:
                if current_clause:
                    current_clause.text = "\n".join(clause_lines).strip()
                    clauses.append(current_clause)

                clause_num = clause_match.group(1)
                clause_text = clause_match.group(2)
                current_clause = ParsedClause(
                    clause_number=clause_num,
                    clause_title=f"Khoản {clause_num}",
                    text=clause_text,
                )
                clause_lines = [line]
            else:
                if current_clause:
                    clause_lines.append(line)
                    # Check for point a), b), c)...
                    pt_match = self.POINT_PATTERN.match(line)
                    if pt_match:
                        current_clause.points.append(
                            {"point": pt_match.group(1), "text": pt_match.group(2)}
                        )
                else:
                    clause_lines.append(line)

        if current_clause:
            current_clause.text = "\n".join(clause_lines).strip()
            clauses.append(current_clause)
        elif clause_lines:
            # Article without explicit clause numbers (Treat entire article body as single clause)
            clauses.append(
                ParsedClause(
                    clause_number="1",
                    clause_title="Toàn văn Điều",
                    text="\n".join(clause_lines).strip(),
                )
            )

        return clauses
