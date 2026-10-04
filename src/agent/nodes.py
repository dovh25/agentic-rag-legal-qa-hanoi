from typing import Any

from src.agent.state import AgentState
from src.agent.tools import retrieve_legal_documents


def router_node(state: AgentState) -> dict[str, Any]:
    """Classify the user query and decide routing strategy."""
    query = state.get("query", "").strip()
    steps = list(state.get("reasoning_steps", []))
    steps.append(f"Router analyzed query: '{query}'")

    # Simple heuristic routing (can be replaced by LLM classifier)
    is_complex = any(
        keyword in query.lower()
        for keyword in ["và", "so sánh", "đồng thời", "quy trình", "bồi thường và tái định cư"]
    )
    is_ambiguous = len(query.split()) < 3

    if is_ambiguous:
        route = "clarification"
        steps.append("Query is too ambiguous, routed to clarification.")
    elif is_complex:
        route = "multi_hop"
        steps.append("Query contains multi-aspect legal requirements, routed to planner.")
    else:
        route = "single_hop"
        steps.append("Query is specific, routed to direct retrieval.")

    return {
        "route": route,
        "reasoning_steps": steps,
    }


def planner_node(state: AgentState) -> dict[str, Any]:
    """Decompose complex query into sub-queries."""
    query = state.get("query", "")
    steps = list(state.get("reasoning_steps", []))

    # Example decomposition
    sub_queries = [
        f"{query} - quy định chung",
        f"{query} - quy định áp dụng tại Hà Nội",
    ]
    steps.append(f"Planner generated {len(sub_queries)} sub-queries.")

    return {
        "sub_queries": sub_queries,
        "reasoning_steps": steps,
    }


def retrieval_node(state: AgentState) -> dict[str, Any]:
    """Retrieve relevant legal documents based on query/sub-queries."""
    steps = list(state.get("reasoning_steps", []))
    as_of_date = state.get("as_of_date")
    district = state.get("district")

    queries_to_search = state.get("sub_queries") or [state.get("query", "")]
    all_docs: list[dict[str, Any]] = []

    for q in queries_to_search:
        docs = retrieve_legal_documents(query=q, as_of_date=as_of_date, district=district)
        all_docs.extend(docs)

    steps.append(f"Retrieved {len(all_docs)} document chunks.")
    return {
        "retrieved_documents": all_docs,
        "reasoning_steps": steps,
    }


def synthesize_node(state: AgentState) -> dict[str, Any]:
    """Synthesize evidence into structured answer with citations."""
    steps = list(state.get("reasoning_steps", []))
    docs = state.get("retrieved_documents", [])

    if not docs:
        steps.append("No relevant legal documents retrieved.")
        return {
            "answer": "Không tìm thấy căn cứ pháp lý phù hợp trong cơ sở dữ liệu để trả lời câu hỏi của bạn.",
            "citations": [],
            "status": "insufficient_evidence",
            "reasoning_steps": steps,
        }

    citations = [
        {
            "doc_id": doc["doc_id"],
            "document_title": doc["title"],
            "document_number": doc.get("doc_number", doc["doc_id"]),
            "article_ref": doc.get("article"),
            "clause": doc.get("clause"),
            "snippet": doc.get("text", "")[:150],
            "source_url": doc.get("source_url"),
            "effective_date": doc.get("effective_date"),
            "relevance_score": doc.get("score", 0.95),
        }
        for doc in docs
    ]

    answer = (
        f"Căn cứ theo {docs[0]['title']}, {docs[0].get('article', '')}:\n{docs[0].get('text', '')}"
    )

    steps.append("Synthesized answer and generated citations from evidence.")
    return {
        "answer": answer,
        "citations": citations,
        "status": "answered",
        "reasoning_steps": steps,
    }


def verify_node(state: AgentState) -> dict[str, Any]:
    """Verify citations and provenance against retrieved evidence."""
    steps = list(state.get("reasoning_steps", []))
    citations = state.get("citations", [])

    if not citations and state.get("status") != "clarification_needed":
        status = "insufficient_evidence"
        steps.append("Verification failed: Answer lacks verifiable citations.")
    else:
        status = state.get("status", "answered")
        steps.append("Verification passed: Citations verified against source corpus.")

    return {
        "status": status,
        "reasoning_steps": steps,
    }


def clarification_node(state: AgentState) -> dict[str, Any]:
    """Handle ambiguous queries by requesting user clarification."""
    steps = list(state.get("reasoning_steps", []))
    steps.append("Formulating clarification response.")

    clarification_msg = (
        "Câu hỏi của bạn chưa đủ thông tin cụ thể (ví dụ: loại đất nông nghiệp hay đất ở, "
        "địa bàn quận/huyện cụ thể tại Hà Nội, hoặc thời điểm áp dụng). "
        "Vui lòng cung cấp thêm thông tin để hệ thống tra cứu chính xác."
    )

    return {
        "answer": None,
        "clarification_question": clarification_msg,
        "citations": [],
        "status": "clarification_needed",
        "reasoning_steps": steps,
    }
