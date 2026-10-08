# Architecture Decision Records (ADR)

Thư mục này ghi nhận các quyết định kiến trúc và công nghệ quan trọng cho dự án **Agentic RAG Legal QA — Hà Nội**, phục vụ quá trình phát triển, kiểm thử và đánh giá nghiệm thu.

## Danh mục Quyết định Kiến trúc (ADR Index)

| Mã ADR | Tiêu đề Quyết định | Trạng thái | Ngày quyết định |
|---|---|---|---|
| [**ADR-0001**](0001-embedding-model-bge-m3.md) | Lựa chọn Mô hình Embedding BAAI/bge-m3 (Dense 1024-dim + Sparse BM25) | `Superseded by ADR-0005` | 2026-10-04 |
| [**ADR-0002**](0002-llm-engine-google-gemini.md) | Lựa chọn LLM Engine — Google Gemini API (Free Tier qua OpenAI Protocol) | `Accepted` | 2026-10-04 |
| [**ADR-0003**](0003-data-crawler-official-gazettes.md) | Chiến lược Thu thập Dữ liệu — Tự động Cào & Tải từ Cổng VBPL Chính thức | `Accepted` | 2026-10-04 |
| [**ADR-0004**](0004-qdrant-hybrid-retrieval.md) | Lựa chọn Qdrant Vector Store & Kiến trúc Hybrid Retrieval | `Accepted` | 2026-10-04 |
| [**ADR-0005**](0005-gemini-embedding.md) | Chuyển Embedding sang Google Gemini và version hóa Qdrant collection | `Accepted` | 2026-10-04 |

---

## Cấu trúc chuẩn của một ADR
1. **Tiêu đề**: Mã số và tên quyết định súc tích.
2. **Trạng thái**: `Proposed` / `Accepted` / `Superseded`.
3. **Bối cảnh & Vấn đề (Context)**: Vấn đề cần giải quyết, yêu cầu nghiệp vụ và kỹ thuật.
4. **Quyết định (Decision)**: Giải pháp được lựa chọn và cơ chế thực thi.
5. **Các phương án đã cân nhắc (Alternatives Considered)**: So sánh định lượng giữa các lựa chọn.
6. **Hệ quả (Consequences)**: Lợi ích đạt được, đánh đổi và biện pháp giảm thiểu rủi ro.
