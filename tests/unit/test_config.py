from src.core.config import Settings, get_settings


def test_settings_load():
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.APP_NAME == "Agentic RAG Legal QA Hanoi"
    assert settings.PORT == 8000
