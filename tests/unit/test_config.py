from src.core.config import Settings, get_settings


def test_settings_load():
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.APP_NAME == "Agentic RAG Legal QA Hanoi"
    assert settings.PORT == 8000
    assert settings.QDRANT_ACTIVE_ALIAS == "legal_chunks"
    assert settings.CORPUS_VERSION == "2026-10-09.2"
    assert settings.EMBEDDING_MODEL == "BAAI/bge-m3"
