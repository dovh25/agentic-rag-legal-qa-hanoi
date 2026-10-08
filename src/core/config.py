from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Agentic RAG Legal QA Hanoi"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000"

    # LLM Settings
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    MODEL_NAME: str = "gemini-3.8-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"

    # Vector Database (Qdrant)
    QDRANT_URL: str | None = None
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "legal_chunks"
    QDRANT_API_KEY: str | None = None

    # Database
    DATABASE_URL: str | None = None

    # Agent constraints & parameters
    MAX_SUBQUERIES: int = 3
    MAX_RETRIEVAL_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.75

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
