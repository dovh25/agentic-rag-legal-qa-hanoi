import json
from datetime import date
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
    target_doc_id: str | None = None,
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
        target_doc_id=target_doc_id,
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
    target_date = date.fromisoformat(as_of_date) if as_of_date else date.today()
    if not manifest_path.exists():
        logger.error(f"Cannot verify validity for {doc_id}: corpus manifest is missing.")
        return {
            "doc_id": doc_id,
            "is_valid": False,
            "status": "Không có manifest để xác minh hiệu lực",
            "replaced_by": None,
            "amendments": [],
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error(f"Cannot verify validity for {doc_id}: invalid corpus manifest ({exc}).")
        return {
            "doc_id": doc_id,
            "is_valid": False,
            "status": "Manifest không hợp lệ, không thể xác minh hiệu lực",
            "replaced_by": None,
            "amendments": [],
        }

    for doc in manifest:
        if doc.get("doc_id") == doc_id or doc.get("document_number") == doc_id:
            eff_date = doc.get("effective_date")
            exp_date = doc.get("expiry_date")
            legal_status = doc.get("legal_status", "active")
            is_valid = bool(eff_date) and legal_status == "active"
            status_text = "Còn hiệu lực" if is_valid else "Thiếu ngày hiệu lực, không thể xác minh"

            if legal_status != "active":
                status_text = (
                    "Văn bản đã hết hiệu lực một phần hoặc được sửa đổi; "
                    "cần xác minh hiệu lực theo từng điều khoản"
                )
            elif eff_date and date.fromisoformat(eff_date) > target_date:
                is_valid = False
                status_text = f"Chưa có hiệu lực (hiệu lực từ {eff_date})"
            elif exp_date and date.fromisoformat(exp_date) < target_date:
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

    logger.warning(f"Cannot verify validity for unknown document {doc_id}.")
    return {
        "doc_id": doc_id,
        "is_valid": False,
        "status": "Không tìm thấy metadata hiệu lực của văn bản",
        "replaced_by": None,
        "amendments": [],
    }
