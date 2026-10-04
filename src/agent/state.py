from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """LangGraph State representation for the Legal QA agent."""
    query: str
    as_of_date: Optional[str]
    district: Optional[str]
    route: str  # "single_hop", "multi_hop", "clarification"
    sub_queries: List[str]
    retrieved_documents: List[Dict[str, Any]]
    answer: str
    citations: List[Dict[str, Any]]
    status: str  # "answered", "insufficient_evidence", "clarification_needed"
    reasoning_steps: List[str]
    error: Optional[str]
