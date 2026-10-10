import hashlib

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.config import get_settings
from src.core.logging import logger
from src.embedding.cache import get_embedding_cache


class HFEmbeddingClient:
    """Hugging Face Inference API client for BGE-M3 embeddings with Redis caching."""

    def __init__(self):
        self.settings = get_settings()
        self.cache = get_embedding_cache()
        self.headers = {
            "Authorization": f"Bearer {self.settings.HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json",
        }
        self.url = self.settings.HF_EMBEDDING_URL
        self.batch_size = self.settings.HF_EMBEDDING_BATCH_SIZE
        self.timeout = self.settings.HF_EMBEDDING_TIMEOUT
        self._client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError)),
    )
    async def _call_hf_api(self, texts: list[str]) -> list[list[float]]:
        """Call HF Inference API with retry logic."""
        client = await self._get_http_client()

        response = await client.post(
            self.url,
            headers=self.headers,
            json={
                "inputs": texts,
                "options": {
                    "wait_for_model": True,
                    "use_cache": True,
                },
            },
        )
        response.raise_for_status()
        result = response.json()

        # HF API returns list of embeddings or single embedding
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], list):
                return result  # List of embeddings
            return [result]  # Single embedding wrapped
        return []

    async def embed(self, texts: list[str], use_cache: bool = True) -> list[list[float]]:
        """Generate embeddings for texts with caching."""
        if not texts:
            return []

        model = self.settings.HF_EMBEDDING_MODEL
        results: list[list[float] | None] = [None] * len(texts)
        to_embed: list[tuple[int, str]] = []

        # Check cache first
        if use_cache:
            cached = await self.cache.get_batch(texts, model)
            for idx, emb in cached.items():
                results[idx] = emb

            # Collect texts that need embedding
            for i, text in enumerate(texts):
                if results[i] is None:
                    to_embed.append((i, text))
        else:
            to_embed = [(i, t) for i, t in enumerate(texts)]

        # Embed uncached texts in batches
        if to_embed:
            for i in range(0, len(to_embed), self.batch_size):
                batch = to_embed[i : i + self.batch_size]
                batch_texts = [t for _, t in batch]
                batch_indices = [idx for idx, _ in batch]

                try:
                    embeddings = await self._call_hf_api(batch_texts)
                    for idx, emb in zip(batch_indices, embeddings):
                        results[idx] = emb

                    # Cache the new embeddings
                    if use_cache:
                        await self.cache.set_batch(batch_texts, embeddings, model)

                except Exception as e:
                    logger.error(f"HF embedding failed for batch: {e}")
                    # Fallback: generate deterministic mock embeddings
                    for idx in batch_indices:
                        results[idx] = self._mock_embedding(texts[idx])

        # Ensure all results are filled
        return [r if r is not None else self._mock_embedding(t) for r, t in zip(results, texts)]

    async def embed_single(self, text: str, use_cache: bool = True) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed([text], use_cache)
        return embeddings[0] if embeddings else self._mock_embedding(text)

    def _mock_embedding(self, text: str) -> list[float]:
        """Deterministic mock embedding for fallback (1024-dim)."""
        import math

        vec = []
        for i in range(1024):
            h = hashlib.sha256(f"{text}-{i}".encode()).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1.0
            vec.append(val)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    async def close(self):
        """Close HTTP client and cache connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        await self.cache.close()


_hf_embedding_client: HFEmbeddingClient | None = None


def get_hf_embedding_client() -> HFEmbeddingClient:
    """Singleton getter for HFEmbeddingClient."""
    global _hf_embedding_client
    if _hf_embedding_client is None:
        _hf_embedding_client = HFEmbeddingClient()
    return _hf_embedding_client
