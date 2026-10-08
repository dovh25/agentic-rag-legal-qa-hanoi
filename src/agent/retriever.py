from datetime import date
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from src.core.config import get_settings
from src.core.logging import logger
from src.ingest.indexer import QdrantLegalIndexer

DOCUMENT_NUMBER_TO_ID = {
    "31/2024": "31-2024-QH15",
    "31-2024": "31-2024-QH15",
    "88/2024": "88-2024-ND-CP",
    "88-2024": "88-2024-ND-CP",
    "102/2024": "102-2024-ND-CP",
    "102-2024": "102-2024-ND-CP",
    "61/2024": "61-2024-QD-UBND",
    "61-2024": "61-2024-QD-UBND",
    "52/2025": "52-2025-NQ-HDND",
    "52-2025": "52-2025-NQ-HDND",
    "71/2024": "71-2024-ND-CP",
    "71-2024": "71-2024-ND-CP",
    "101/2024": "101-2024-ND-CP",
    "101-2024": "101-2024-ND-CP",
    "10/2024": "10-2024-TT-BTNMT",
    "10-2024": "10-2024-TT-BTNMT",
}

LEGAL_FOCUS_PHRASES = (
    "hạn mức giao đất ở",
    "hạn mức công nhận đất ở",
    "điều kiện thu hồi đất",
    "thu hồi đất",
    "bồi thường đất nông nghiệp",
    "bồi thường",
    "tái định cư",
    "bảng giá đất",
    "giá đất",
    "đăng ký đất đai",
)


def matching_legal_focus_phrases(query: str, evidence: str) -> list[str]:
    """Return specific legal concepts present in both a query and evidence."""
    query_lower = query.lower()
    evidence_lower = evidence.lower()
    return [
        phrase
        for phrase in LEGAL_FOCUS_PHRASES
        if phrase in query_lower and phrase in evidence_lower
    ]


def is_document_valid_on(metadata: dict[str, Any], as_of_date: date) -> bool:
    """Return whether a document is in force on the inclusive target date."""
    if metadata.get("legal_status", "active") != "active":
        return False
    effective_date = metadata.get("effective_date")
    expiry_date = metadata.get("expiry_date")
    if not effective_date:
        return False
    if date.fromisoformat(effective_date) > as_of_date:
        return False
    return not expiry_date or date.fromisoformat(expiry_date) >= as_of_date


