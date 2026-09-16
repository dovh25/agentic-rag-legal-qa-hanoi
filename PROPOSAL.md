# HỆ THỐNG HỎI ĐÁP PHÁP LUẬT DỰA TRÊN AGENTIC RAG PHỤC VỤ TRA CỨU QUY HOẠCH, THU HỒI ĐẤT, BỒI THƯỜNG VÀ TÁI ĐỊNH CƯ TẠI HÀ NỘI

> **Đồ án Liên ngành — Khoa Trí tuệ nhân tạo và Khoa học dữ liệu**  
> **Giảng viên hướng dẫn:** ThS. Nguyễn Văn Sơn  
> **Sinh viên thực hiện:** Vũ Huy Đô  
> **Năm học:** 2026–2027 · **Học kỳ:** I

## 1. Tóm tắt đề tài

Đề tài xây dựng một prototype hỏi đáp tiếng Việt có truy xuất tăng cường (RAG) cho corpus văn bản pháp luật về đất đai, quy hoạch, thu hồi đất, bồi thường và tái định cư tại Hà Nội. Hệ thống không coi LLM là nguồn tri thức hay cơ chế xác định hiệu lực. LLM chỉ tổng hợp từ evidence đã được truy xuất, kiểm tra provenance và ràng buộc thời điểm áp dụng.

Agentic RAG được dùng có chọn lọc cho câu hỏi nhiều ý hoặc cần đối chiếu nhiều văn bản. Với câu hỏi đơn giản, hệ thống đi qua pipeline retrieval một bước nhằm bảo đảm độ trễ, chi phí và khả năng kiểm thử. Cả hai luồng đều có cơ chế từ chối trả lời (`insufficient_evidence`) hoặc yêu cầu làm rõ (`clarification_needed`).

README là tài liệu kỹ thuật rút gọn và luôn đồng bộ với proposal này: [README.md](README.md).

## 2. Vấn đề và động lực

Người dùng phải đối chiếu nhiều văn bản trung ương và địa phương, đồng thời quan tâm địa bàn và thời điểm áp dụng. Tìm kiếm từ khoá không giải quyết tốt câu hỏi diễn đạt tự nhiên hoặc đa bước; LLM không có RAG có thể tạo ra số hiệu, điều khoản và suy luận không được nguồn hỗ trợ.

Bài toán không chỉ là “trả lời giống người”, mà là:

1. tìm đúng evidence ở cấp điều/khoản;
2. xác minh nguồn, phiên bản và khả năng áp dụng tại thời điểm hỏi;
3. gắn citation kiểm chứng được cho từng mệnh đề pháp lý;
4. không kết luận khi hồ sơ hoặc bằng chứng không đủ.

Ví dụ, câu hỏi về “mức bồi thường đất ở tại Long Biên” không được trả một mức tiền nếu thiếu vị trí, loại đất, quyết định thu hồi, thời điểm và văn bản địa phương đang áp dụng. Kết quả đúng của hệ thống trong trường hợp này có thể là danh sách quy định liên quan và câu hỏi làm rõ.

## 3. Mục tiêu và phạm vi

### 3.1. Mục tiêu tổng quát

Thiết kế, triển khai và đánh giá prototype Agentic RAG có khả năng trả lời có căn cứ về phạm vi corpus xác định, đồng thời chứng minh được Agentic layer cải thiện gì so với retrieval một bước trong cùng điều kiện thí nghiệm.

### 3.2. Mục tiêu cụ thể và tiêu chí nghiệm thu

| Mục tiêu | Bằng chứng nghiệm thu |
|---|---|
| Xây dựng corpus pháp lý có provenance | Danh mục nguồn, snapshot, checksum, metadata review và `corpus_version` tái lập được |
| Truy xuất đúng evidence | Báo cáo Recall@K, MRR/nDCG, precision/recall theo gold evidence trên tập test khóa |
| Citation có thể kiểm chứng | Citation trỏ đúng document/điều/khoản/đoạn trích; báo cáo citation accuracy và coverage |
| Quản lý hiệu lực/phạm vi | Test case chứa văn bản sửa đổi, thay thế, hết hiệu lực và truy vấn `as_of_date` |
| So sánh Agentic RAG công bằng | Ablation giữa BM25, dense RAG, hybrid RAG và Agentic RAG với cùng corpus/model/prompt/ngân sách |
| Xử lý an toàn | Đo precision/recall của abstention và `clarification_needed`; có audit log cho kết quả |

Mục tiêu ban đầu là xây dựng corpus pilot đã được review và benchmark nội bộ. Quy mô văn bản/cặp QA và ngưỡng chỉ số được chốt sau khảo sát nguồn và trên tập development; không đặt số lượng lớn hoặc tỷ lệ “100% chính xác” khi chưa có phương pháp gán nhãn và baseline.

