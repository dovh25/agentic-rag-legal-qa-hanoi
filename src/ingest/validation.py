import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.ingest.schema import LegalChunkPayload, LegalDocumentRecord


@dataclass
class ValidationIssue:
    level: str
    code: str
    message: str
    context: str | None = None


@dataclass
class ValidationReport:
    documents: int
    chunks: int
    issues: list[ValidationIssue]

    @property
    def valid(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)

    def write(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(
                {
                    "documents": self.documents,
                    "chunks": self.chunks,
                    "valid": self.valid,
                    "issues": [asdict(issue) for issue in self.issues],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def validate_records(
    documents: list[dict[str, Any]], chunks: list[dict[str, Any]]
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    chunk_ids: set[str] = set()

    for document in documents:
        try:
            LegalDocumentRecord.model_validate(document)
        except ValidationError as error:
            issues.append(
                ValidationIssue(
                    "error",
                    "invalid_document",
                    str(error),
                    str(document.get("doc_id", "<unknown>")),
                )
            )

    for chunk in chunks:
        try:
            LegalChunkPayload.model_validate(chunk)
        except ValidationError as error:
            issues.append(
                ValidationIssue(
                    "error",
                    "invalid_chunk",
                    str(error),
                    str(chunk.get("chunk_id", "<unknown>")),
                )
            )
        chunk_id = str(chunk.get("chunk_id", ""))
        if chunk_id in chunk_ids:
            issues.append(ValidationIssue("error", "duplicate_chunk_id", chunk_id, chunk_id))
        chunk_ids.add(chunk_id)

    return ValidationReport(len(documents), len(chunks), issues)
