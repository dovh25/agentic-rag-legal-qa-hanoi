import json

from eval.scripts.run_eval import evaluate_dataset


def test_evaluator_checks_gold_clause_retrieval_and_abstention(tmp_path):
    dataset = tmp_path / "gold.jsonl"
    dataset.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "gold-1",
                        "query": "Hạn mức giao đất ở?",
                        "expected_status": "answered",
                        "expected_route": "single_hop",
                        "gold_citations": [
                            {
                                "doc_number": "61/2024/QĐ-UBND",
                                "article_ref": "Điều 14",
                                "clause": "Khoản 1",
                            }
                        ],
                    }
                ),
                json.dumps(
                    {
                        "id": "gold-2",
                        "query": "Câu hỏi ngoài phạm vi",
                        "expected_status": "insufficient_evidence",
                        "expected_route": "single_hop",
                        "expected_doc_ids": [],
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    class FakeGraph:
        def invoke(self, state):
            if state["query"] == "Hạn mức giao đất ở?":
                evidence = {
                    "doc_id": "61-2024-QD-UBND",
                    "document_number": "61/2024/QĐ-UBND",
                    "article_ref": "Điều 14",
                    "clause": "Khoản 1",
                }
                return {
                    "status": "answered",
                    "route": "single_hop",
                    "retrieved_documents": [evidence],
                    "citations": [evidence],
                    "processing_time_ms": 100,
                }
            return {
                "status": "insufficient_evidence",
                "route": "single_hop",
                "retrieved_documents": [],
                "citations": [],
                "processing_time_ms": 20,
            }

    report = evaluate_dataset(str(dataset), graph=FakeGraph())

    assert report["passed_cases"] == 2
    assert report["retrieval_recall_at_5"] == 1.0
    assert report["gold_citation_recall"] == 1.0
    assert report["citation_accuracy"] == 1.0
    assert report["abstention_precision"] == 1.0
    assert report["grounded_citation_rate"] == 1.0
    assert report["p95_graph_duration_ms"] >= 0
    assert report["p95_agent_reported_ms"] == 100.0
    assert "excludes external HTTP" in report["latency_scope"]


def test_evaluator_requires_all_expected_documents_in_citations(tmp_path):
    dataset = tmp_path / "gold.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "multi-hop",
                "query": "Compare legal texts",
                "expected_status": "answered",
                "expected_doc_ids": ["31-2024-QH15", "88-2024-ND-CP"],
            }
        ),
        encoding="utf-8",
    )

    class FakeGraph:
        def invoke(self, state):
            return {
                "status": "answered",
                "retrieved_documents": [
                    {"doc_id": "31-2024-QH15"},
                    {"doc_id": "88-2024-ND-CP"},
                ],
                "citations": [{"doc_id": "31-2024-QH15"}],
            }

    report = evaluate_dataset(str(dataset), graph=FakeGraph())

    assert report["retrieval_recall_at_5"] == 1.0
    assert report["passed_cases"] == 0
    assert report["cases"][0]["gold_citation_match"] is False
