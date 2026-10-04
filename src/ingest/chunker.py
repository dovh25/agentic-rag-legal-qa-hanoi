from dataclasses import dataclass
from typing import Any

from src.ingest.parser import ParsedDocument


@dataclass
class LegalChunk:
    chunk_id: str
    text: str
    breadcrumb: str
    metadata: dict[str, Any]


class LegalChunker:
    """Context-Injected Hierarchical Chunker for Vietnamese legal documents."""

    def __init__(self, corpus_version: str = "2026-10-04.1"):
        self.corpus_version = corpus_version

    def chunk_document(self, doc: ParsedDocument) -> list[LegalChunk]:
        """Convert a ParsedDocument into an indexed list of contextualized LegalChunks."""
        chunks: list[LegalChunk] = []
        chunk_index = 0

        for article in doc.articles:
            # Build article breadcrumb prefix
            chapter_info = (
                f" > [Chương {article.chapter_number}: {article.chapter_title}]"
                if article.chapter_number
                else ""
            )
            base_breadcrumb = (
                f"[Văn bản: {doc.document_title}]{chapter_info} "
                f"> [Điều {article.article_number}: {article.article_title}]"
            )

            if not article.clauses:
                # Article without clauses
                chunk_index += 1
                chunk_id = f"{doc.doc_id}-d{article.article_number}"
                text_with_context = f"{base_breadcrumb}\n{article.full_text}"

                metadata = {
                    "doc_id": doc.doc_id,
                    "document_title": doc.document_title,
                    "document_number": doc.document_number,
                    "document_type": doc.document_type,
                    "issuing_body": doc.issuing_body,
                    "effective_date": doc.effective_date,
                    "expiry_date": None,
                    "legal_status": "active",
                    "administrative_area": doc.administrative_area,
                    "article_ref": f"Điều {article.article_number}",
                    "clause": None,
                    "chunk_index": chunk_index,
                    "source_url": doc.source_url,
                    "corpus_version": self.corpus_version,
                }

                chunks.append(
                    LegalChunk(
                        chunk_id=chunk_id,
                        text=text_with_context,
                        breadcrumb=base_breadcrumb,
                        metadata=metadata,
                    )
                )
                continue

            for clause in article.clauses:
                chunk_index += 1
                clause_label = f"Khoản {clause.clause_number}"
                full_breadcrumb = f"{base_breadcrumb} > [{clause_label}]"
                chunk_id = f"{doc.doc_id}-d{article.article_number}-k{clause.clause_number}"

                text_with_context = f"{full_breadcrumb}\n{clause.text}"

                metadata = {
                    "doc_id": doc.doc_id,
                    "document_title": doc.document_title,
                    "document_number": doc.document_number,
                    "document_type": doc.document_type,
                    "issuing_body": doc.issuing_body,
                    "effective_date": doc.effective_date,
                    "expiry_date": None,
                    "legal_status": "active",
                    "administrative_area": doc.administrative_area,
                    "article_ref": f"Điều {article.article_number}",
                    "clause": clause_label,
                    "chunk_index": chunk_index,
                    "source_url": doc.source_url,
                    "corpus_version": self.corpus_version,
                }

                chunks.append(
                    LegalChunk(
                        chunk_id=chunk_id,
                        text=text_with_context,
                        breadcrumb=full_breadcrumb,
                        metadata=metadata,
                    )
                )

        return chunks
