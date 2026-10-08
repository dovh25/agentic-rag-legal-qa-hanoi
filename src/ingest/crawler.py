import hashlib
import json
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from src.core.logging import logger


@dataclass
class DocumentSource:
    doc_id: str
    document_number: str
    document_title: str
    document_type: str
    issuing_body: str
    issued_date: str
    effective_date: str
    expiry_date: str | None
    source_url: str
    administrative_area: list[str]
    legal_domain: list[str]
    legal_status: str = "active"
    download_url: str | None = None


P0_CORPUS_REGISTRY: list[DocumentSource] = [
    DocumentSource(
        doc_id="31-2024-QH15",
        document_number="31/2024/QH15",
        document_title="Luật Đất đai số 31/2024/QH15",
        document_type="luat",
        issuing_body="Quốc hội",
        issued_date="2024-01-18",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/?classid=1&docid=211189",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["dat_dai", "quy_hoach", "boi_thuong", "tai_dinh_cu"],
    ),
    DocumentSource(
        doc_id="88-2024-ND-CP",
        document_number="88/2024/NĐ-CP",
        document_title="Nghị định số 88/2024/NĐ-CP quy định về bồi thường, hỗ trợ, tái định cư khi Nhà nước thu hồi đất",
        document_type="nghi_dinh",
        issuing_body="Chính phủ",
        issued_date="2024-07-15",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/?classid=0&docid=210658",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["boi_thuong", "ho_tro", "tai_dinh_cu"],
    ),
    DocumentSource(
        doc_id="102-2024-ND-CP",
        document_number="102/2024/NĐ-CP",
        document_title="Nghị định số 102/2024/NĐ-CP quy định chi tiết thi hành một số điều của Luật Đất đai",
        document_type="nghi_dinh",
        issuing_body="Chính phủ",
        issued_date="2024-07-30",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/?classid=0&docid=210672",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["dat_dai", "thi_hanh"],
    ),
    DocumentSource(
        doc_id="61-2024-QD-UBND",
        document_number="61/2024/QĐ-UBND",
        document_title="Quyết định số 61/2024/QĐ-UBND của UBND TP. Hà Nội quy định cụ thể một số nội dung bồi thường, hỗ trợ, tái định cư",
        document_type="quyet_dinh",
        issuing_body="Ủy ban nhân dân TP. Hà Nội",
        issued_date="2024-09-27",
        effective_date="2024-10-07",
        expiry_date=None,
        source_url="https://congbao.hanoi.gov.vn/",
        administrative_area=["Hà Nội"],
        legal_domain=["boi_thuong", "ho_tro", "tai_dinh_cu", "ha_noi"],
    ),
    DocumentSource(
        doc_id="52-2025-NQ-HDND",
        document_number="52/2025/NQ-HĐND",
        document_title="Nghị quyết số 52/2025/NQ-HĐND của HĐND TP. Hà Nội ban hành Bảng giá đất áp dụng trên địa bàn thành phố Hà Nội",
        document_type="nghi_quyet",
        issuing_body="Hội đồng nhân dân TP. Hà Nội",
        issued_date="2025-12-10",
        effective_date="2026-01-01",
        expiry_date=None,
        source_url="https://congbao.hanoi.gov.vn/Default.aspx?p_attribute=5054&pageid=45002",
        administrative_area=["Hà Nội"],
        legal_domain=["gia_dat", "bang_gia_dat", "ha_noi"],
    ),
]

P1_CORPUS_REGISTRY: list[DocumentSource] = [
    DocumentSource(
        doc_id="71-2024-ND-CP",
        document_number="71/2024/NĐ-CP",
        document_title="Nghị định số 71/2024/NĐ-CP quy định về giá đất",
        document_type="nghi_dinh",
        issuing_body="Chính phủ",
        issued_date="2024-06-27",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/?pageid=27160&docid=210523",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["gia_dat", "dat_dai"],
        legal_status="amended",
        download_url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/7/71-cp.signed.pdf",
    ),
    DocumentSource(
        doc_id="101-2024-ND-CP",
        document_number="101/2024/NĐ-CP",
        document_title=(
            "Nghị định số 101/2024/NĐ-CP quy định về điều tra cơ bản đất đai; đăng ký, "
            "cấp Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất "
            "và Hệ thống thông tin đất đai"
        ),
        document_type="nghi_dinh",
        issuing_body="Chính phủ",
        issued_date="2024-07-29",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/?pageid=27160&docid=210791",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["dat_dai", "dang_ky_dat_dai", "giay_chung_nhan"],
        legal_status="amended",
        download_url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/7/101-nd.signed.pdf",
    ),
    DocumentSource(
        doc_id="10-2024-TT-BTNMT",
        document_number="10/2024/TT-BTNMT",
        document_title=(
            "Thông tư số 10/2024/TT-BTNMT quy định về hồ sơ địa chính, Giấy chứng nhận "
            "quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất"
        ),
        document_type="thong_tu",
        issuing_body="Bộ Tài nguyên và Môi trường",
        issued_date="2024-07-31",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/?pageid=27160&docid=210905&classid=1",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["dat_dai", "dang_ky_dat_dai", "giay_chung_nhan"],
        legal_status="active",
        download_url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/8/10-btnmt.pdf",
    ),
]


