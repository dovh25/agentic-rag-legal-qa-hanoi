from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class LegalDocumentType(StrEnum):
    LAW = "law"
    DECREE = "decree"
    DECISION = "decision"
    RESOLUTION = "resolution"
    CIRCULAR = "circular"
    GUIDANCE = "guidance"
    CASE = "case"


class LegalStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    AMENDED = "amended"
    EXPIRED = "expired"


class CorpusTier(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class LegalDocumentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=3)
    doc_number: str = Field(min_length=1)
    doc_title: str = Field(min_length=1)
    doc_type: LegalDocumentType
    issuing_body: str = Field(min_length=1)
    issued_date: date
    effective_from: date
    effective_to: date | None = None
    legal_status: LegalStatus = LegalStatus.ACTIVE
    replaced_by: str | None = None
    amended_by: list[str] = Field(default_factory=list)
    legal_domain: list[str] = Field(min_length=1)
    scope: str
    applicable_district: list[str] | None = None
    administrative_area: list[str] = Field(min_length=1)
    source_url: HttpUrl
    source_authority: str = Field(min_length=1)
    corpus_tier: CorpusTier
    snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_fetched_at: datetime | None = None
    parser_version: str = Field(min_length=1)
    corpus_version: str = Field(min_length=1)

    @field_validator("effective_to")
    @classmethod
    def validate_date_range(cls, value: date | None, info) -> date | None:
        effective_from = info.data.get("effective_from")
        if value and effective_from and value < effective_from:
            raise ValueError("effective_to must not precede effective_from")
        return value


class LegalChunkPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str
    doc_number: str
    doc_title: str
    doc_type: LegalDocumentType
    issuing_body: str
    issued_date: date
    effective_from: date
    effective_to: date | None = None
    legal_status: LegalStatus
    replaced_by: str | None = None
    amended_by: list[str] = Field(default_factory=list)
    legal_domain: list[str]
    scope: str
    applicable_district: list[str] | None = None
    administrative_area: list[str]
    chapter: str | None = None
    chapter_title: str | None = None
    section: str | None = None
    section_title: str | None = None
    article: str
    article_title: str | None = None
    clause: str | None = None
    point: str | None = None
    source_url: HttpUrl
    source_authority: str
    snapshot_sha256: str
    source_fetched_at: datetime | None = None
    quote_text: str
    chunk_id: str
    chunk_index: int = Field(ge=1)
    corpus_tier: CorpusTier
    corpus_version: str
