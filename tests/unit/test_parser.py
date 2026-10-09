from src.ingest.crawler import DocumentSource, LegalCrawler
from src.ingest.parser import VietnameseLegalParser


def test_parse_articles_and_clauses():
    raw_sample = """
Chương VI
THU HỒI ĐẤT, TRƯNG DỤNG ĐẤT

Điều 79. Thu hồi đất để phát triển kinh tế - xã hội vì lợi ích quốc gia, công cộng
1. Nhà nước thu hồi đất để thực hiện các dự án phát triển kinh tế - xã hội vì lợi ích quốc gia, công cộng nhằm phát huy nguồn lực đất đai.
a) Dự án xây dựng công trình giao thông, bao gồm đường cao tốc, đường sắt.
b) Dự án xây dựng công trình thủy lợi, cấp thoát nước.
2. Việc thu hồi đất phải căn cứ vào quy hoạch sử dụng đất cấp huyện đã được phê duyệt.
    """

    metadata = {
        "doc_id": "test-31-2024",
        "document_title": "Luật Đất đai số 31/2024/QH15",
        "document_number": "31/2024/QH15",
        "document_type": "luat",
        "issuing_body": "Quốc hội",
        "effective_date": "2024-08-01",
        "source_url": "https://vanban.chinhphu.vn/?classid=1&docid=211189",
        "administrative_area": ["Toàn quốc", "Hà Nội"],
    }

    parser = VietnameseLegalParser()
    parsed_doc = parser.parse(raw_sample, metadata)

    assert parsed_doc.doc_id == "test-31-2024"
    assert parsed_doc.document_title == "Luật Đất đai số 31/2024/QH15"
    assert len(parsed_doc.articles) == 1

    art = parsed_doc.articles[0]
    assert art.article_number == "79"
    assert "Thu hồi đất" in art.article_title
    assert art.chapter_number == "VI"
    assert len(art.clauses) == 2

    c1 = art.clauses[0]
    assert c1.clause_number == "1"
    assert len(c1.points) == 2
    assert c1.points[0]["point"] == "a"
    assert "giao thông" in c1.points[0]["text"]
    assert c1.points[1]["point"] == "b"


def test_parse_empty_or_unstructured_text():
    metadata = {
        "doc_id": "empty-doc",
        "document_title": "Văn bản rỗng",
    }
    parser = VietnameseLegalParser()
    parsed_doc = parser.parse("Nội dung thông báo không chứa cấu trúc điều khoản", metadata)

    assert parsed_doc.doc_id == "empty-doc"
    assert len(parsed_doc.articles) == 0


def test_parse_section_and_normalize_whitespace():
    parser = VietnameseLegalParser()
    parsed = parser.parse(
        "Chương I\nMục 2. Quy định chung\nĐiều 3. Phạm vi\n1.  Nội dung   có khoảng trắng thừa.",
        {"doc_id": "section-doc", "document_title": "T", "document_number": "1"},
    )
    article = parsed.articles[0]
    assert article.section_number == "2"
    assert article.section_title == "Quy định chung"
    assert "Nội dung có khoảng trắng thừa." in article.clauses[0].text


def test_official_ocr_normalization_and_identity_check():
    source = DocumentSource(
        doc_id="88-2024-ND-CP",
        document_number="88/2024/NĐ-CP",
        document_title="Nghị định",
        document_type="nghi_dinh",
        issuing_body="Chính phủ",
        issued_date="2024-07-15",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://example.com",
        administrative_area=["Toàn quốc"],
        legal_domain=["dat_dai"],
    )
    text = LegalCrawler._normalize_ocr_structure("Số: 88/2024/ND-CP\nDIEU 1. Phạm vi điều chỉnh")
    assert "Điều 1" in text
    assert LegalCrawler._matches_source(text, source)
