from typing import Any

from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """LangGraph State representation for the Legal QA agent conforming to PRD specifications."""

    query: str
    as_of_date: str | None
    as_of_date_applied: str | None
    district: str | None
    max_results: int
    route: str  # "single_hop", "multi_hop", "clarification"
    sub_queries: list[str]
    retrieved_documents: list[dict[str, Any]]
    answer: str | None
    citations: list[dict[str, Any]]
    status: str  # "answered", "insufficient_evidence", "clarification_needed"
    clarification_question: str | None
    reasoning_steps: list[str]
    processing_time_ms: float | None
    error: str | None
