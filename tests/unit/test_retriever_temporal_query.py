from datetime import date
from types import SimpleNamespace

from src.agent.retriever import HybridRetriever


def test_low_confidence_dense_search_falls_back_to_exact_topic_match(monkeypatch):
    relevant = SimpleNamespace(
        payload={
            "doc_id": "61-2024-QD-UBND",
            "document_title": "Quyết định 61/2024/QĐ-UBND",
            "document_number": "61/2024/QĐ-UBND",
            "article_ref": "Điều 14",
            "clause": "Khoản 1",
            "text": "Điều 14: Hạn mức giao đất ở cho cá nhân tại thành phố Hà Nội.",
            "source_url": "https://congbao.hanoi.gov.vn/",
            "effective_date": "2024-10-07",
        }
    )
    irrelevant = SimpleNamespace(
        payload={
            "doc_id": "61-2024-QD-UBND",
            "document_title": "Quyết định 61/2024/QĐ-UBND",
            "document_number": "61/2024/QĐ-UBND",
            "article_ref": "Điều 18",
            "clause": "Khoản 2",
            "text": "Bồi thường, hỗ trợ về đất nông nghiệp tại thành phố Hà Nội.",
            "source_url": "https://congbao.hanoi.gov.vn/",
            "effective_date": "2024-10-07",
        }
    )

    class FakeClient:
        def query_points(self, **kwargs):
            return SimpleNamespace(
                points=[
                    SimpleNamespace(payload=irrelevant.payload, score=0.06),
                ]
            )

        def scroll(self, **kwargs):
            return [relevant, irrelevant], None

    retriever = HybridRetriever()
    monkeypatch.setattr(retriever, "get_client", lambda: FakeClient())
    monkeypatch.setattr(retriever.indexer, "generate_embeddings", lambda texts: [[0.0] * 1024])
    retriever._is_connected = True

    results = retriever.retrieve(
        "Hạn mức giao đất ở cho cá nhân theo Quyết định 61/2024",
        as_of_date="2026-10-08",
        district="Cầu Giấy",
    )

    assert [result["article_ref"] for result in results] == ["Điều 14"]


def test_qdrant_query_enforces_effective_and_expiry_dates(monkeypatch):
    captured = {}

    class FakeClient:
        def query_points(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(points=[SimpleNamespace(payload={}, score=0.9)])

    retriever = HybridRetriever()
    monkeypatch.setattr(retriever, "get_client", lambda: FakeClient())
    monkeypatch.setattr(retriever.indexer, "generate_embeddings", lambda texts: [[0.0] * 1024])
    retriever._is_connected = True

    retriever.retrieve(
        "quy định bồi thường đất",
        as_of_date="2024-10-07",
        district="Đông Anh",
    )

    query_filter = captured["query_filter"]
    assert query_filter.must[0].key == "legal_status"
    assert query_filter.must[1].key == "effective_date"
    assert query_filter.must[1].range.lte == date(2024, 10, 7)
    assert query_filter.must[2].key == "administrative_area"
    assert query_filter.must_not[0].key == "expiry_date"
    assert query_filter.must_not[0].range.lt == date(2024, 10, 7)
