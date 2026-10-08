import math
import uuid
from functools import lru_cache
from typing import Literal

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.core.config import get_embedding_api_key, get_settings
from src.core.logging import logger
from src.ingest.chunker import LegalChunk


class CollectionDimensionMismatchError(RuntimeError):
    """Raised when an existing Qdrant collection cannot store configured vectors."""


@lru_cache(maxsize=4)
def _get_embedding_client(api_key: str):
    from google import genai

    return genai.Client(api_key=api_key)


class QdrantLegalIndexer:
    """Manages collection creation, payload indexing, and batch upsert in Qdrant (ADR-0004)."""

    def __init__(
        self,
        url: str | None = None,
        host: str | None = None,
        port: int | None = None,
        api_key: str | None = None,
        collection_name: str | None = None,
        vector_dim: int | None = None,
    ):
        settings = get_settings()
        self.settings = settings
        self.url = url or settings.QDRANT_URL
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.vector_dim = vector_dim or settings.EMBEDDING_DIMENSION
        self.client: QdrantClient | None = None

    def connect(self) -> QdrantClient:
        """Establish connection with Qdrant server (cloud or local)."""
        if not self.client:
            if self.url or (self.host and self.host.startswith("http")):
                endpoint = self.url or self.host
                self.client = QdrantClient(
                    url=endpoint,
                    api_key=self.api_key,
                    timeout=10.0,
                    check_compatibility=False,
                )
            else:
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    api_key=self.api_key,
                    timeout=10.0,
                    check_compatibility=False,
                )
        return self.client

    def ensure_collection(self) -> bool:
        """Ensure collection exists with Cosine distance and payload indexes."""
        try:
            client = self.connect()
            collections = [c.name for c in client.get_collections().collections]

            if self.collection_name not in collections:
                logger.info(
                    f"Creating Qdrant collection '{self.collection_name}' (dim={self.vector_dim}, metric=Cosine)"
                )
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE,
                    ),
                )

                logger.info(f"Collection '{self.collection_name}' created successfully.")

            collection_info = client.get_collection(collection_name=self.collection_name)
            vectors_config = getattr(
                getattr(getattr(collection_info, "config", None), "params", None),
                "vectors",
                None,
            )
            existing_vector_size = getattr(vectors_config, "size", None)
            if existing_vector_size and existing_vector_size != self.vector_dim:
                raise CollectionDimensionMismatchError(
                    f"Qdrant collection '{self.collection_name}' uses {existing_vector_size}-dim "
                    f"vectors, but {self.settings.EMBEDDING_MODEL} is configured for "
                    f"{self.vector_dim}. Index into a new versioned collection and switch "
                    "QDRANT_COLLECTION only after verification."
                )
            current_schema = collection_info.payload_schema or {}
            index_schemas = {
                "doc_id": qmodels.PayloadSchemaType.KEYWORD,
                "legal_status": qmodels.PayloadSchemaType.KEYWORD,
                "document_number": qmodels.PayloadSchemaType.KEYWORD,
                "article_ref": qmodels.PayloadSchemaType.KEYWORD,
                "administrative_area": qmodels.PayloadSchemaType.KEYWORD,
                "effective_date": qmodels.PayloadSchemaType.DATETIME,
                "expiry_date": qmodels.PayloadSchemaType.DATETIME,
            }
            for field_name, field_schema in index_schemas.items():
                existing_schema = current_schema.get(field_name)
                existing_type = getattr(existing_schema, "data_type", existing_schema)
                if existing_type == field_schema:
                    continue
                if existing_schema is not None:
                    client.delete_payload_index(
                        collection_name=self.collection_name,
                        field_name=field_name,
                    )
                client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_schema,
                )
            return True
        except Exception as e:
            if isinstance(e, CollectionDimensionMismatchError):
                raise
            logger.warning(
                f"Could not connect to Qdrant at {self.host}:{self.port} ({e}). Running in offline/mock mode."
            )
            return False

    def generate_embeddings(
        self,
        texts: list[str],
        task_type: Literal["RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT"] = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        """Generate normalized Gemini embeddings; fail explicitly instead of indexing fake vectors."""
        if not texts:
            return []

        api_key = get_embedding_api_key(self.settings)
        if not api_key:
            raise RuntimeError(
                "A valid Google Gemini API key is required for embeddings; configure "
                "EMBEDDING_API_KEY or use OPENAI_API_KEY with the Gemini endpoint."
            )

        from google.genai import types

        client = _get_embedding_client(api_key)
        embeddings: list[list[float]] = []
        batch_size = 100
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = client.models.embed_content(
                model=self.settings.EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.vector_dim,
                ),
            )
            batch_embeddings = response.embeddings or []
            if len(batch_embeddings) != len(batch):
                raise RuntimeError(
                    "Gemini embedding response count does not match the input batch."
                )

            for embedding in batch_embeddings:
                values = embedding.values
                if values is None or len(values) != self.vector_dim:
                    raise RuntimeError(
                        f"Gemini returned an invalid embedding dimension; expected "
                        f"{self.vector_dim} for {self.settings.EMBEDDING_MODEL}."
                    )
                vector = [float(value) for value in values]
                if not all(math.isfinite(value) for value in vector):
                    raise RuntimeError("Gemini returned non-finite embedding values.")
                norm = math.sqrt(sum(value * value for value in vector))
                if norm == 0:
                    raise RuntimeError("Gemini returned a zero-length embedding.")
                embeddings.append([value / norm for value in vector])

        return embeddings

    def index_chunks(self, chunks: list[LegalChunk], batch_size: int = 64) -> int:
        """Batch index chunks into Qdrant collection."""
        if not chunks:
            return 0

        client = self.connect()
        is_ready = self.ensure_collection()
        if not is_ready:
            raise RuntimeError(
                f"Qdrant collection '{self.collection_name}' is unavailable; "
                f"refusing to skip indexing {len(chunks)} legal chunks."
            )

        total_indexed = 0
        texts = [chunk.text for chunk in chunks]
        embeddings = self.generate_embeddings(texts, task_type="RETRIEVAL_DOCUMENT")
        if len(embeddings) != len(chunks) or any(
            len(vector) != self.vector_dim for vector in embeddings
        ):
            raise RuntimeError(
                "Embedding output does not match the number of legal chunks or configured "
                "Qdrant vector dimension; refusing to index."
            )

        points: list[qmodels.PointStruct] = []
        for i, chunk in enumerate(chunks):
            # Deterministic UUID from chunk_id
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))
            payload = {
                **chunk.metadata,
                "text": chunk.text,
                "breadcrumb": chunk.breadcrumb,
                "chunk_id": chunk.chunk_id,
            }

            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload=payload,
                )
            )

        # Batch upsert
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            client.upsert(collection_name=self.collection_name, points=batch)
            total_indexed += len(batch)

        logger.info(f"Successfully indexed {total_indexed} chunks into '{self.collection_name}'.")
        return total_indexed
