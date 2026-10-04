from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ResponseStatus(StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CLARIFICATION_NEEDED = "clarification_needed"


class LegalCitation(BaseModel):
    """Citation linking answer claims directly to source legal documents."""

    doc_id: str = Field(..., description="Document identifier, e.g., 'Luat-Dat-dai-2024'")
    title: str = Field(..., description="Official title of the legal document")
    article: str | None = Field(None, description="Article number or name, e.g., 'Điều 79'")
    clause: str | None = Field(None, description="Clause or paragraph, e.g., 'Khoản 2'")
    snippet: str = Field(..., description="Exact textual excerpt used as evidence")
    source_url: str | None = Field(None, description="Official portal verification URL")
    effective_date: str | None = Field(None, description="Effective date (YYYY-MM-DD)")


class LegalQARequest(BaseModel):
    """Incoming user legal question request."""

    query: str = Field(
        ..., min_length=3, description="Legal question regarding land, planning, compensation, etc."
    )
    as_of_date: str | None = Field(
        None, description="Target legal validity date (YYYY-MM-DD). Defaults to query date."
    )
    district: str | None = Field(
        None, description="Specific Hanoi district/town (e.g., 'Long Biên', 'Hoàn Kiếm')"
    )
    include_reasoning_steps: bool = Field(
        default=True, description="Whether to include agent reasoning steps in response"
    )


class LegalQAResponse(BaseModel):
    """Outgoing response for legal question answering."""

    query: str
    status: ResponseStatus
    answer: str
    citations: list[LegalCitation] = Field(default_factory=list)
    reasoning_steps: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
