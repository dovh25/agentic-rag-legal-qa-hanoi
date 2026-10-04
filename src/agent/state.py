from typing import Any

from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """LangGraph State representation for the Legal QA agent."""

    query: str
    as_of_date: str | None
    district: str | None
    route: str  # "single_hop", "multi_hop", "clarification"
    sub_queries: list[str]
    retrieved_documents: list[dict[str, Any]]
    answer: str
    citations: list[dict[str, Any]]
    status: str  # "answered", "insufficient_evidence", "clarification_needed"
    reasoning_steps: list[str]
    error: str | None
