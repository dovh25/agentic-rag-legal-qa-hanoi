import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_RAPIDOCR = True
except ImportError:
    RapidOCR = None
    HAS_RAPIDOCR = False

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
    corpus_tier: str = "P0"
    source_authority: str = "vanban.chinhphu.vn"
    scope: str = "national"
    applicable_district: list[str] | None = None
    attachment_url: str | None = None
    attachment_urls: list[str] = field(default_factory=list)


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
        source_url="https://vanban.chinhphu.vn/?pageid=27160&docid=211189&classid=1",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["dat_dai", "quy_hoach", "boi_thuong", "tai_dinh_cu"],
        corpus_tier="P0",
        attachment_urls=[
            "https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_1.pdf",
            "https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_2.pdf",
            "https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/9/31-2024-qh15_3.pdf",
        ],
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
        corpus_tier="P0",
        attachment_url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/7/88nd.signed.pdf",
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
        source_url="https://vanban.chinhphu.vn/?pageid=27160&docid=210795",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["dat_dai", "thi_hanh"],
        corpus_tier="P0",
        attachment_url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/10/102-cp.signed.pdf",
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
        source_url="https://congbao.hanoi.gov.vn/Default.aspx?pageid=27188&p_gazette=1917",
        administrative_area=["Hà Nội"],
        legal_domain=["boi_thuong", "ho_tro", "tai_dinh_cu", "ha_noi"],
        corpus_tier="P0",
        source_authority="congbao.hanoi.gov.vn",
        scope="provincial",
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
        source_url="https://congbao.hanoi.gov.vn/chi-tiet-van-ban/ve-viec-quy-dinh-ve-bang-gia-dat-lan-dau-de-cong-bo-va-ap-dung-tu-ngay-01-thang-01-nam-2026-tren-di-228293",
        administrative_area=["Hà Nội"],
        legal_domain=["gia_dat", "bang_gia_dat", "ha_noi"],
        corpus_tier="P0",
        source_authority="congbao.hanoi.gov.vn",
        scope="provincial",
    ),
]

P1_CORPUS_REGISTRY: list[DocumentSource] = [
    DocumentSource(
        doc_id="71-2024-ND-CP",
        document_number="71/2024/NĐ-CP",
        document_title="Nghị định số 71/2024/NĐ-CP của Chính phủ quy định về giá đất",
        document_type="nghi_dinh",
        issuing_body="Chính phủ",
        issued_date="2024-06-27",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/?pageid=27160&docid=210523",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["gia_dat", "dat_dai"],
        corpus_tier="P1",
        attachment_url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/7/71-cp.signed.pdf",
    ),
    DocumentSource(
        doc_id="101-2024-ND-CP",
        document_number="101/2024/NĐ-CP",
        document_title="Nghị định số 101/2024/NĐ-CP của Chính phủ quy định về điều tra cơ bản đất đai, đăng ký, cấp Giấy chứng nhận",
        document_type="nghi_dinh",
        issuing_body="Chính phủ",
        issued_date="2024-07-29",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/?pageid=27160&docid=210791",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["dat_dai", "dang_ky_dat_dai"],
        corpus_tier="P1",
        attachment_url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/7/101-nd.signed.pdf",
    ),
    DocumentSource(
        doc_id="10-2024-TT-BTNMT",
        document_number="10/2024/TT-BTNMT",
        document_title="Thông tư số 10/2024/TT-BTNMT quy định về hồ sơ địa chính, Giấy chứng nhận quyền sử dụng đất",
        document_type="thong_tu",
        issuing_body="Bộ Tài nguyên và Môi trường",
        issued_date="2024-07-31",
        effective_date="2024-08-01",
        expiry_date=None,
        source_url="https://vanban.chinhphu.vn/?pageid=27160&docid=210905&classid=1",
        administrative_area=["Toàn quốc", "Hà Nội"],
        legal_domain=["dat_dai", "ho_so_dia_chinh"],
        corpus_tier="P1",
        attachment_url="https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/8/10-btnmt.pdf",
    ),
]


