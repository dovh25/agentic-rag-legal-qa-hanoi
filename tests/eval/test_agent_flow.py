from types import SimpleNamespace

from src.agent.graph import create_agent_graph
from src.agent.nodes import grader_node, planner_node
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
    assert result["citations"][0]["doc_id"] in ["31-2024-QH15", "88-2024-ND-CP", "61-2024-QD-UBND"]
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


def test_agent_rejects_unrelated_query_with_generic_document_word():
    result = create_agent_graph().invoke(
        {
            "query": "Thủ tục xin visa du học Mỹ cần giấy tờ gì?",
            "reasoning_steps": [],
        }
    )

    assert result["status"] == "insufficient_evidence"
    assert result.get("citations", []) == []


def test_grader_prioritizes_exact_legal_topic_over_high_scoring_noise():
    result = grader_node(
        {
            "query": "Hạn mức giao đất ở cho cá nhân tại quận Cầu Giấy theo Quyết định 61/2024",
            "reasoning_steps": [],
            "retrieved_documents": [
                {
                    "doc_id": "61-2024-QD-UBND",
                    "article_ref": "Điều 18",
                    "text": "Bồi thường, hỗ trợ về đất nông nghiệp tại thành phố Hà Nội.",
                    "score": 0.9,
                },
                {
                    "doc_id": "61-2024-QD-UBND",
                    "article_ref": "Điều 14",
                    "text": (
                        "Điều 14: Hạn mức giao đất ở cho cá nhân tại thành phố Hà Nội. "
                        "Tại các phường thuộc các quận: không quá 90 m2/cá nhân."
                    ),
                    "score": 0.06,
                },
            ],
        }
    )

    assert [doc["article_ref"] for doc in result["retrieved_documents"]] == ["Điều 14"]


def test_grader_abstains_when_specific_query_topic_has_no_matching_evidence():
    result = grader_node(
        {
            "query": "Hạn mức giao đất ở cho cá nhân tại quận Cầu Giấy?",
            "reasoning_steps": [],
            "retrieved_documents": [
                {
                    "doc_id": "61-2024-QD-UBND",
                    "article_ref": "Điều 18",
                    "text": "Bồi thường, hỗ trợ về đất nông nghiệp tại thành phố Hà Nội.",
                    "score": 0.9,
                }
            ],
        }
    )

    assert result["status"] == "insufficient_evidence"
    assert result["retrieved_documents"] == []


def test_planner_respects_configured_maximum_and_keeps_district(monkeypatch):
    monkeypatch.setattr("src.agent.nodes.get_settings", lambda: SimpleNamespace(MAX_SUBQUERIES=3))
    result = planner_node(
        {
            "query": "So sánh thu hồi đất, bồi thường, tái định cư và giá đất",
            "district": "Đông Anh",
            "reasoning_steps": [],
        }
    )

    assert 1 <= len(result["sub_queries"]) <= 3
    assert all("Đông Anh" in query for query in result["sub_queries"])


def test_document_validity():
    # Valid document
    val = check_document_validity("31-2024-QH15", as_of_date="2026-10-04")
    assert val["is_valid"] is True
    assert val["status"] == "Còn hiệu lực"

    # Pre-effective date
    val_early = check_document_validity("31-2024-QH15", as_of_date="2023-01-01")
    assert val_early["is_valid"] is False
    assert "Chưa có hiệu lực" in val_early["status"]
