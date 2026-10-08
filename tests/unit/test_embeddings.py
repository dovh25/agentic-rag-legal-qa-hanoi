from types import SimpleNamespace

import pytest

from src.ingest import indexer as indexer_module
from src.ingest.indexer import QdrantLegalIndexer


def test_generate_embeddings_uses_gemini_retrieval_config_and_normalizes(monkeypatch):
    indexer = QdrantLegalIndexer()
    monkeypatch.setattr(indexer.settings, "EMBEDDING_API_KEY", "test-api-key")
    captured = {}

    class FakeModels:
        def embed_content(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                embeddings=[
                    SimpleNamespace(values=[3.0] + [4.0] + [0.0] * (indexer.vector_dim - 2))
                ]
            )

    monkeypatch.setattr(
        indexer_module,
        "_get_embedding_client",
        lambda api_key: SimpleNamespace(models=FakeModels()),
    )

    vectors = indexer.generate_embeddings(["test"], task_type="RETRIEVAL_QUERY")

    assert captured["model"] == indexer.settings.EMBEDDING_MODEL
    assert captured["config"].task_type == "RETRIEVAL_QUERY"
    assert captured["config"].output_dimensionality == indexer.vector_dim
    assert vectors[0][:2] == pytest.approx([0.6, 0.8])


def test_generate_embeddings_rejects_wrong_dimension(monkeypatch):
    indexer = QdrantLegalIndexer()
    monkeypatch.setattr(indexer.settings, "EMBEDDING_API_KEY", "test-api-key")

    class FakeModels:
        def embed_content(self, **kwargs):
            return SimpleNamespace(
                embeddings=[SimpleNamespace(values=[1.0] * (indexer.vector_dim - 1))]
            )

    monkeypatch.setattr(
        indexer_module,
        "_get_embedding_client",
        lambda api_key: SimpleNamespace(models=FakeModels()),
    )

    with pytest.raises(RuntimeError, match="invalid embedding dimension"):
        indexer.generate_embeddings(["test"])


def test_generate_embeddings_requires_google_api_key(monkeypatch):
    indexer = QdrantLegalIndexer()
    monkeypatch.setattr(indexer.settings, "EMBEDDING_API_KEY", "")
    monkeypatch.setattr(indexer.settings, "OPENAI_API_KEY", "")

    with pytest.raises(RuntimeError, match="Google Gemini API key"):
        indexer.generate_embeddings(["test"])