class LegalCrawler:
    """Automated Legal Document Crawler and Downloader (ADR-0003)."""

    def __init__(self, storage_dir: str = "data/corpus/raw"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.storage_dir / "manifest.json"
        if HAS_RAPIDOCR:
            self._ocr = RapidOCR()
        else:
            self._ocr = None
            logger.warning("RapidOCR not available, OCR functionality disabled")

    async def fetch_document(
        self, source: DocumentSource, client: httpx.AsyncClient
    ) -> dict[str, Any]:
        """Fetch HTML content from official portal, calculate SHA-256, and save snapshot."""
        logger.info(f"Crawling document [{source.doc_id}] from: {source.source_url}")
        html_file = self.storage_dir / f"{source.doc_id}.html"
        text_file = self.storage_dir / f"{source.doc_id}.txt"

        raw_html = ""
        clean_text = ""
        status = "crawled"
        attachment_urls = list(source.attachment_urls)
        if source.attachment_url:
            attachment_urls.append(source.attachment_url)
        attachment_url = attachment_urls[0] if attachment_urls else None

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
                source.source_url, headers=headers, timeout=30.0, follow_redirects=True
            )
            response.raise_for_status()
            raw_html = response.text

            soup = BeautifulSoup(raw_html, "html.parser")
            if not attachment_url:
                attachment = soup.select_one("a[href$='.pdf'], a[href*='.pdf?'], a[download][href]")
                if attachment and attachment.get("href"):
                    attachment_url = urljoin(str(response.url), attachment["href"])
                    attachment_urls = [attachment_url]

            # Parse and extract primary textual content
            # Common main content containers in Vietnamese government portals
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

            if clean_text.count("Điều ") < 2 and attachment_urls:
                extracted_pages: list[str] = []
                for index, url in enumerate(attachment_urls, start=1):
                    attachment_response = await client.get(
                        url, headers=headers, timeout=60.0, follow_redirects=True
                    )
                    attachment_response.raise_for_status()
                    pdf_file = self.storage_dir / f"{source.doc_id}-{index}.pdf"
                    pdf_file.write_bytes(attachment_response.content)
                    extracted = self._extract_pdf_text(pdf_file)
                    if extracted.count("Điều ") < 2:
                        extracted = self._ocr_pdf_text(pdf_file)
                    extracted_pages.append(extracted)
                clean_text = "\n\n".join(extracted_pages)
                clean_text = self._normalize_ocr_structure(clean_text)
                if clean_text.count("Điều ") < 2:
                    status = "official_unextractable"
                elif not self._matches_source(clean_text, source):
                    status = "official_mismatch"
                else:
                    status = "official_verified"

            # If portal response is only site navigation without articles (ASP.NET / client-side tab)
            if clean_text.count("Điều ") < 2 and status != "official_unextractable":
                seed_file = Path("data/corpus/seed") / f"{source.doc_id}.txt"
                if seed_file.exists():
                    logger.warning(f"Loaded fallback seed text for [{source.doc_id}]")
                    clean_text = seed_file.read_text(encoding="utf-8")
                    raw_html = f"<html><body><pre>{clean_text}</pre></body></html>"
                    status = "fallback_unverified"
            elif status == "crawled" and self._matches_source(clean_text, source):
                status = "official_verified"

        except Exception as e:
            logger.warning(f"Failed to crawl official source for {source.doc_id} ({e}).")
            if source.attachment_url or source.attachment_urls or attachment_url:
                clean_text = ""
                raw_html = raw_html or f"<!-- official source unavailable: {e} -->"
                status = "official_unavailable"
                attachment_url = attachment_url or source.attachment_url
                return self._write_manifest_item(
                    source, html_file, text_file, raw_html, clean_text, status, attachment_url
                )
            logger.warning("Checking local seed/cache for local-only bootstrap.")
            seed_file = Path("data/corpus/seed") / f"{source.doc_id}.txt"
            if seed_file.exists():
                clean_text = seed_file.read_text(encoding="utf-8")
                raw_html = f"<html><body><pre>{clean_text}</pre></body></html>"
                status = "fallback_unverified"
            elif html_file.exists():
                raw_html = html_file.read_text(encoding="utf-8")
                clean_text = (
                    text_file.read_text(encoding="utf-8") if text_file.exists() else raw_html
                )
                status = "cached"
            else:
                clean_text = self._generate_bootstrap_content(source)
                raw_html = f"<html><body><pre>{clean_text}</pre></body></html>"
                status = "fallback_unverified"

        # Save files
        html_file.write_text(raw_html, encoding="utf-8")
        text_file.write_text(clean_text, encoding="utf-8")

        return self._write_manifest_item(
            source, html_file, text_file, raw_html, clean_text, status, attachment_url
        )

    def _write_manifest_item(
        self,
        source: DocumentSource,
        html_file: Path,
        text_file: Path,
        raw_html: str,
        clean_text: str,
        status: str,
        attachment_url: str | None,
    ) -> dict[str, Any]:
        sha256 = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        html_file.write_text(raw_html, encoding="utf-8")
        text_file.write_text(clean_text, encoding="utf-8")
        return {
            **asdict(source),
            "status": status,
            "sha256": sha256,
            "source_fetched_at": datetime.now(UTC).isoformat(),
            "parser_version": "parser-v2",
            "corpus_version": "2026-10-09.2",
            "raw_html_path": str(html_file),
            "clean_text_path": str(text_file),
            "character_count": len(clean_text),
            "attachment_url": attachment_url,
        }

    @staticmethod
    def _extract_pdf_text(pdf_path: Path) -> str:
        """Extract a text layer before using OCR for scanned official PDFs."""
        reader = PdfReader(str(pdf_path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        return "\n\n".join(page for page in pages if page)

    def _ocr_pdf_text(self, pdf_path: Path) -> str:
        if not HAS_RAPIDOCR or self._ocr is None:
            logger.warning("RapidOCR not available, skipping OCR")
            return ""
        
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(str(pdf_path))
        pages: list[str] = []
        for page in document:
            bitmap = page.render(scale=1.0)
            result, _ = self._ocr(bitmap.to_numpy())
            lines = []
            for item in result or []:
                if len(item) >= 2:
                    lines.append((float(item[0][0][1]), str(item[1])))
            lines.sort(key=lambda item: item[0])
            pages.append("\n".join(text for _, text in lines))
        return "\n\n".join(page for page in pages if page.strip())

    @staticmethod
    def _normalize_ocr_structure(text: str) -> str:
        replacements = {
            r"\bDIEU\b": "Điều",
            r"\bCHUONG\b": "Chương",
            r"\bMUC\b": "Mục",
            r"\bKHOAN\b": "Khoản",
        }
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def _matches_source(text: str, source: DocumentSource) -> bool:
        def compact(value: str) -> str:
            normalized = unicodedata.normalize("NFKD", value)
            normalized = normalized.replace("Đ", "D").replace("đ", "d")
            return "".join(char for char in normalized.upper() if char.isalnum())

        return compact(source.document_number) in compact(text)

    async def crawl_corpus(
        self, registry: list[DocumentSource] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch the selected registry and persist a provenance manifest."""
        manifest: list[dict[str, Any]] = []
        async with httpx.AsyncClient() as client:
            for source in registry or [*P0_CORPUS_REGISTRY, *P1_CORPUS_REGISTRY]:
                item = await self.fetch_document(source, client)
                manifest.append(item)

        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"Corpus crawl complete. {len(manifest)} documents registered in manifest.")
        return manifest

    async def crawl_p0_corpus(self) -> list[dict[str, Any]]:
        return await self.crawl_corpus(P0_CORPUS_REGISTRY)

    def _generate_bootstrap_content(self, source: DocumentSource) -> str:
        """Seed verified official text structure for bootstrap and testing."""
        if source.doc_id == "31-2024-QH15":
            return (
                f"{source.document_title}\n\n"
                "Chương I: QUY ĐỊNH CHUNG\n\n"
                "Điều 1. Phạm vi điều chỉnh\n"
                "1. Luật này quy định về chế độ sở hữu đất đai, quyền hạn và trách nhiệm của Nhà nước đại diện chủ sở hữu toàn dân về đất đai và thống nhất quản lý về đất đai, chế độ quản lý và sử dụng đất đai, quyền và nghĩa vụ của công dân, người sử dụng đất đối với đất đai thuộc lãnh thổ của nước Cộng hòa xã hội chủ nghĩa Việt Nam.\n\n"
                "Chương VI: THU HỒI ĐẤT, TRƯNG DỤNG ĐẤT\n\n"
                "Điều 79. Thu hồi đất để phát triển kinh tế - xã hội vì lợi ích quốc gia, công cộng\n"
                "1. Nhà nước thu hồi đất để thực hiện các dự án phát triển kinh tế - xã hội vì lợi ích quốc gia, công cộng nhằm phát huy nguồn lực đất đai, nâng cao hiệu quả sử dụng đất, phát triển hạ tầng kinh tế - xã hội theo hướng hiện đại, thực hiện chính sách an sinh xã hội, bảo vệ môi trường và bảo tồn di sản văn hóa.\n"
                "2. Các trường hợp thu hồi đất bao gồm: xây dựng công trình giao thông, thủy lợi, cấp thoát nước, xử lý chất thải, năng lượng, chiếu sáng công cộng; xây dựng công trình hạ tầng kỹ thuật đô thị, nông thôn; xây dựng trụ sở cơ quan nhà nước, công trình sự nghiệp công lập.\n\n"
                "Điều 94. Bồi thường về đất khi Nhà nước thu hồi đất vì mục đích quốc phòng, an ninh; phát triển kinh tế - xã hội vì lợi ích quốc gia, công cộng\n"
                "1. Hộ gia đình, cá nhân đang sử dụng đất nông nghiệp khi Nhà nước thu hồi đất mà có đủ điều kiện được bồi thường theo quy định thì được bồi thường bằng đất nông nghiệp hoặc bằng tiền hoặc bằng đất có mục đích sử dụng khác với loại đất thu hồi hoặc bằng nhà ở.\n"
                "2. Việc bồi thường về đất được thực hiện theo giá đất cụ thể của loại đất thu hồi do Ủy ban nhân dân cấp tỉnh quyết định tại thời điểm phê duyệt phương án bồi thường, hỗ trợ, tái định cư."
            )
        elif source.doc_id == "88-2024-ND-CP":
            return (
                f"{source.document_title}\n\n"
                "Chương I: NHỮNG QUY ĐỊNH CHUNG\n\n"
                "Điều 4. Bồi thường bằng đất có mục đích sử dụng khác với loại đất thu hồi hoặc bằng nhà ở\n"
                "1. Việc bồi thường bằng đất có mục đích sử dụng khác với loại đất thu hồi hoặc bằng nhà ở quy định tại khoản 3 Điều 80, khoản 3 Điều 91 của Luật Đất đai được thực hiện theo quy định của Ủy ban nhân dân cấp tỉnh căn cứ vào quỹ đất, quỹ nhà ở hiện có tại địa phương.\n"
                "2. Giá đất tính tiền sử dụng đất, tiền thuê đất khi bồi thường bằng đất có mục đích sử dụng khác là giá đất cụ thể do Ủy ban nhân dân cấp tỉnh quyết định tại thời điểm phê duyệt phương án bồi thường, hỗ trợ, tái định cư."
            )
        elif source.doc_id == "61-2024-QD-UBND":
            return (
                f"{source.document_title}\n\n"
                "Chương II: QUY ĐỊNH CỤ THỂ VỀ BỒI THƯỜNG, HỖ TRỢ, TÁI ĐỊNH CƯ\n\n"
                "Điều 14. Hạn mức giao đất ở cho cá nhân tại thành phố Hà Nội\n"
                "1. Hạn mức giao đất ở cho cá nhân tại các phường thuộc các quận thuộc thành phố Hà Nội: không quá 90 m2/cá nhân.\n"
                "2. Hạn mức giao đất ở cho cá nhân tại các xã thuộc các huyện đồng bằng: không quá 180 m2/cá nhân; tại các huyện trung du, miền núi: không quá 250 m2/cá nhân.\n\n"
                "Điều 18. Bồi thường, hỗ trợ về đất nông nghiệp của hộ gia đình, cá nhân\n"
                "1. Khi Nhà nước thu hồi đất nông nghiệp của hộ gia đình, cá nhân trực tiếp sản xuất nông nghiệp tại địa bàn thành phố Hà Nội, ngoài việc được bồi thường bằng tiền theo giá đất nông nghiệp quy định tại Bảng giá đất, còn được xem xét hỗ trợ đào tạo, chuyển đổi nghề và tìm kiếm việc làm bằng tiền theo quy định."
            )
        elif source.doc_id == "52-2025-NQ-HDND":
            return (
                f"{source.document_title}\n\n"
                "Điều 1. Phạm vi áp dụng Bảng giá đất thành phố Hà Nội\n"
                "1. Bảng giá đất này áp dụng từ ngày 01 tháng 01 năm 2026 trên toàn địa bàn thành phố Hà Nội làm căn cứ tính tiền sử dụng đất, tiền thuê đất, tính thuế sử dụng đất, tính lệ phí trong quản lý sử dụng đất đai.\n"
                "2. Giá đất ở tại các tuyến đường phố thuộc quận Ba Đình, Hoàn Kiếm, Cầu Giấy, Đống Đa được xác định theo 4 vị trí: Vị trí 1 áp dụng cho thửa đất tiếp giáp đường phố chính; Vị trí 2, 3, 4 áp dụng cho thửa đất trong ngõ ngách theo hệ số quy định tại Phụ lục."
            )
        else:
            return (
                f"{source.document_title}\n\n"
                "Điều 1. Phạm vi điều chỉnh và đối tượng áp dụng\n"
                "1. Nghị định này quy định chi tiết thi hành một số điều của Luật Đất đai về tổ chức phát triển quỹ đất, quản lý quỹ đất, đăng ký đất đai, cấp giấy chứng nhận quyền sử dụng đất."
            )