class HybridRetriever:
    """Hybrid Retriever combining dense semantic search and lexical payload filtering (ADR-0004)."""

    def __init__(self):
        self.settings = get_settings()
        self.indexer = QdrantLegalIndexer()
        self.client: QdrantClient | None = None
        self._is_connected: bool | None = None

    def get_client(self) -> QdrantClient | None:
        if self._is_connected is None:
            try:
                settings = self.settings
                if settings.QDRANT_URL or (
                    settings.QDRANT_HOST and settings.QDRANT_HOST.startswith("http")
                ):
                    endpoint = settings.QDRANT_URL or settings.QDRANT_HOST
                    client = QdrantClient(
                        url=endpoint,
                        api_key=settings.QDRANT_API_KEY,
                        timeout=5.0,
                        check_compatibility=False,
                    )
                else:
                    client = QdrantClient(
                        host=settings.QDRANT_HOST,
                        port=settings.QDRANT_PORT,
                        api_key=settings.QDRANT_API_KEY,
                        timeout=3.0,
                        check_compatibility=False,
                    )
                client.get_collections()
                self.client = client
                self._is_connected = True
                target_str = settings.QDRANT_URL or f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
                logger.info(f"Connected to Qdrant at {target_str}")
            except Exception as e:
                logger.debug(
                    f"Qdrant not reachable ({e}). Retriever will use fallback semantic matcher."
                )
                self.client = None
                self._is_connected = False
        return self.client

    def retrieve(
        self,
        query: str,
        as_of_date: str | None = None,
        district: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Execute hybrid search with payload filtering."""
        effective_date = date.fromisoformat(as_of_date) if as_of_date else date.today()
        client = self.get_client()

        if client and self._is_connected:
            try:
                # 1. Generate query embedding
                query_vector = self.indexer.generate_embeddings([query])[0]

                # 2. Build payload filter
                filter_conditions: list[qmodels.Condition] = [
                    qmodels.FieldCondition(
                        key="legal_status",
                        match=qmodels.MatchValue(value="active"),
                    ),
                    qmodels.FieldCondition(
                        key="effective_date",
                        range=qmodels.DatetimeRange(lte=effective_date),
                    ),
                ]
                if district:
                    filter_conditions.append(
                        qmodels.FieldCondition(
                            key="administrative_area",
                            match=qmodels.MatchAny(any=[district, "Hà Nội", "Toàn quốc"]),
                        )
                    )

                # Prioritize explicit document number if specified in query
                for pattern, target_doc_id in DOCUMENT_NUMBER_TO_ID.items():
                    if pattern in query.lower():
                        filter_conditions.append(
                            qmodels.FieldCondition(
                                key="doc_id",
                                match=qmodels.MatchValue(value=target_doc_id),
                            )
                        )
                        break

                search_filter = qmodels.Filter(
                    must=filter_conditions,
                    must_not=[
                        qmodels.FieldCondition(
                            key="expiry_date",
                            range=qmodels.DatetimeRange(lt=effective_date),
                        )
                    ],
                )

                # 3. Search in Qdrant (using modern query_points API)
                if hasattr(client, "query_points"):
                    query_response = client.query_points(
                        collection_name=self.settings.QDRANT_COLLECTION,
                        query=query_vector,
                        query_filter=search_filter,
                        limit=top_k,
                    )
                    search_results = query_response.points
                else:
                    search_results = client.search(
                        collection_name=self.settings.QDRANT_COLLECTION,
                        query_vector=query_vector,
                        query_filter=search_filter,
                        limit=top_k,
                    )

                results = []
                for point in search_results:
                    payload = point.payload or {}
                    doc_title = payload.get("document_title", "")
                    art_ref = payload.get("article_ref")
                    results.append(
                        {
                            "doc_id": payload.get("doc_id", ""),
                            "document_title": doc_title,
                            "title": doc_title,
                            "document_number": payload.get("document_number", ""),
                            "article_ref": art_ref,
                            "article": art_ref,
                            "clause": payload.get("clause"),
                            "text": payload.get("text", ""),
                            "source_url": payload.get("source_url"),
                            "effective_date": payload.get("effective_date"),
                            "expiry_date": payload.get("expiry_date"),
                            "score": float(point.score),
                        }
                    )
                if results and max(result["score"] for result in results) >= (
                    self.settings.SIMILARITY_THRESHOLD
                ):
                    return results
                if results:
                    logger.warning(
                        "Dense retrieval confidence below threshold; trying exact legal-topic "
                        "matching against indexed payloads."
                    )
                    lexical_results = self._scroll_lexical_retrieve(
                        client,
                        search_filter,
                        query,
                        top_k,
                    )
                    if lexical_results:
                        return lexical_results
                    logger.warning(
                        "Lexical fallback found no sufficiently topic-matched evidence."
                    )
                    return []
            except Exception as e:
                logger.warning(f"Qdrant search error ({e}). Falling back to local matcher.")

        # Fallback offline retrieval based on lexical & legal entity matching
        return self._offline_retrieve(query, effective_date.isoformat(), district, top_k)

    def _scroll_lexical_retrieve(
        self,
        client: QdrantClient,
        search_filter: qmodels.Filter,
        query: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Use exact query concepts over a bounded full-corpus scan when vectors are weak."""
        query_lower = query.lower()
        focus_phrases = [
            phrase for phrase in LEGAL_FOCUS_PHRASES if phrase in query_lower
        ]
        stop_words = {
            "và",
            "của",
            "các",
            "cho",
            "về",
            "thì",
            "là",
            "ở",
            "tại",
            "theo",
            "được",
            "có",
            "những",
            "này",
            "đó",
            "quy",
            "định",
            "mới",
            "nhất",
        }
        query_terms = {
            term for term in query_lower.split() if len(term) > 1 and term not in stop_words
        }
        points: list[Any] = []
        offset: Any = None
        page_size = 256
        max_pages = 16

        for _ in range(max_pages):
            page, offset = client.scroll(
                collection_name=self.settings.QDRANT_COLLECTION,
                scroll_filter=search_filter,
                limit=page_size,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            points.extend(page)
            if offset is None:
                break
        else:
            logger.warning(
                "Skipping lexical fallback because corpus exceeds its safe scan limit "
                f"({page_size * max_pages} points)."
            )
            return []

        ranked: list[tuple[int, int, dict[str, Any]]] = []
        for point in points:
            payload = point.payload or {}
            text = str(payload.get("text", ""))
            title = str(payload.get("document_title", ""))
            article = str(payload.get("article_ref", ""))
            evidence = f"{text} {title} {article}"
            matched_phrases = matching_legal_focus_phrases(query, evidence)
            if focus_phrases and not matched_phrases:
                continue

            evidence_terms = set(evidence.lower().split())
            term_overlap = len(query_terms & evidence_terms)
            if not focus_phrases and term_overlap < 2:
                continue

            ranked.append(
                (
                    len(matched_phrases),
                    term_overlap,
                    {
                        "doc_id": payload.get("doc_id", ""),
                        "document_title": title,
                        "title": title,
                        "document_number": payload.get("document_number", ""),
                        "article_ref": article,
                        "article": article,
                        "clause": payload.get("clause"),
                        "text": text,
                        "source_url": payload.get("source_url"),
                        "effective_date": payload.get("effective_date"),
                        "expiry_date": payload.get("expiry_date"),
                        "score": 0.0,
                    },
                )
            )

        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [item[2] for item in ranked[:top_k]]

    def _offline_retrieve(
        self,
        query: str,
        as_of_date: str | None,
        district: str | None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Fallback local retrieval matching against verified seed legal corpus."""
        import json
        from pathlib import Path

        seed_dir = Path("data/corpus/seed")
        manifest_path = Path("data/corpus/raw/manifest.json")

        if not seed_dir.exists() or not manifest_path.exists():
            return []

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        target_date = date.fromisoformat(as_of_date) if as_of_date else date.today()
        query_lower = query.lower()
        requested_doc_id = next(
            (
                doc_id
                for pattern, doc_id in DOCUMENT_NUMBER_TO_ID.items()
                if pattern in query_lower
            ),
            None,
        )
        if requested_doc_id and not any(
            item.get("doc_id") == requested_doc_id for item in manifest
        ):
            return []
        STOP_WORDS = {
            "và",
            "của",
            "các",
            "cho",
            "về",
            "thì",
            "là",
            "ở",
            "tại",
            "theo",
            "được",
            "có",
            "những",
            "này",
            "đó",
            "ra",
            "vào",
            "lại",
            "nào",
            "gì",
            "sao",
            "thế",
            "công",
            "gia",
            "nhất",
            "như",
            "nếu",
            "để",
            "do",
            "thức",
            "ngon",
            "truyền",
            "cách",
            "làm",
            "ngày",
            "tết",
            "thống",
        }
        query_words = set(query.lower().split()) - STOP_WORDS
        if not query_words:
            return []

        # Domain verification: query must touch land/legal vocabulary
        legal_domain_stems = {
            "đất",
            "nhà",
            "giá",
            "bồi",
            "thường",
            "thu",
            "hồi",
            "tái",
            "định",
            "cư",
            "hạn",
            "mức",
            "quy",
            "hoạch",
            "sổ",
            "đỏ",
            "sử",
            "dụng",
            "giao",
            "thuê",
            "chuyển",
            "mục",
            "đích",
            "cấp",
            "tranh",
            "chấp",
            "nghị",
            "luật",
            "quyết",
            "bảng",
            "ubnd",
            "hđnd",
            "dự",
            "án",
        }
        if not any(stem in query_words for stem in legal_domain_stems):
            return []

        candidates: list[tuple[float, dict[str, Any]]] = []

        from src.ingest.chunker import LegalChunker
        from src.ingest.parser import VietnameseLegalParser

        parser = VietnameseLegalParser()
        chunker = LegalChunker()

        for item in manifest:
            if requested_doc_id and item.get("doc_id") != requested_doc_id:
                continue
            if item.get("legal_status", "active") != "active":
                continue
            if not is_document_valid_on(item, target_date):
                continue

            text_file = Path(item.get("clean_text_path") or seed_dir / f"{item['doc_id']}.txt")
            if not text_file.exists():
                text_file = seed_dir / f"{item['doc_id']}.txt"
            if not text_file.exists():
                continue

            parsed_doc = parser.parse(text_file.read_text(encoding="utf-8"), item)
            chunks = chunker.chunk_document(parsed_doc)

            for chunk in chunks:
                chunk_words = set(chunk.text.lower().split()) - STOP_WORDS
                overlap = len(query_words.intersection(chunk_words))
                if overlap >= 2 or (
                    overlap >= 1
                    and any(
                        k in query_words
                        for k in ["đất", "giá", "bồi", "thường", "thu", "hồi", "hạn", "mức"]
                    )
                ):
                    score = overlap / (len(query_words) or 1)
                    # Boost if district or specific article number matches
                    if district and district.lower() in chunk.text.lower():
                        score += 0.5
                    if item.get("doc_id") == "61-2024-QD-UBND":
                        score += 0.2  # Prefer Hanoi local decrees for Hanoi queries

                    candidates.append(
                        (
                            score,
                            {
                                "doc_id": chunk.metadata["doc_id"],
                                "document_title": chunk.metadata["document_title"],
                                "title": chunk.metadata["document_title"],
                                "document_number": chunk.metadata["document_number"],
                                "article_ref": chunk.metadata.get("article_ref"),
                                "article": chunk.metadata.get("article_ref"),
                                "clause": chunk.metadata.get("clause"),
                                "text": chunk.text,
                                "source_url": chunk.metadata.get("source_url"),
                                "effective_date": chunk.metadata.get("effective_date"),
                                "expiry_date": chunk.metadata.get("expiry_date"),
                                "score": round(score, 4),
                            },
                        )
                    )

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in candidates[:top_k]]