class LegalCrawler:
    """Automated Legal Document Crawler and Downloader (ADR-0003)."""

    def __init__(self, storage_dir: str = "data/corpus/raw"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.storage_dir / "manifest.json"

    async def fetch_document(
        self, source: DocumentSource, client: httpx.AsyncClient
    ) -> dict[str, Any]:
        """Fetch HTML content from official portal, calculate SHA-256, and save snapshot."""
        logger.info(f"Crawling document [{source.doc_id}] from: {source.source_url}")
        raw_file = self.storage_dir / f"{source.doc_id}{'.pdf' if source.download_url else '.html'}"
        text_file = self.storage_dir / f"{source.doc_id}.txt"

        raw_content: str | bytes = ""
        clean_text = ""
        status = "crawled_pdf" if source.download_url else "crawled"

        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            }
            response = await client.get(
                source.download_url or source.source_url,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            is_pdf = "application/pdf" in content_type or response.content.startswith(b"%PDF")
            if is_pdf:
                raw_content = response.content
                reader = PdfReader(BytesIO(response.content))
                clean_text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
            else:
                raw_content = response.text
                soup = BeautifulSoup(raw_content, "html.parser")
                content_div = (
                    soup.find("div", class_="content")
                    or soup.find("div", id="content")
                    or soup.find("div", class_="doc-content")
                    or soup.find("div", class_="detail-content")
                    or soup.body
                )

                if content_div:
                    for tag in content_div(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    clean_text = content_div.get_text(separator="\n", strip=True)
                else:
                    clean_text = soup.get_text(separator="\n", strip=True)

            # If portal response is only site navigation without articles (ASP.NET / client-side tab)
            if clean_text.count("Điều ") < 2:
                seed_file = Path("data/corpus/seed") / f"{source.doc_id}.txt"
                if seed_file.exists():
                    logger.info(f"Loaded verified seed text for [{source.doc_id}]")
                    clean_text = seed_file.read_text(encoding="utf-8")
                    raw_html = f"<html><body><pre>{clean_text}</pre></body></html>"
                    status = "verified_seed"
                    raw_content = raw_html
                elif raw_file.exists() and text_file.exists():
                    raw_content = (
                        raw_file.read_bytes()
                        if raw_file.suffix == ".pdf"
                        else raw_file.read_text(encoding="utf-8")
                    )
                    clean_text = text_file.read_text(encoding="utf-8")
                    status = "cached"
                else:
                    raise ValueError(
                        f"Official response for {source.document_number} did not contain "
                        "a legal document body."
                    )

        except Exception as e:
            logger.warning(
                f"Failed to crawl live URL for {source.doc_id} ({e}). Checking local seed/cache."
            )
            seed_file = Path("data/corpus/seed") / f"{source.doc_id}.txt"
            if seed_file.exists():
                clean_text = seed_file.read_text(encoding="utf-8")
                raw_content = f"<html><body><pre>{clean_text}</pre></body></html>"
                status = "verified_seed"
            elif raw_file.exists() and text_file.exists():
                raw_content = (
                    raw_file.read_bytes()
                    if raw_file.suffix == ".pdf"
                    else raw_file.read_text(encoding="utf-8")
                )
                clean_text = text_file.read_text(encoding="utf-8")
                status = "cached"
            else:
                raise RuntimeError(
                    f"No verified official content, seed, or cache is available for "
                    f"{source.document_number}."
                ) from e

        # Save files
        if isinstance(raw_content, bytes):
            raw_file.write_bytes(raw_content)
        else:
            raw_file.write_text(raw_content, encoding="utf-8")
        text_file.write_text(clean_text, encoding="utf-8")

        sha256 = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

        return {
            **asdict(source),
            "status": status,
            "sha256": sha256,
            "raw_document_path": str(raw_file),
            "clean_text_path": str(text_file),
            "character_count": len(clean_text),
        }

    async def crawl_corpus(self, sources: list[DocumentSource]) -> list[dict[str, Any]]:
        """Fetch a document tier and merge its records into the corpus manifest."""
        existing: dict[str, dict[str, Any]] = {}
        if self.manifest_path.exists():
            existing = {
                item["doc_id"]: item
                for item in json.loads(self.manifest_path.read_text(encoding="utf-8"))
            }

        async with httpx.AsyncClient() as client:
            for source in sources:
                item = await self.fetch_document(source, client)
                existing[source.doc_id] = item

        manifest = list(existing.values())
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"Crawl complete. {len(manifest)} documents registered in manifest.")
        return manifest

    async def crawl_p0_corpus(self) -> list[dict[str, Any]]:
        """Fetch all documents in the Corpus P0 registry."""
        return await self.crawl_corpus(P0_CORPUS_REGISTRY)

    async def crawl_p1_corpus(self) -> list[dict[str, Any]]:
        """Fetch all documents in the Corpus P1 registry."""
        return await self.crawl_corpus(P1_CORPUS_REGISTRY)

    async def crawl_mvp_corpus(self) -> list[dict[str, Any]]:
        """Fetch both MVP corpus tiers."""
        return await self.crawl_corpus(P0_CORPUS_REGISTRY + P1_CORPUS_REGISTRY)
