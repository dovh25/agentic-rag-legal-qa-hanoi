import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.core.config import get_settings
from src.core.logging import logger
from src.ingest.chunker import LegalChunk


class QdrantLegalIndexer:
    """Manages collection creation, payload indexing, and batch upsert in Qdrant (ADR-0004)."""

    def __init__(
        self,
        url: str | None = None,
        host: str | None = None,
        port: int | None = None,
        api_key: str | None = None,
        collection_name: str | None = None,
        vector_dim: int = 1024,
    ):
        settings = get_settings()
        self.url = url or settings.QDRANT_URL
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.vector_dim = vector_dim
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

                # Create Payload Indexes for fast metadata filtering (ADR-0004)
                for field_name in [
                    "doc_id",
                    "doc_number",
                    "doc_title",
                    "legal_status",
                    "effective_from",
                    "effective_to",
                    "scope",
                    "article",
                    "administrative_area",
                    "corpus_version",
                ]:
                    client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field_name,
                        field_schema=qmodels.PayloadSchemaType.KEYWORD,
                    )
                logger.info(
                    f"Collection '{self.collection_name}' and payload indexes created successfully."
                )
            else:
                logger.info(f"Collection '{self.collection_name}' already exists in Qdrant.")
            return True
        except Exception as e:
            logger.warning(
                f"Could not connect to Qdrant at {self.host}:{self.port} ({e}). Running in offline/mock mode."
            )
            return False

    def recreate_versioned_collection(self, collection_name: str) -> bool:
        """Create a clean versioned collection without touching the active one."""
        original = self.collection_name
        self.collection_name = collection_name
        try:
            client = self.connect()
            if collection_name in [c.name for c in client.get_collections().collections]:
                client.delete_collection(collection_name=collection_name)
            return self.ensure_collection()
        finally:
            self.collection_name = original

    def promote_alias(self, collection_name: str, alias_name: str) -> None:
        """Atomically point an alias at a validated collection."""
        client = self.connect()
        aliases = client.get_collection_aliases().aliases
        actions: list[qmodels.CreateAlias] = []
        for alias in aliases:
            if alias.alias_name == alias_name:
                actions.append(qmodels.DeleteAlias(alias_name=alias_name))
        actions.append(qmodels.CreateAlias(collection_name=collection_name, alias_name=alias_name))
        client.update_collection_aliases(change_aliases_operations=actions)

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate dense embeddings using BGE-M3 or fallback to normalized mock vectors."""
        # Try importing sentence_transformers for local BGE-M3 (ADR-0001)
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("BAAI/bge-m3")
            vectors = model.encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in vectors]
        except Exception as e:
            logger.debug(
                f"sentence_transformers/BGE-M3 not loaded directly ({e}). Using deterministic embedding generator."
            )
            import hashlib
            import math

            # Deterministic reproducible 1024-dim pseudo-embeddings for development & test suites
            embeddings: list[list[float]] = []
            for text in texts:
                vec: list[float] = []
                for i in range(self.vector_dim):
                    h = hashlib.sha256(f"{text}-{i}".encode()).hexdigest()
                    val = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1.0
                    vec.append(val)
                # Normalize vector to unit length
                norm = math.sqrt(sum(x * x for x in vec)) or 1.0
                vec = [x / norm for x in vec]
                embeddings.append(vec)
            return embeddings

    def index_chunks(self, chunks: list[LegalChunk], batch_size: int = 64) -> int:
        """Batch index chunks into Qdrant collection."""
        if not chunks:
            return 0

        client = self.connect()
        is_ready = self.ensure_collection()
        if not is_ready:
            logger.warning(f"Qdrant server unavailable. Skipping index of {len(chunks)} chunks.")
            return 0

        total_indexed = 0
        texts = [chunk.text for chunk in chunks]
        embeddings = self.generate_embeddings(texts)

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
