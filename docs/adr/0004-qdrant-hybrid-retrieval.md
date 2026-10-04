# ADR-0004: Lựa chọn Qdrant Vector Store & Kiến trúc Hybrid Retrieval

- **Trạng thái**: Accepted
- **Ngày quyết định**: 2026-10-04
- **Người quyết định**: Vũ Huy Đô (Senior AI Engineer / Tech Lead)
- **Tài liệu liên quan**: [docs/PRD.md](../PRD.md), [docs/Brief.md](../Brief.md), [docker-compose.yml](../../docker-compose.yml)

---

## 1. Bối cảnh & Vấn đề (Context)
Truy xuất văn bản pháp luật đòi hỏi một cơ chế lưu trữ và tìm kiếm vector đáp ứng:
1. Tìm kiếm ngữ nghĩa (Semantic search) kết hợp tìm kiếm từ khóa chính xác (Lexical / BM25 search).
2. Lọc dữ liệu phức tạp (Payload filtering) theo mốc hiệu lực thời gian (`effective_date <= as_of_date` và `expiry_date >= as_of_date`) và địa bàn (`administrative_area`).
3. Khả năng triển khai cục bộ (Self-hosted via Docker) với chi phí 0 VNĐ, hiệu năng cao và độ trễ thấp.

## 2. Quyết định (Decision)
Dự án quyết định chọn **Qdrant** làm Vector Database chính:
- **Collection**: `legal_chunks`
- **Dense Vector**: 1024-dim (`BAAI/bge-m3`), Cosine distance.
- **Sparse Vector / Payload BM25**: Hỗ trợ tìm kiếm từ khóa chính xác điều khoản.
- **Payload Index**: Đánh chỉ mục trường `legal_status`, `document_number`, `article_ref`, `administrative_area`, `effective_date`.
- **Triển khai**: Container hóa qua Docker Compose (`qdrant/qdrant:latest`), mount dữ liệu local.

## 3. Các phương án đã cân nhắc (Alternatives Considered)

| Tiêu chí | Qdrant (Được chọn) | ChromaDB | Milvus | Pinecone |
|---|---|---|---|---|
| **Hiệu năng & Viết bằng** | Rust (Cực nhanh, tiết kiệm RAM) | Python | C++/Go | Cloud-only |
| **Hybrid Search** | Hỗ trợ tuyệt vời (Dense + Sparse) | Hạn chế | Tốt nhưng nặng | Tốt |
| **Payload Filtering** | Rất mạnh mẽ & tối ưu HNSW | Cơ bản | Tốt | Tốt |
| **Chi phí** | **0 VNĐ (Open-source / Docker)** | 0 VNĐ | 0 VNĐ | Trả phí Cloud |
| **Độ phức tạp hạ tầng** | Đơn giản (1 container nhẹ) | Rất đơn giản | Rất phức tạp (nhiều pods) | SaaS |

## 4. Hệ quả (Consequences)

### Tích cực:
- Vận hành cực nhẹ và ổn định trên môi trường dev local.
- Lọc theo điều kiện thời gian `as_of_date` diễn ra ở cấp độ vector index, không làm giảm tốc độ tìm kiếm.
- Chi phí 0 VNĐ.

### Hạn chế & Giảm thiểu:
- Cần Docker để chạy service cục bộ.
  *Giảm thiểu:* Đã tích hợp sẵn `docker-compose.yml` và shortcut `make docker-up` / `make docker-down`.
