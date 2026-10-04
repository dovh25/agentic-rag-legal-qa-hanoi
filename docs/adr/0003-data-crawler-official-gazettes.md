# ADR-0003: Chiến lược Thu thập Dữ liệu — Tự động Cào & Tải từ Cổng VBPL Chính thức

- **Trạng thái**: Accepted
- **Ngày quyết định**: 2026-10-04
- **Người quyết định**: Vũ Huy Đô (Senior AI Engineer / Tech Lead)
- **Tài liệu liên quan**: [docs/PRD.md](../PRD.md), [.agents/skills/legal-corpus-ingest/SKILL.md](../../.agents/skills/legal-corpus-ingest/SKILL.md)

---

## 1. Bối cảnh & Vấn đề (Context)
Corpus pháp lý của dự án bao gồm các văn bản luật trung ương và quy định đặc thù của Hà Nội (Luật Đất đai 31/2024, Nghị định 88/2024, Nghị định 102/2024, Quyết định 61/2024 Hà Nội, Nghị quyết 52/2025 Bảng giá đất Hà Nội).

Có 2 phương án tiếp cận để nạp dữ liệu:
1. *Nạp thủ công*: Tìm tải file PDF/DOCX, copy text thủ công vào repo.
2. *Thu thập tự động (Automated Scraper/Crawler)*: Xây dựng pipeline tự động fetch nội dung HTML/PDF sạch từ các cổng công báo điện tử chính thức, trích xuất cấu trúc văn bản kèm URL nguồn nguyên bản.

## 2. Quyết định (Decision)
Dự án quyết định xây dựng **Module Thu thập Dữ liệu Tự động (Automated Legal Crawler & Downloader)**:
- **Nguồn thu thập**:
  - Cổng Thông tin điện tử Chính phủ / Cổng VBPL Quốc gia: `https://vanban.chinhphu.vn` và `https://vbpl.vn`.
  - Công báo điện tử Thành phố Hà Nội: `https://congbao.hanoi.gov.vn`.
- **Phương thức thực hiện**:
  - Script crawler trong `src/ingest/crawler.py` (sử dụng `httpx` + `BeautifulSoup4`).
  - Tải trực tiếp định dạng HTML chính thức để bảo đảm 100% độ nguyên vẹn văn bản (tránh lỗi OCR từ các bản PDF scan mờ).
  - Tự động lưu bản snapshot offline trong `data/corpus/raw/` kèm SHA-256 checksum để đảm bảo tính lặp lại (Reproducibility) và lưu vết nguồn gốc (Provenance).

## 3. Các phương án đã cân nhắc (Alternatives Considered)

| Tiêu chí | Cào Tự động (Được chọn) | Nạp Thủ công (Manual PDF) | Dùng Dataset RAG có sẵn |
|---|---|---|---|
| **Độ tin cậy & Nguồn gốc** | **100% Chính thức (Cổng VBPL)** | Dễ sai sót khi copy | Không có văn bản Hà Nội 2024-2025 |
| **Tính cập nhật** | Tự động cập nhật khi có sửa đổi | Tốn công sức cập nhật | Lỗi thời |
| **Chất lượng văn bản** | HTML text sạch, không lỗi OCR | PDF scan dễ lỗi font, mất dấu | Không kiểm soát được |
| **Khả năng mở rộng (P1, P2)**| Rất cao (chỉ cần thêm URL) | Tốn nhiều nhân công | Thấp |

## 4. Hệ quả (Consequences)

### Tích cực:
- Lưu vết đường dẫn URL nguồn chính thức cho 100% chunks phục vụ trích dẫn (`source_url`).
- Định dạng HTML giúp parser bóc tách thẻ chương, điều, khoản dễ dàng và chính xác hơn so với bóc tách từ PDF nhị phân.
- Tái lập kết quả nạp dữ liệu bất cứ lúc nào qua script tự động.

### Hạn chế & Giảm thiểu:
- Cần xử lý giới hạn tốc độ (Rate limiting) và cấu trúc HTML thay đổi giữa các cổng.
  *Giảm thiểu:* Thiết lập delay giữa các request, lưu bản cache snapshot offline tại `data/corpus/` để không phải cào lại nhiều lần.
