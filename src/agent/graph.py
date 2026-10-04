from langgraph.graph import END, START, StateGraph

from src.agent.nodes import (
    clarification_node,
    grader_node,
    planner_node,
    retrieval_node,
    router_node,
    synthesize_node,
    verify_node,
)
from src.agent.state import AgentState


def router_decision(state: AgentState) -> str:
    """Decide next step based on router outcome."""
    route = state.get("route", "single_hop")
    if route == "clarification":
        return "clarification"
    elif route == "multi_hop":
        return "planner"
    return "retrieval"


def grader_decision(state: AgentState) -> str:
    """Decide whether to proceed to synthesis or abstain (Zero Hallucination)."""
    status = state.get("status")
    docs = state.get("retrieved_documents", [])
    if status == "insufficient_evidence" or not docs:
        return "insufficient_evidence"
    return "synthesize"


def create_agent_graph() -> StateGraph:
    """Construct and compile the Hanoi Legal QA LangGraph agent state graph."""
    workflow = StateGraph(AgentState)

    # 1. Add all functional nodes
    workflow.add_node("router", router_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("grader", grader_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("clarification", clarification_node)

    # 2. Add edges & conditional transitions
    workflow.add_edge(START, "router")

    workflow.add_conditional_edges(
        "router",
        router_decision,
        {
            "clarification": "clarification",
            "planner": "planner",
            "retrieval": "retrieval",
        },
    )

    workflow.add_edge("planner", "retrieval")
    workflow.add_edge("retrieval", "grader")

    workflow.add_conditional_edges(
        "grader",
        grader_decision,
        {
            "synthesize": "synthesize",
            "insufficient_evidence": END,
        },
    )

    workflow.add_edge("synthesize", "verify")
    workflow.add_edge("verify", END)
    workflow.add_edge("clarification", END)

    return workflow.compile()


# Compile default agent graph instance
legal_qa_graph = create_agent_graph()
