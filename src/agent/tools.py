import json
from pathlib import Path
from typing import Any

from src.agent.retriever import HybridRetriever
from src.core.logging import logger

_retriever: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    """Singleton getter for HybridRetriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


def retrieve_legal_documents(
    query: str,
    as_of_date: str | None = None,
    district: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Retrieve relevant legal chunks from Hanoi legal corpus (Qdrant / Hybrid).

    Args:
        query: Search query or sub-query.
        as_of_date: Validity cutoff date (YYYY-MM-DD).
        district: Optional Hanoi district filter.
        limit: Maximum number of chunks to return.

    Returns:
        List of legal document chunks with metadata and score.
    """
    logger.info(
        f"Retrieving legal docs for query='{query}', district='{district}', as_of_date='{as_of_date}', limit={limit}"
    )
    retriever = get_retriever()
    results = retriever.retrieve(
        query=query,
        as_of_date=as_of_date,
        district=district,
        top_k=limit,
    )
    logger.info(f"Retriever returned {len(results)} chunks")
    return results


def check_document_validity(doc_id: str, as_of_date: str | None = None) -> dict[str, Any]:
    """Check legal document validity status as of a specified date.

    Args:
        doc_id: Legal document ID (e.g. '31-2024-QH15', '61-2024-QD-UBND').
        as_of_date: Target validity date in YYYY-MM-DD format.

    Returns:
        Validity metadata, replacement status, and active amendments.
    """
    logger.info(f"Checking validity for doc_id='{doc_id}' as of date='{as_of_date}'")
    manifest_path = Path("data/corpus/raw/manifest.json")
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for doc in manifest:
                if doc.get("doc_id") == doc_id or doc.get("document_number") == doc_id:
                    eff_date = doc.get("effective_date")
                    exp_date = doc.get("expiry_date")
                    is_valid = True
                    status_text = "Còn hiệu lực"

                    if as_of_date:
                        if eff_date and as_of_date < eff_date:
                            is_valid = False
                            status_text = f"Chưa có hiệu lực (hiệu lực từ {eff_date})"
                        elif exp_date and as_of_date > exp_date:
                            is_valid = False
                            status_text = f"Hết hiệu lực từ {exp_date}"

                    return {
                        "doc_id": doc_id,
                        "document_title": doc.get("document_title"),
                        "effective_date": eff_date,
                        "expiry_date": exp_date,
                        "is_valid": is_valid,
                        "status": status_text,
                        "replaced_by": doc.get("replaced_by"),
                        "amendments": doc.get("amendments", []),
                    }
        except Exception as e:
            logger.warning(f"Error checking manifest for doc validity: {e}")

    return {
        "doc_id": doc_id,
        "is_valid": True,
        "status": "Còn hiệu lực",
        "replaced_by": None,
        "amendments": [],
    }