### 3.3. Phạm vi và ngoài phạm vi

- **Trong phạm vi:** văn bản có nguồn chính thức xác minh được liên quan đến Hà Nội và miền đề tài; văn bản trung ương cần thiết để giải thích quy định địa phương.
- **Thời điểm:** mỗi kết quả gắn `as_of_date` và phiên bản corpus. Mặc định là ngày truy vấn, không phải một trạng thái “hiện hành” mơ hồ.
- **Ngoài phạm vi:** tư vấn pháp lý cá nhân, dự báo kết quả khiếu nại, tính mức bồi thường chính thức, tự động ra quyết định hành chính, hoặc khẳng định tình trạng pháp lý ngoài corpus đã review.
- **Mức triển khai:** MVP nghiên cứu; production security, SLA và multi-tenancy là hướng mở rộng, không phải tiêu chí hoàn thành của đồ án.

## 4. Dữ liệu, nguồn và quản trị

### 4.1. Thứ bậc nguồn

| Tier | Vai trò | Cách dùng |
|---|---|---|
| Official | Cổng VBPL, Công báo, cơ quan ban hành và cổng thông tin Hà Nội | Nguồn evidence/citation ưu tiên |
| Mirror/index | Nguồn phổ biến lại văn bản | Chỉ discovery hoặc đối chiếu; không dùng citation cuối khi có bản official |
| Manual | Tài liệu do nhóm bổ sung | Chỉ publish sau review, ghi rõ provenance và hạn chế |

Việc tải dữ liệu phải tuân thủ điều khoản sử dụng, `robots.txt`, bản quyền và giới hạn tốc độ. Không mặc định crawl toàn bộ một website hay coi API không công bố là có thể dùng.

### 4.2. Pipeline tái lập

```text
Source registry → tải bản gốc → checksum/snapshot → parse hoặc OCR có QA
→ trích xuất cấu trúc → review metadata → chunk theo Điều/Khoản
→ embed + lexical index → publish corpus version
```

Mỗi artifact lưu URL, thời điểm tải, checksum, parser/OCR version và reviewer. PDF scan có `ocr_quality`; văn bản OCR kém không là evidence độc lập. A document chỉ được publish khi có số hiệu, cơ quan ban hành, nguồn, trạng thái review và dữ liệu hiệu lực tối thiểu.

### 4.3. Mô hình dữ liệu

Mỗi chunk lưu `doc_id`, số hiệu/tên/loại/cơ quan ban hành, URL, source tier, checksum, các mốc hiệu lực, `legal_status`, quan hệ `amends`/`supersedes`, phạm vi/địa bàn, cấu trúc chương–điều–khoản–điểm, `chunk_id`, `corpus_version` và `review_status`.

`legal_status` là metadata được review ở cấp văn bản. Validator đánh giá khả năng áp dụng theo `as_of_date` và quan hệ văn bản; LLM không tự suy diễn “còn hiệu lực”.

## 5. Thiết kế hệ thống

### 5.1. Kiến trúc

```text
UI/API → query normalizer (intent, entities, as_of_date, filters)
       → router ──► one-step hybrid retrieval ──┐
                  └► bounded planner → parallel retrieval ┤
       → reranker → evidence/validity validator → generator
       → citation verifier → answered | insufficient_evidence | clarification_needed

Qdrant: dense BGE-M3 + sparse/BM25 + payload indexes
PostgreSQL/object storage: bản gốc, version, quan hệ, ingest và audit log
```

Qdrant là lựa chọn vector store duy nhất cho MVP. Dense retrieval và lexical/sparse retrieval được hợp nhất bằng reciprocal rank fusion trước reranking. Không gọi là “hybrid” nếu chưa triển khai cả hai tín hiệu.

### 5.2. Agentic layer có kiểm soát

LangGraph biểu diễn state machine, không phải tập agent tự trị. State tối thiểu gồm query chuẩn hoá, sub-query, filters, evidence, `as_of_date`, `corpus_version`, retry count, budget và citation candidates.

- Router chỉ bật planner với câu hỏi multi-hop/đa ý; truy vấn còn lại đi thẳng qua baseline một bước.
- Đặt giới hạn số sub-query, vòng truy xuất, thời gian và token; hết ngân sách phải kết thúc có kiểm soát.
- Validator làm các kiểm tra xác định được: provenance, review status, hiệu lực theo thời gian, phạm vi, trùng lặp và đủ citation. Đánh giá bằng LLM nếu có chỉ là tín hiệu bổ sung.
- Generator bị ràng buộc chỉ tổng hợp evidence được duyệt. Citation verifier hậu kiểm liên kết document–điều/khoản–quote.

### 5.3. Giao diện kết quả

