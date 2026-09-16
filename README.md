<div align="center">

# ⚖️ Agentic RAG Legal QA — Hà Nội

**Prototype tra cứu văn bản pháp luật về đất đai, quy hoạch, thu hồi đất, bồi thường và tái định cư tại Hà Nội**

> Đồ án Liên ngành · Khoa Trí tuệ nhân tạo và Khoa học dữ liệu  
> Giảng viên hướng dẫn: ThS. Nguyễn Văn Sơn · Sinh viên: Vũ Huy Đô

[![Status](https://img.shields.io/badge/Status-Design%20%2F%20Development-orange?style=flat-square)]()
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

## Mục tiêu và phạm vi

Đây là **MVP nghiên cứu**, không phải hệ thống tư vấn pháp lý hay công cụ xác định mức bồi thường cho một hồ sơ cụ thể. Hệ thống nhận câu hỏi tiếng Việt, tìm đoạn văn bản liên quan, kiểm tra tính áp dụng theo thời điểm và xuất câu trả lời mà mỗi kết luận phải truy vết được về nguồn.

Corpus ưu tiên văn bản còn hiệu lực hoặc có lịch sử hiệu lực xác định được: Luật Đất đai và văn bản hướng dẫn; văn bản quy hoạch/QPPL của Hà Nội; bảng giá đất và văn bản địa phương có **phiên bản, thời điểm áp dụng và nguồn chính thức** rõ ràng.

Mức bồi thường thực tế còn phụ thuộc hồ sơ, vị trí, loại đất, dự án, quyết định hành chính và dữ liệu định giá. Hệ thống chỉ giải thích quy định, hiển thị nguồn và nêu dữ kiện còn thiếu; không suy diễn ra một con số nếu nguồn không đủ.

Chi tiết mục tiêu nghiên cứu, tiêu chí nghiệm thu và giới hạn được thống nhất trong [PROPOSAL.md](PROPOSAL.md).

## Trạng thái triển khai

Tài liệu này mô tả **kiến trúc mục tiêu**. Những đường dẫn mã nguồn, API và lệnh vận hành chỉ được xem là cam kết khi chúng đã xuất hiện trong repository và có kiểm thử tương ứng. Trước khi có bản chạy được, không tuyên bố crawler, agent, API hay dữ liệu đã sẵn sàng.

## Nguyên tắc kỹ thuật

1. **Nguồn chính thức trước.** Cổng VBPL của cơ quan nhà nước, Công báo và cổng Hà Nội là nguồn chứng cứ. Nguồn thương mại/chỉ mục chỉ dùng để phát hiện tài liệu, không làm nguồn trích dẫn cuối cùng nếu có bản chính thức.
2. **Thời điểm là một phần của truy vấn.** Mặc định trả lời “tại ngày truy vấn”; người dùng có thể nêu `as_of_date`. Bộ lọc hiệu lực xét ngày hiệu lực, ngày hết hiệu lực, văn bản thay thế/sửa đổi và phạm vi áp dụng.
3. **Không có bằng chứng thì không kết luận.** Citation được tạo từ chunk đã chọn, sau đó đối chiếu lại `doc_id`, điều/khoản và URL; thiếu nguồn, mâu thuẫn nguồn hoặc retrieval dưới ngưỡng sẽ trả lời có kiểm soát/đề nghị làm rõ.
4. **Agent có ngân sách.** LangGraph chỉ điều phối đồ thị trạng thái xác định: giới hạn số sub-query, số lần truy xuất, thời gian và token. Agent không được tự duyệt web mở hay tự khẳng định hiệu lực pháp lý.
5. **Đánh giá tách retrieval khỏi generation.** Không dùng “điểm confidence” của LLM như xác suất đúng. Chất lượng citation, độ phủ bằng chứng và tỷ lệ từ chối đúng được đo riêng trên bộ dữ liệu gán nhãn.

## Kiến trúc mục tiêu

```text
Web UI / API
     │
     ▼
Query normalizer ──► intent, thực thể, as_of_date, metadata filter
     │
     ▼
LangGraph (đồ thị có giới hạn ngân sách)
  ├─ single-hop: Hybrid retrieval → rerank → validation
  └─ multi-hop: planner → retrieval song song (tối đa N) → validation
     │
     ▼
Evidence selector → Answer generator → Citation verifier → Answer | Abstain
     │
     ▼
Qdrant (dense + sparse/BM25 + payload)  ←→ PostgreSQL/object storage (bản gốc, phiên bản, audit)
```

Một câu hỏi đơn giản không cần planner. Đây là lựa chọn có chủ ý để giảm độ trễ, chi phí và bề mặt lỗi; Agentic RAG chỉ bật khi router phát hiện câu hỏi đa ý hoặc cần đối chiếu nhiều văn bản.

### Luồng truy vấn

1. Chuẩn hoá câu hỏi, trích xuất địa bàn, loại đất, loại thủ tục và thời điểm áp dụng; yêu cầu làm rõ nếu thiếu dữ kiện quyết định.
2. Xây filter theo hiệu lực/phạm vi, rồi chạy **hybrid retrieval**: dense BGE-M3 và lexical/sparse retrieval. Hợp nhất kết quả bằng RRF, lấy top 20 để rerank và chọn tối đa 5 đoạn làm bằng chứng.
3. Validator kiểm tra provenance, trùng lặp, điều/khoản, quan hệ sửa đổi-thay thế và điều kiện hiệu lực tại `as_of_date`.
4. Generator chỉ dùng evidence đã duyệt. Mỗi mệnh đề pháp lý phải có citation; nếu một phần không được hỗ trợ, câu trả lời phải chỉ rõ phần đó.
5. Citation verifier kiểm tra citation trỏ đến đúng đoạn; nếu không đạt ngưỡng thì trả về `insufficient_evidence` thay vì câu trả lời tự tin giả.

## Dữ liệu và quản trị corpus

```text
Danh mục nguồn → tải bản gốc → checksum + lưu snapshot → parse/OCR có đánh giá
→ trích xuất cấu trúc → review metadata → chunk theo Điều/Khoản → embed/index → publish version
```

- Tuân thủ điều khoản sử dụng, `robots.txt`, giới hạn tốc độ và yêu cầu cấp phép. Không mặc định crawl toàn bộ website.
- Mỗi lần ingest tạo `corpus_version`; raw artifact, parser version, thời điểm tải và checksum phải được lưu để tái lập kết quả.
- PDF scan được đánh dấu `ocr_quality`; văn bản có OCR thấp không dùng làm nguồn duy nhất cho kết luận.
- Chỉ publish một văn bản khi có số hiệu, cơ quan ban hành, URL nguồn, ngày tải và trạng thái kiểm duyệt metadata.

### Metadata tối thiểu

```jsonc
{
  "doc_id": "uuid", "doc_number": "31/2024/QH15", "doc_title": "Luật Đất đai",
  "doc_type": "law", "issuing_body": "Quốc hội", "source_url": "https://...",
  "source_tier": "official", "source_checksum": "sha256:...", "retrieved_at": "2026-09-16T00:00:00Z",
  "effective_from": "2024-08-01", "effective_to": null, "legal_status": "active",
  "supersedes": [], "amends": [], "scope": "national", "administrative_area": ["Hà Nội"],
  "article": "79", "clause": "1", "point": null, "chunk_id": "...", "chunk_index": 3,
  "parser_version": "...", "corpus_version": "...", "review_status": "approved"
}
```

`legal_status` là dữ liệu đã kiểm duyệt ở cấp văn bản, không phải kết luận do LLM tạo. Các quan hệ `amends`/`supersedes` cho phép giải thích lý do một nguồn bị loại.

## Lưu trữ và retrieval

MVP chốt **Qdrant** làm vector store. Collection `legal_chunks` có dense vector 1024 chiều (BGE-M3), sparse/BM25 vector, HNSW cosine và payload index cho trạng thái pháp lý, mốc hiệu lực, loại/cơ quan ban hành, phạm vi, địa bàn, lĩnh vực, phiên bản corpus và trạng thái review.

PostgreSQL (hoặc object storage cho file lớn) lưu văn bản gốc, quan hệ văn bản, lịch sử ingest, session và audit. Qdrant không thay thế kho nguồn có versioning. Các tham số chunking, HNSW, top-k và ngưỡng abstention là cấu hình thí nghiệm, phải ghi nhận cùng benchmark.

## Hợp đồng API mục tiêu

`POST /api/v1/query` nhận `query`, `as_of_date` (tuỳ chọn), `filters` và `top_k` giới hạn. Response không có trường `confidence` mang nghĩa pháp lý; thay vào đó trả về trạng thái và bằng chứng kiểm chứng được.

```jsonc
{
  "status": "answered", // answered | insufficient_evidence | clarification_needed
  "answer": "...",
  "citations": [{
    "doc_id": "...", "doc_number": "...", "article": "...", "clause": "...",
    "source_url": "...", "quote": "..."
  }],
  "as_of_date": "2026-09-16", "corpus_version": "2026-09-16.1", "limitations": []
}
```

## Đánh giá và tiêu chí nghiệm thu

Benchmark phải có train/dev/test tách biệt, bao phủ câu hỏi đơn giản, multi-hop, văn bản bị sửa đổi/hết hiệu lực, câu hỏi thiếu dữ kiện và ngoài phạm vi. Gold labels cần do người có năng lực pháp lý rà soát; LLM-as-judge chỉ dùng bổ trợ và phải được audit mẫu thủ công.

| Lớp | Chỉ số |
|---|---|
| Retrieval | Recall@K, MRR/nDCG, context precision/recall theo gold evidence |
| Citation | entailment của mệnh đề–evidence, độ chính xác điều/khoản, citation coverage |
| Generation | faithfulness, answer relevancy, tỷ lệ assertion không có chứng cứ |
| Safety | abstention precision/recall, tỷ lệ loại đúng văn bản không còn áp dụng |
| Vận hành | p50/p95 latency, tỷ lệ lỗi, chi phí và tỷ lệ vượt ngân sách |

Ngưỡng cụ thể được chốt trên dev trước khi chạy test cuối. Baseline bắt buộc: BM25, dense RAG một bước và hybrid RAG một bước; Agentic RAG phải được so sánh cùng corpus/model/prompt/ngân sách.

## Roadmap 8 tuần

| Tuần | Đầu ra kiểm chứng được |
|---|---|
| 1 | Data contract, danh mục nguồn chính thức, risk register, schema phiên bản |
| 2–3 | Ingestion lặp lại, parser/OCR QA, corpus pilot đã review |
| 4 | Hybrid retrieval baseline và tập gold dev/test ban đầu |
| 5 | Citation verifier, abstention và audit log |
| 6 | LangGraph giới hạn ngân sách cho truy vấn multi-hop |
| 7 | Ablation/benchmark, phân tích lỗi và sửa dữ liệu/retrieval |
| 8 | API/UI demo, tái lập thí nghiệm, báo cáo giới hạn |

## Tài liệu pháp lý khởi đầu

- [Luật Đất đai số 31/2024/QH15](https://vanban.chinhphu.vn/?classid=1&docid=211189&orggroupid=1&pageid=27160).
- [Nghị định 88/2024/NĐ-CP về bồi thường, hỗ trợ, tái định cư](https://vanban.chinhphu.vn/?classid=0&docid=210658&pageid=27160).
- [Nghị quyết 52/2025/NQ-HĐND về Bảng giá đất Hà Nội áp dụng từ 01/01/2026](https://congbao.hanoi.gov.vn/Default.aspx?p_attribute=5054&pageid=45002).

Danh mục trên chỉ là seed list; mỗi tài liệu phải được xác minh và version hoá trong pipeline trước khi đưa vào corpus.

## Disclaimer pháp lý

Hệ thống chỉ hỗ trợ tra cứu. Kết quả không phải tư vấn pháp lý, không thay thế quyết định của cơ quan có thẩm quyền hoặc ý kiến luật sư. Người dùng phải kiểm tra văn bản gốc và tình trạng hiệu lực tại thời điểm áp dụng trước khi đưa ra quyết định.
