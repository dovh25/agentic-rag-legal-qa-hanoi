import hashlib
import json

import redis.asyncio as redis
from redis.asyncio import Redis

from src.core.config import get_settings
from src.core.logging import logger


class EmbeddingCache:
    """Redis-based cache for embeddings with text-hash keys."""

    def __init__(self):
        self.settings = get_settings()
        self._client: Redis | None = None
        self._connected: bool = False

    async def _get_client(self) -> Redis | None:
        if self._connected is not None and self._client is not None:
            return self._client

        if not self.settings.REDIS_URL and not (self.settings.REDIS_HOST and self.settings.REDIS_PORT):
            logger.debug("Redis not configured, embedding cache disabled")
            self._connected = False
            return None

        try:
            if self.settings.REDIS_URL:
                self._client = redis.from_url(
                    self.settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
            else:
                self._client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    db=self.settings.REDIS_DB,
                    password=self.settings.REDIS_PASSWORD,
                    encoding="utf-8",
                    decode_responses=True,
                )

            await self._client.ping()
            self._connected = True
            logger.info("Connected to Redis for embedding cache")
            return self._client
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Embedding cache disabled.")
            self._connected = False
            self._client = None
            return None

    @staticmethod
    def _make_key(text: str, model: str) -> str:
        """Generate cache key from text hash and model name."""
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"emb:{model}:{text_hash}"

    async def get(self, text: str, model: str | None = None) -> list[float] | None:
        """Retrieve cached embedding for text."""
        client = await self._get_client()
        if not client:
            return None

        model = model or self.settings.HF_EMBEDDING_MODEL
        key = self._make_key(text, model)

        try:
            cached = await client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.debug(f"Cache get error: {e}")
        return None

    async def set(self, text: str, embedding: list[float], model: str | None = None, ttl: int | None = None) -> bool:
        """Store embedding in cache."""
        client = await self._get_client()
        if not client:
            return False

        model = model or self.settings.HF_EMBEDDING_MODEL
        key = self._make_key(text, model)
        ttl = ttl or self.settings.EMBEDDING_CACHE_TTL

        try:
            await client.setex(key, ttl, json.dumps(embedding))
            return True
        except Exception as e:
            logger.debug(f"Cache set error: {e}")
            return False

    async def get_batch(self, texts: list[str], model: str | None = None) -> dict[int, list[float]]:
        """Retrieve multiple cached embeddings."""
        client = await self._get_client()
        if not client:
            return {}

        model = model or self.settings.HF_EMBEDDING_MODEL
        keys = [self._make_key(t, model) for t in texts]

        try:
            values = await client.mget(keys)
            result = {}
            for i, val in enumerate(values):
                if val:
                    result[i] = json.loads(val)
            return result
        except Exception as e:
            logger.debug(f"Cache batch get error: {e}")
            return {}

    async def set_batch(self, texts: list[str], embeddings: list[list[float]], model: str | None = None, ttl: int | None = None) -> int:
        """Store multiple embeddings in cache."""
        client = await self._get_client()
        if not client:
            return 0

        model = model or self.settings.HF_EMBEDDING_MODEL
        ttl = ttl or self.settings.EMBEDDING_CACHE_TTL

        try:
            pipe = client.pipeline()
            for text, emb in zip(texts, embeddings):
                key = self._make_key(text, model)
                pipe.setex(key, ttl, json.dumps(emb))
            await pipe.execute()
            return len(texts)
        except Exception as e:
            logger.debug(f"Cache batch set error: {e}")
            return 0

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False


_embedding_cache: EmbeddingCache | None = None


def get_embedding_cache() -> EmbeddingCache:
    """Singleton getter for EmbeddingCache."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache
