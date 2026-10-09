from src.ingest.chunker import LegalChunker
from src.ingest.parser import VietnameseLegalParser


def test_chunking_with_breadcrumbs():
    raw_sample = """
Chương II
BỒI THƯỜNG, HỖ TRỢ, TÁI ĐỊNH CƯ

Điều 14. Hạn mức giao đất ở tái định cư tại Thành phố Hà Nội
1. Hạn mức giao đất ở tái định cư cho mỗi hộ gia đình cá nhân không vượt quá hạn mức giao đất ở mới tối đa quy định tại địa bàn từng quận, huyện.
2. Trường hợp diện tích đất ở bị thu hồi lớn hơn hạn mức giao đất ở mới, Ủy ban nhân dân cấp huyện xem xét giao thêm đất ở hoặc bán căn hộ chung cư tái định cư.
    """

    metadata = {
        "doc_id": "61-2024-QD-UBND",
        "document_title": "Quyết định số 61/2024/QĐ-UBND",
        "document_number": "61/2024/QĐ-UBND",
        "document_type": "quyet_dinh",
        "issuing_body": "UBND TP. Hà Nội",
        "effective_date": "2024-10-07",
        "source_url": "https://congbao.hanoi.gov.vn/",
        "administrative_area": ["Hà Nội"],
    }

    parser = VietnameseLegalParser()
    parsed_doc = parser.parse(raw_sample, metadata)

    chunker = LegalChunker(corpus_version="2026-10-04.1")
    chunks = chunker.chunk_document(parsed_doc)

    assert len(chunks) == 2

    # Test breadcrumb context injection
    first_chunk = chunks[0]
    assert "[Văn bản: Quyết định số 61/2024/QĐ-UBND]" in first_chunk.breadcrumb
    assert "[Chương II: BỒI THƯỜNG, HỖ TRỢ, TÁI ĐỊNH CƯ]" in first_chunk.breadcrumb
    assert (
        "[Điều 14: Hạn mức giao đất ở tái định cư tại Thành phố Hà Nội]" in first_chunk.breadcrumb
    )
    assert "[Khoản 1]" in first_chunk.breadcrumb

    # Text must contain breadcrumb prefix
    assert first_chunk.text.startswith(first_chunk.breadcrumb)

    # Test metadata fields
    assert first_chunk.metadata["doc_id"] == "61-2024-QD-UBND"
    assert first_chunk.metadata["article_ref"] == "Điều 14"
    assert first_chunk.metadata["clause"] == "Khoản 1"
    assert first_chunk.metadata["legal_status"] == "active"
    assert "Hà Nội" in first_chunk.metadata["administrative_area"]


def test_chunk_ids_are_deterministic_and_include_section():
    raw = "Chương I\nMục 1. Quy định\nĐiều 1. Phạm vi\n1. Nội dung."
    metadata = {
        "doc_id": "doc-1",
        "document_title": "Văn bản",
        "document_number": "1/2024",
        "effective_date": "2024-01-01",
        "source_url": "https://example.com",
        "administrative_area": ["Hà Nội"],
    }
    parser = VietnameseLegalParser()
    first = LegalChunker().chunk_document(parser.parse(raw, metadata))
    second = LegalChunker().chunk_document(parser.parse(raw, metadata))
    assert first[0].chunk_id == second[0].chunk_id == "doc-1-d1-k1"
    assert "[Mục 1: Quy định]" in first[0].breadcrumb
