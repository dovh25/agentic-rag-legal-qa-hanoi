import uuid
from collections import Counter
import re
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.models import SparseVector

from src.core.config import get_settings
from src.core.logging import logger
from src.ingest.chunker import LegalChunk
from src.embedding.hf_client import get_hf_embedding_client


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
        """Ensure collection exists with dense + sparse vectors and payload indexes."""
        try:
            client = self.connect()
            collections = [c.name for c in client.get_collections().collections]

            if self.collection_name not in collections:
                logger.info(
                    f"Creating Qdrant collection '{self.collection_name}' (dense_dim={self.vector_dim}, sparse=BM25, metric=Cosine)"
                )
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "": qmodels.VectorParams(
                            size=self.vector_dim,
                            distance=qmodels.Distance.COSINE,
                        ),
                    },
                    sparse_vectors_config={
                        "text": qmodels.SparseVectorParams()
                    },
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
        aliases = []
        for collection in client.get_collections().collections:
            aliases.extend(client.get_collection_aliases(collection.name).aliases)
        actions: list[qmodels.CreateAliasOperation | qmodels.DeleteAliasOperation] = []
        for alias in aliases:
            if alias.alias_name == alias_name:
                actions.append(
                    qmodels.DeleteAliasOperation(
                        delete_alias=qmodels.DeleteAlias(alias_name=alias_name)
                    )
                )
        actions.append(
            qmodels.CreateAliasOperation(
                create_alias=qmodels.CreateAlias(
                    collection_name=collection_name, alias_name=alias_name
                )
            )
        )
        client.update_collection_aliases(change_aliases_operations=actions)

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate dense BGE-M3 embeddings using HF Inference API with Redis cache."""
        settings = get_settings()

        if settings.USE_HF_EMBEDDING_API and settings.HUGGINGFACE_API_KEY:
            try:
                hf_client = get_hf_embedding_client()
                embeddings = await hf_client.embed(texts, use_cache=True)
                logger.info(f"Generated {len(embeddings)} embeddings via HF API (with cache)")
                return embeddings
            except Exception as e:
                logger.warning(f"HF embedding API failed: {e}. Falling back to local model.")
        else:
            logger.info("HF embedding API not configured, using local sentence-transformers")

        # Fallback to local sentence-transformers
        try:
            model = self._get_embedding_model()
            vectors = model.encode(
                texts,
                batch_size=64,
                normalize_embeddings=True,
                show_progress_bar=True,
                convert_to_numpy=True,
            )
            return [v.tolist() for v in vectors]
        except Exception as e:
            if not settings.ALLOW_MOCK_EMBEDDINGS:
                raise RuntimeError(
                    "BGE-M3 is unavailable; refusing to generate production embeddings. "
                    "Install sentence-transformers and the BAAI/bge-m3 model, or set "
                    "ALLOW_MOCK_EMBEDDINGS=true only for isolated tests."
                ) from e
            logger.warning(
                "Using deterministic mock embeddings because test mode is enabled: %s", e
            )
            import hashlib
            import math

            embeddings: list[list[float]] = []
            for text in texts:
                vec: list[float] = []
                for i in range(self.vector_dim):
                    h = hashlib.sha256(f"{text}-{i}".encode()).hexdigest()
                    val = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1.0
                    vec.append(val)
                norm = math.sqrt(sum(x * x for x in vec)) or 1.0
                vec = [x / norm for x in vec]
                embeddings.append(vec)
            return embeddings

    @lru_cache(maxsize=1)
    def _get_embedding_model(self):
        """Get cached BGE-M3 embedding model (local fallback)."""
        import torch
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("BAAI/bge-m3")
        torch.set_num_threads(min(32, torch.get_num_threads()))
        model.max_seq_length = 512
        return model

    def _build_sparse_vector(self, text: str) -> SparseVector:
        """Build BM25 sparse vector for document text with unique indices."""
        # Simple tokenization
        tokens = re.findall(r'\b\w+\b', text.lower())
        stop_words = {"và", "của", "các", "cho", "về", "thì", "là", "ở", "tại", "theo",
                      "được", "có", "những", "này", "đó", "ra", "vào", "lại", "nào",
                      "gì", "sao", "thế", "công", "gia", "nhất", "như", "nếu", "để",
                      "do", "thức", "ngon", "truyền", "cách", "làm", "ngày", "tết"}
        tokens = [t for t in tokens if t not in stop_words and len(t) > 1]
        
        tf = Counter(tokens)
        if not tf:
            return SparseVector(indices=[], values=[])
        
        # Use deterministic hash-based indexing with collision handling
        # Use a consistent hash function to avoid Python's hash randomization
        import hashlib
        term_to_idx = {}
        used_indices = set()
        for term in tf:
            # Use MD5 hash for deterministic, collision-resistant indexing
            h = hashlib.md5(term.encode()).hexdigest()
            idx = int(h[:8], 16) % 1000000
            # Handle collisions - check against used_indices, not term_to_idx keys
            while idx in used_indices:
                idx = (idx + 1) % 1000000
            term_to_idx[term] = idx
            used_indices.add(idx)
        
        indices = [term_to_idx[term] for term in tf]
        values = [float(tf[term]) for term in tf]
        
        return SparseVector(indices=indices, values=values)

    async def index_chunks(self, chunks: list[LegalChunk], batch_size: int = 64) -> int:
        """Batch index chunks into Qdrant collection with dense + sparse vectors."""
        if not chunks:
            return 0

        client = self.connect()
        is_ready = self.ensure_collection()
        if not is_ready:
            logger.warning(f"Qdrant server unavailable. Skipping index of {len(chunks)} chunks.")
            return 0

        total_indexed = 0
        texts = [chunk.text for chunk in chunks]
        embeddings = await self.generate_embeddings(texts)

        points: list[qmodels.PointStruct] = []
        for i, chunk in enumerate(chunks):
            # Deterministic UUID from chunk_id
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))
            
            # Generate sparse vector for this chunk
            sparse_vector = self._build_sparse_vector(chunk.text)
            
            payload = {
                **chunk.metadata,
                "text": chunk.text,
                "breadcrumb": chunk.breadcrumb,
                "chunk_id": chunk.chunk_id,
            }

            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector={
                        "": embeddings[i],  # default dense vector
                        "text": sparse_vector,  # sparse vector for BM25
                    },
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
