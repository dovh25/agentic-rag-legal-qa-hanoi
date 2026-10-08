from types import SimpleNamespace

import httpx
import pytest

from src.ingest.crawler import P1_CORPUS_REGISTRY, DocumentSource, LegalCrawler


@pytest.mark.asyncio
async def test_crawler_does_not_synthesize_missing_legal_text(tmp_path):
    source = DocumentSource(
        doc_id="unseeded-test-doc",
        document_number="999/2024/NĐ-CP",
        document_title="Unseeded test document",
        document_type="nghi_dinh",
        issuing_body="Chính phủ",
        issued_date="2024-01-01",
        effective_date="2024-02-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/test",
        administrative_area=["Toàn quốc"],
        legal_domain=["dat_dai"],
    )

    class OfflineClient:
        async def get(self, *args, **kwargs):
            raise httpx.ConnectError("offline")

    crawler = LegalCrawler(storage_dir=str(tmp_path))
    with pytest.raises(RuntimeError, match="No verified official content"):
        await crawler.fetch_document(source, OfflineClient())


@pytest.mark.asyncio
async def test_crawler_extracts_p1_text_from_official_pdf(tmp_path, monkeypatch):
    class FakeResponse:
        content = b"%PDF-fake"
        headers = {"content-type": "application/pdf"}

        def raise_for_status(self):
            return None

    class FakeClient:
        async def get(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(
        "src.ingest.crawler.PdfReader",
        lambda _: SimpleNamespace(
            pages=[
                SimpleNamespace(
                    extract_text=lambda: "Điều 1. Quy định\n1. Nội dung\nĐiều 2. Phạm vi"
                )
            ]
        ),
    )
    source = P1_CORPUS_REGISTRY[-1]
    crawler = LegalCrawler(storage_dir=str(tmp_path))

    manifest_item = await crawler.fetch_document(source, FakeClient())

    assert manifest_item["status"] == "crawled_pdf"
    assert manifest_item["legal_status"] == "active"
    assert (tmp_path / f"{source.doc_id}.pdf").read_bytes() == b"%PDF-fake"
    assert "Điều 1." in (tmp_path / f"{source.doc_id}.txt").read_text(encoding="utf-8")


def test_p1_registry_uses_official_sources_and_marks_partial_amendments():
    by_number = {source.document_number: source for source in P1_CORPUS_REGISTRY}
    assert set(by_number) == {
        "71/2024/NĐ-CP",
        "101/2024/NĐ-CP",
        "10/2024/TT-BTNMT",
    }
    assert by_number["71/2024/NĐ-CP"].legal_status == "amended"
    assert by_number["101/2024/NĐ-CP"].legal_status == "amended"
    assert by_number["10/2024/TT-BTNMT"].legal_status == "active"
    assert all(
        source.source_url.startswith("https://vanban.chinhphu.vn/")
        and source.download_url
        and source.download_url.startswith("https://datafiles.chinhphu.vn/")
        for source in P1_CORPUS_REGISTRY
    )
