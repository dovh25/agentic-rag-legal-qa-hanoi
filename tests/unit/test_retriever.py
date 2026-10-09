from src.agent.retriever import HybridRetriever


def test_temporal_validity_excludes_documents_not_yet_effective():
    payload = {"effective_date": "2024-08-01", "expiry_date": None}

    assert HybridRetriever._is_valid_as_of(payload, "2024-08-01") is True
    assert HybridRetriever._is_valid_as_of(payload, "2024-07-31") is False


def test_temporal_validity_excludes_expired_documents():
    payload = {"effective_date": "2024-01-01", "expiry_date": "2024-06-30"}

    assert HybridRetriever._is_valid_as_of(payload, "2024-06-30") is True
    assert HybridRetriever._is_valid_as_of(payload, "2024-07-01") is False
