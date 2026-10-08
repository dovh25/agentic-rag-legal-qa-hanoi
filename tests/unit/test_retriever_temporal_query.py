from datetime import date
from types import SimpleNamespace

from src.agent.retriever import HybridRetriever


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
