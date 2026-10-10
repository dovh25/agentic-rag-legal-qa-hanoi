# ADR-0001: Lựa chọn Mô hình Embedding BAAI/bge-m3 (Dense 1024-dim + Sparse BM25)

- **Trạng thái**: Accepted
- **Ngày quyết định**: 2026-10-04
- **Người quyết định**: Vũ Huy Đô (Senior AI Engineer / Tech Lead)
- **Tài liệu liên quan**: [docs/PRD.md](../PRD.md), [docs/Brief.md](../Brief.md), [.agents/skills/legal-corpus-ingest/SKILL.md](../../.agents/skills/legal-corpus-ingest/SKILL.md)

> **Implementation note (2026-10-10):** Dense 1024-dim và Sparse BM25 đã được implement đầy đủ.
> Embedding sử dụng Hugging Face Inference API (GPU-accelerated, free tier) kết hợp Redis cache (TTL 30 ngày).
> Sparse BM25 vectors đã được materialize vào Qdrant collection `legal_chunks` và hoạt động trong production.

---

## 1. Bối cảnh & Vấn đề (Context)
Hệ thống Legal QA chuyên sâu cho Thành phố Hà Nội đòi hỏi khả năng truy xuất cực kỳ chính xác văn bản pháp lý tiếng Việt ở cấp độ **Khoản / Điều**. Các văn bản pháp luật có cấu trúc ngữ nghĩa chặt chẽ, thuật ngữ chuyên ngành dày đặc (ví dụ: *bồi thường, hỗ trợ, tái định cư, giá đất cụ thể, hạn mức giao đất, thu hồi đất vì lợi ích quốc gia*).

Yêu cầu đặt ra:
1. Nắm bắt sâu sắc ngữ nghĩa tiếng Việt đa tầng.
2. Hỗ trợ truy xuất lai (Hybrid Retrieval: Semantic Dense + Lexical Sparse) để bắt chính xác các từ khóa số hiệu điều luật mà không bị trôi ngữ nghĩa.
3. Hoạt động độc lập, chi phí 0 VNĐ, không bị phụ thuộc vào quota token hay chi phí API embedding đám mây trả phí.

## 2. Quyết định (Decision)
Dự án quyết định lựa chọn **`BAAI/bge-m3`** làm mô hình Embedding chủ lực:
- **Kích thước vector dense**: 1024 chiều (Cosine distance).
- **Hỗ trợ đa phương thức**: Dense retrieval, Multi-vector (ColBERT style), và Sparse lexical weights (tương đương BM25 có trọng số ngữ cảnh).
- **Ngôn ngữ**: Hỗ trợ xuất sắc tiếng Việt (thuộc nhóm mô hình SOTA trên benchmark tiếng Việt).
- **Môi trường triển khai**: Hugging Face Inference API (GPU-accelerated, free tier) với Redis cache layer; fallback local sentence-transformers khi cần.

## 3. Các phương án đã cân nhắc (Alternatives Considered)

| Tiêu chí | BAAI/bge-m3 (Được chọn) | OpenAI text-embedding-3-small | Sentence-BERT multilingual |
|---|---|---|---|
| **Chi phí** | **0 VNĐ (Miễn phí vĩnh viễn)** | Trả phí per-token | 0 VNĐ |
| **Kích thước vector** | 1024-dim | 1536-dim | 768-dim |
| **Sparse / BM25 Weight** | Có sẵn natively | Không (phải dựng BM25 riêng) | Không |
| **Bảo mật & Offline** | API calls không lưu dữ liệu; Redis cache local | Gửi dữ liệu ra Cloud | 100% Local |
| **Độ chính xác tiếng Việt** | Rất cao (Top benchmark MTEB) | Tốt | Trung bình |

## 4. Hệ quả (Consequences)

### Tích cực:
- Hoàn toàn miễn phí chi phí embedding khi ingest hàng chục nghìn chunks pháp luật.
- Kết hợp hoàn hảo với Qdrant Vector DB (hỗ trợ lưu cả Dense 1024-dim và Sparse payload).
- Embedding không lưu dữ liệu pháp luật ở HF; Redis cache giảm latency và quota usage.

### Hạn chế & Giảm thiểu:
- Phụ thuộc network cho HF Inference API.
  *Giảm thiểu:* Retry với exponential backoff; fallback sang local sentence-transformers; Redis cache giảm 90%+ API calls.
