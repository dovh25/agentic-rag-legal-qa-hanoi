from datetime import date
from types import SimpleNamespace

import pytest

from src.agent.retriever import HybridRetriever
from src.ingest.indexer import CollectionDimensionMismatchError


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
        def get_collection(self, **kwargs):
            return SimpleNamespace(
                config=SimpleNamespace(
                    params=SimpleNamespace(
                        vectors=SimpleNamespace(size=retriever.settings.EMBEDDING_DIMENSION)
                    )
                )
            )

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
    monkeypatch.setattr(
        retriever.indexer,
        "generate_embeddings",
        lambda texts, task_type="RETRIEVAL_DOCUMENT": [
            [0.0] * retriever.settings.EMBEDDING_DIMENSION
        ],
    )
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
        def get_collection(self, **kwargs):
            return SimpleNamespace(
                config=SimpleNamespace(
                    params=SimpleNamespace(
                        vectors=SimpleNamespace(size=retriever.settings.EMBEDDING_DIMENSION)
                    )
                )
            )

        def query_points(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(points=[SimpleNamespace(payload={}, score=0.9)])

    retriever = HybridRetriever()
    monkeypatch.setattr(retriever, "get_client", lambda: FakeClient())
    monkeypatch.setattr(
        retriever.indexer,
        "generate_embeddings",
        lambda texts, task_type="RETRIEVAL_DOCUMENT": [
            [0.0] * retriever.settings.EMBEDDING_DIMENSION
        ],
    )
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


def test_embedding_failure_does_not_fall_back_to_local_retrieval(monkeypatch):
    retriever = HybridRetriever()

    class FakeClient:
        def get_collection(self, **kwargs):
            return SimpleNamespace(
                config=SimpleNamespace(
                    params=SimpleNamespace(
                        vectors=SimpleNamespace(size=retriever.settings.EMBEDDING_DIMENSION)
                    )
                )
            )

    def fail_embedding(*args, **kwargs):
        raise RuntimeError("Gemini unavailable")

    monkeypatch.setattr(retriever, "get_client", lambda: FakeClient())
    monkeypatch.setattr(retriever.indexer, "generate_embeddings", fail_embedding)
    monkeypatch.setattr(
        retriever,
        "_offline_retrieve",
        lambda *args, **kwargs: pytest.fail("must not hide embedding failure"),
    )
    retriever._is_connected = True

    with pytest.raises(RuntimeError, match="Gemini unavailable"):
        retriever.retrieve("quy định bồi thường đất")


def test_retriever_rejects_legacy_collection_dimension(monkeypatch):
    retriever = HybridRetriever()

    class FakeClient:
        def get_collection(self, **kwargs):
            return SimpleNamespace(
                config=SimpleNamespace(params=SimpleNamespace(vectors=SimpleNamespace(size=1024)))
            )

    monkeypatch.setattr(retriever, "get_client", lambda: FakeClient())
    monkeypatch.setattr(retriever.indexer, "generate_embeddings", lambda *args, **kwargs: [])
    retriever._is_connected = True

    with pytest.raises(CollectionDimensionMismatchError, match="versioned collection"):
        retriever.retrieve("quy định bồi thường đất")


def test_retriever_extracts_multiple_explicit_documents():
    from src.agent.retriever import extract_requested_doc_ids

    assert extract_requested_doc_ids(
        "Bồi thường theo Luật Đất đai 2024 và Nghị định 88/2024/NĐ-CP"
    ) == ["88-2024-ND-CP", "31-2024-QH15"]
    assert extract_requested_doc_ids("So sánh Luật Đất đai 2013 và Luật Đất đai 2024") == [
        "31-2024-QH15",
        "45-2013-QH13",
    ]


def test_production_retrieval_does_not_fall_back_when_qdrant_is_unavailable(monkeypatch):
    retriever = HybridRetriever()
    monkeypatch.setattr(retriever.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(retriever, "get_client", lambda: None)
    monkeypatch.setattr(
        retriever,
        "_offline_retrieve",
        lambda *args, **kwargs: pytest.fail("production must not use local corpus"),
    )

    with pytest.raises(RuntimeError, match="refusing to fall back"):
        retriever.retrieve("Hỏi về bồi thường đất")


def test_production_retrieval_propagates_qdrant_search_errors(monkeypatch):
    retriever = HybridRetriever()
    monkeypatch.setattr(retriever.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        retriever,
        "validate_collection_dimension",
        lambda client: None,
    )
    monkeypatch.setattr(
        retriever.indexer,
        "generate_embeddings",
        lambda *args, **kwargs: [[0.0] * retriever.settings.EMBEDDING_DIMENSION],
    )

    class FailingClient:
        def get_collection(self, **kwargs):
            return SimpleNamespace()

        def query_points(self, **kwargs):
            raise OSError("vector database unavailable")

    monkeypatch.setattr(retriever, "get_client", lambda: FailingClient())
    monkeypatch.setattr(
        retriever,
        "_offline_retrieve",
        lambda *args, **kwargs: pytest.fail("production must not use local corpus"),
    )
    retriever._is_connected = True

    with pytest.raises(RuntimeError, match="Production Qdrant retrieval is unavailable"):
        retriever.retrieve("Hỏi về bồi thường đất")
