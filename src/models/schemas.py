from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ResponseStatus(StrEnum):
    """Execution status returned by the Agentic RAG pipeline."""

    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CLARIFICATION_NEEDED = "clarification_needed"


class LegalCitation(BaseModel):
    """Citation linking answer claims directly to official legal sources."""

    doc_id: str = Field(..., description="Document identifier, e.g. '31-2024-QH15'")
    document_title: str = Field(..., description="Official title of the legal document")
    document_number: str = Field(
        default="", description="Official document number, e.g. '31/2024/QH15'"
    )
    article_ref: str | None = Field(None, description="Article reference, e.g. 'Điều 79'")
    clause: str | None = Field(None, description="Clause reference, e.g. 'Khoản 1'")
    snippet: str = Field(..., description="Exact textual excerpt used as evidence")
    source_url: str | None = Field(None, description="Official portal verification URL")
    effective_date: str | None = Field(None, description="Effective date (YYYY-MM-DD)")
    expiry_date: str | None = Field(None, description="Expiry date if superseded/amended")
    relevance_score: float | None = Field(None, description="Retrieval / Grader relevance score")

    @model_validator(mode="before")
    @classmethod
    def map_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map 'title' to 'document_title' if missing
            if "title" in data and "document_title" not in data:
                data["document_title"] = data["title"]
            # Map 'article' to 'article_ref' if missing
            if "article" in data and "article_ref" not in data:
                data["article_ref"] = data["article"]
            # Default document_number to doc_id if empty
            if not data.get("document_number") and "doc_id" in data:
                data["document_number"] = data["doc_id"]
        return data

    @property
    def title(self) -> str:
        return self.document_title

    @property
    def article(self) -> str | None:
        return self.article_ref


class LegalQARequest(BaseModel):
    """Incoming user legal question request conforming to PRD Section 10."""

    query: str = Field(
        ..., min_length=3, description="Legal question regarding land, planning, compensation, etc."
    )
    as_of_date: str | None = Field(
        None, description="Target legal validity date (YYYY-MM-DD). Defaults to current date."
    )
    district: str | None = Field(
        None, description="Specific Hanoi district/town (e.g. 'Hoàn Kiếm', 'Đông Anh')"
    )
    max_results: int = Field(
        default=5, ge=1, le=20, description="Maximum evidence chunks to retrieve"
    )
    session_id: str | None = Field(
        None, description="Optional conversation session ID for multi-turn chat"
    )
    include_reasoning_steps: bool = Field(
        default=True, description="Whether to include agent reasoning trace in response"
    )

    @field_validator("as_of_date")
    @classmethod
    def validate_as_of_date(cls, value: str | None) -> str | None:
        if value is not None:
            date.fromisoformat(value)
        return value


class LegalQAResponse(BaseModel):
    """Outgoing response for legal question answering conforming to PRD Section 10."""

    query: str
    status: ResponseStatus
    answer: str | None = Field(
        None, description="Grounded answer text (None if clarification needed)"
    )
    citations: list[LegalCitation] = Field(default_factory=list)
    reasoning_steps: list[str] = Field(default_factory=list)
    route: str | None = Field(
        None, description="Routing path: single_hop | multi_hop | clarification"
    )
    sub_queries: list[str] = Field(default_factory=list, description="Sub-queries if multi-hop")
    clarification_question: str | None = Field(
        None, description="Question asked to user when clarification is needed"
    )
    processing_time_ms: float | None = Field(None, description="Execution latency in milliseconds")
    as_of_date_applied: str | None = Field(None, description="Effective date applied for filtering")
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    """User feedback payload conforming to PRD Section 10.3."""

    query_id: str = Field(..., description="Query ID or UUID")
    rating: str = Field(..., description="'positive' or 'negative'")
    comment: str | None = Field(None, description="Optional user comment")

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"positive", "negative"}:
            raise ValueError("rating must be 'positive' or 'negative'")
        return normalized


class HealthResponse(BaseModel):
    """System health check conforming to PRD Section 10.2."""

    status: str = "healthy"
    version: str = "1.0.0"
    qdrant: str = "connected"
    llm: str = "connected"
    corpus_size: int = 1250
    active_collection: str = "legal_chunks"
    corpus_version: str | None = None