API mục tiêu nhận `query`, `as_of_date`, metadata filters và `top_k` bị giới hạn. Output luôn chứa `status`, citations, `corpus_version`, `as_of_date` và `limitations`; không xuất số `confidence` để gợi ý sai rằng đó là xác suất đúng pháp lý.

## 6. Đánh giá thực nghiệm

### 6.1. Dataset và phương pháp

Tập đánh giá tách train/dev/test, với test khóa trước tối ưu cuối. Nó cần bao phủ câu hỏi đơn giản, multi-hop, xung đột/sửa đổi văn bản, câu hỏi thiếu dữ kiện, ngoài phạm vi và câu hỏi đòi hỏi từ chối. Gold answer/evidence/citation phải được người có năng lực pháp lý review. RAGAS hoặc LLM-as-judge chỉ là bổ trợ và cần audit mẫu thủ công.

### 6.2. Metrics

| Nhóm | Metrics |
|---|---|
| Retrieval | Recall@K, MRR/nDCG, context precision/recall trên gold evidence |
| Citation | citation correctness (document + điều/khoản), citation coverage, claim–evidence entailment |
| Generation | faithfulness, answer relevancy, unsupported-assertion rate |
| Safety | abstention precision/recall, tỷ lệ loại đúng tài liệu không áp dụng |
| Vận hành | p50/p95 latency, lỗi, chi phí/truy vấn, tỷ lệ vượt budget |

Thí nghiệm so sánh BM25, dense RAG một bước, hybrid RAG một bước và Agentic RAG. Tất cả dùng cùng corpus snapshot, gold set, LLM, prompt cơ sở và giới hạn chi phí; báo cáo cả trường hợp Agentic RAG không cải thiện để tránh kết luận do nhiễu.

## 7. Rủi ro và giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| Văn bản sai phiên bản/hết hiệu lực | Official source, versioning, temporal filter, quan hệ sửa đổi/thay thế, review metadata |
| Citation đúng định dạng nhưng không hỗ trợ claim | Claim-level citation, quote/evidence verifier, abstention |
| OCR hoặc parse làm mất cấu trúc điều khoản | Lưu bản gốc, parser QA, `ocr_quality`, review mẫu |
| Agent lặp vô hạn/chi phí cao | State graph, retry/token/time budget, tracing |
| Rò rỉ dữ liệu phiên hỏi đáp | Data minimization, không ghi dữ liệu nhạy cảm vào prompt/log nếu không cần, retention policy |
| Người dùng hiểu là tư vấn | Disclaimer rõ, nêu giới hạn/dữ kiện thiếu, không định lượng bồi thường cá nhân |

## 8. Kế hoạch 8 tuần

| Tuần | Công việc | Đầu ra |
|---|---|---|
| 1 | Source registry, data contract, schema, risk register | Thiết kế được review |
| 2–3 | Ingestion, parsing/OCR QA, metadata review | Corpus pilot versioned |
| 4 | Dense/lexical index và baseline retrieval | Báo cáo retrieval dev |
| 5 | Generation grounded, citation verifier, abstention | API contract + audit log |
| 6 | Bounded LangGraph cho multi-hop | Ablation prototype |
| 7 | Benchmark/test, error analysis | Báo cáo so sánh |
| 8 | UI/API demo, tái lập thí nghiệm, báo cáo | Bản nộp và hướng dẫn chạy |

## 9. Kết quả kỳ vọng

Kết quả của đề tài là corpus pháp lý có provenance và versioning, prototype RAG có citation kiểm chứng được, benchmark đã review, cùng báo cáo ablation chỉ ra điều kiện Agentic RAG hữu ích hoặc không hữu ích. Đề tài không khẳng định độ đúng pháp lý tuyệt đối hay thay thế tư vấn chuyên môn.

## 10. Tài liệu tham khảo và seed corpus

1. Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS.
2. Es, S. et al. (2024). *RAGAS: Automated Evaluation of Retrieval Augmented Generation.* EACL.
3. Yao, S. et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* ICLR.
4. [Luật Đất đai số 31/2024/QH15](https://vanban.chinhphu.vn/?classid=1&docid=211189&orggroupid=1&pageid=27160).
5. [Nghị định 88/2024/NĐ-CP về bồi thường, hỗ trợ, tái định cư](https://vanban.chinhphu.vn/?classid=0&docid=210658&pageid=27160).
6. [Nghị quyết 52/2025/NQ-HĐND về Bảng giá đất Hà Nội, áp dụng từ 01/01/2026](https://congbao.hanoi.gov.vn/Default.aspx?p_attribute=5054&pageid=45002).

Các văn bản pháp lý trong mục này chỉ là seed corpus. Trước khi đưa vào đánh giá hoặc trả lời, pipeline phải xác minh bản gốc, trạng thái và quan hệ hiệu lực tại snapshot tương ứng.

---

*Phiên bản: 2.0 · Cập nhật: 16/09/2026*
