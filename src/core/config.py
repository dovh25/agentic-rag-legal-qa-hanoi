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
    API_KEY: str | None = None
    ALLOWED_ORIGINS: str = "*"
    RATE_LIMIT_PER_MINUTE: int = 30

    # LLM Settings
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.groq.com/openai/v1"
    MODEL_NAME: str = "llama-3.3-70b-versatile"
    LLM_PROVIDER: str = "groq"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"

    # Hugging Face Embedding API (GPU-accelerated, free tier)
    HUGGINGFACE_API_KEY: str | None = None
    USE_HF_EMBEDDING_API: bool = True
    HF_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    HF_EMBEDDING_URL: str = "https://api-inference.huggingface.co/models/BAAI/bge-m3"
    HF_EMBEDDING_BATCH_SIZE: int = 32
    HF_EMBEDDING_TIMEOUT: float = 30.0

    # Redis Cache for Embeddings
    REDIS_URL: str | None = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    EMBEDDING_CACHE_TTL: int = 86400 * 30  # 30 days

    # Vector Database (Qdrant)
    QDRANT_URL: str | None = None
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "legal_chunks"
    QDRANT_ACTIVE_ALIAS: str = "legal_chunks"
    QDRANT_API_KEY: str | None = None
    CORPUS_VERSION: str = "2026-10-09.2"
    EMBEDDING_REVISION: str = "bge-m3-1024-v1"
    ALLOW_MOCK_EMBEDDINGS: bool = False

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
