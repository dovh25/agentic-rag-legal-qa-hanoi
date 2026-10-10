from src.agent.graph import create_agent_graph
from src.agent.tools import check_document_validity


def test_agent_graph_execution():
    graph = create_agent_graph()
    initial_state = {
        "query": "Quy định về thu hồi đất và bồi thường tái định cư tại Long Biên",
        "as_of_date": "2024-08-01",
        "district": "Long Biên",
        "reasoning_steps": [],
    }

    result = graph.invoke(initial_state)

    assert "answer" in result
    assert "citations" in result
    assert "status" in result
    assert result["status"] == "answered"
    assert len(result["citations"]) > 0
    # Check that citations have required fields
    for cit in result["citations"]:
        assert "doc_id" in cit
        assert "document_title" in cit
        assert "article_ref" in cit
        assert "snippet" in cit
        assert "source_url" in cit
    assert len(result["reasoning_steps"]) > 0


def test_agent_clarification_flow():
    graph = create_agent_graph()
    initial_state = {
        "query": "đất",  # ambiguous
        "reasoning_steps": [],
    }

    result = graph.invoke(initial_state)
    assert result["status"] == "clarification_needed"
    assert result.get("clarification_question") is not None
    assert "quận, huyện" in result["clarification_question"]


def test_agent_single_hop_flow():
    graph = create_agent_graph()
    initial_state = {
        "query": "Hạn mức giao đất ở tại quận Cầu Giấy theo quy định mới nhất?",
        "reasoning_steps": [],
    }

    result = graph.invoke(initial_state)
    assert result["route"] == "single_hop"
    assert result["district"] == "Cầu Giấy"
    assert result["status"] == "answered"
    assert len(result["citations"]) > 0


def test_agent_insufficient_evidence_flow():
    graph = create_agent_graph()
    # A completely unrelated non-legal question
    initial_state = {
        "query": "Công thức nấu phở bò gia truyền ngon nhất",
        "reasoning_steps": [],
    }

    result = graph.invoke(initial_state)
    assert result["status"] == "insufficient_evidence"
    assert len(result.get("citations", [])) == 0


def test_document_validity():
    # Valid document
    val = check_document_validity("31-2024-QH15", as_of_date="2026-10-04")
    assert val["is_valid"] is True
    assert val["status"] == "Còn hiệu lực"

    # Pre-effective date
    val_early = check_document_validity("31-2024-QH15", as_of_date="2023-01-01")
    assert val_early["is_valid"] is False
    assert "Chưa có hiệu lực" in val_early["status"]
