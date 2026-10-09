# API Documentation — Agentic RAG Legal QA Hà Nội

> Tài liệu đặc tả kỹ thuật và hợp đồng API (API Contracts) cho hệ thống Hỏi đáp Pháp luật Đất đai & Quy hoạch TP. Hà Nội.  
> Framework: **FastAPI** | Data Validation: **Pydantic v2** | Runtime: **Uvicorn**

Production demo chạy FastAPI trên Render; frontend Vercel gọi qua
`NEXT_PUBLIC_API_BASE_URL`. Health và error behavior trong cloud được kiểm tra theo
[MVP cloud runbook](../deployment/MVP_CLOUD.md).

---

## 1. Tổng quan Endpoints

| Phương thức | Đường dẫn | Mục đích | PRD Reference |
|---|---|---|---|
| `POST` | `/api/v1/query` | Truy vấn pháp lý chính (Canonical endpoint) | Section 10.1 |
| `POST` | `/api/v1/qa/ask` | Endpoint bí danh tương thích ngược (Alias) | Section 10.1 |
| `GET` | `/api/v1/health` | Kiểm tra tình trạng dịch vụ, Qdrant và kích thước corpus | Section 10.2 |
| `POST` | `/api/v1/feedback` | Tiếp nhận phản hồi & đánh giá của người dùng | Section 10.3 |
| `GET` | `/health` | Health check cơ bản cho container / load balancer | N/A |
| `GET` | `/docs` | Swagger UI tương tác trực tiếp | N/A |
| `GET` | `/redoc` | ReDoc API Reference | N/A |

---

## 2. Chi tiết Endpoints

### 2.1 `POST /api/v1/query` (Truy vấn Pháp luật Đất đai)

Gửi câu hỏi bằng ngôn ngữ tự nhiên để Agentic RAG xử lý (định tuyến, tìm kiếm vector lai, chấm điểm độ liên quan, tổng hợp câu trả lời kèm trích dẫn).

#### Request Body (`application/json`)
```json
{
  "query": "Khi bị thu hồi đất tại Đông Anh, tôi được bồi thường theo bảng giá nào?",
  "as_of_date": "2026-02-01",
  "district": "Đông Anh",
  "max_results": 5,
  "session_id": "optional-session-uuid",
  "include_reasoning_steps": true
}
```

- `query` (*string, bắt buộc*): Câu hỏi pháp lý của người dùng (tối đa 500 ký tự).
- `as_of_date` (*string, tùy chọn*): Mốc thời gian áp dụng luật theo định dạng `YYYY-MM-DD` (mặc định là ngày hiện tại).
- `district` (*string, tùy chọn*): Địa bàn quận/huyện tại Hà Nội để lọc chính sách địa phương.
- `max_results` (*integer, tùy chọn, mặc định 5*): Số lượng đoạn trích tối đa cần lấy.
- `session_id` (*string, tùy chọn*): ID phiên hội thoại.
- `include_reasoning_steps` (*boolean, tùy chọn, mặc định true*): Có trả về các bước suy luận của Agent hay không.

#### Response: Trạng thái `answered` (200 OK)
```json
{
  "query": "Khi bị thu hồi đất tại Đông Anh, tôi được bồi thường theo bảng giá nào?",
  "status": "answered",
  "answer": "Theo Điều 94 Luật Đất đai số 31/2024/QH15 và Quyết định số 61/2024/QĐ-UBND của UBND TP. Hà Nội, giá đất bồi thường khi Nhà nước thu hồi đất là giá đất cụ thể do UBND cấp có thẩm quyền phê duyệt tại thời điểm quyết định thu hồi đất...",
  "citations": [
    {
      "document_title": "Luật Đất đai số 31/2024/QH15",
      "document_number": "31/2024/QH15",
      "article_ref": "Điều 94",
      "effective_date": "2024-08-01",
      "expiry_date": null,
      "source_url": "https://vanban.chinhphu.vn/?classid=1&docid=211189",
      "relevance_score": 0.95,
      "excerpt": "Bồi thường về đất khi Nhà nước thu hồi đất ở..."
    },
    {
      "document_title": "Quyết định số 61/2024/QĐ-UBND của UBND TP. Hà Nội",
      "document_number": "61/2024/QĐ-UBND",
      "article_ref": "Điều 7",
      "effective_date": "2024-10-07",
      "expiry_date": null,
      "source_url": "https://congbao.hanoi.gov.vn/",
      "relevance_score": 0.92,
      "excerpt": "Quy định cụ thể một số nội dung về bồi thường, hỗ trợ, tái định cư khi Nhà nước thu hồi đất trên địa bàn thành phố Hà Nội..."
    }
  ],
  "reasoning_steps": [
    "Router: Phân loại câu hỏi dạng Single-hop",
    "Retriever: Tìm kiếm trên Qdrant collection legal_chunks với hybrid BGE-M3 + BM25",
    "Grader: Đánh giá độ liên quan pháp lý, giữ lại 4/5 chunks phù hợp",
    "Synthesizer: Tổng hợp căn cứ pháp lý từ văn bản quy phạm pháp luật",
    "Verifier: Kiểm tra 100% trích dẫn nguồn Cổng VBPL & Công báo Hà Nội"
  ],
  "route": "single_hop",
  "sub_queries": [],
  "clarification_question": null,
  "processing_time_ms": 2850.5,
  "as_of_date_applied": "2026-02-01",
  "metadata": {
    "as_of_date": "2026-02-01",
    "district": "Đông Anh",
    "route_taken": "single_hop"
  }
}
```

#### Response: Trạng thái `clarification_needed` (200 OK)
```json
{
  "query": "Bồi thường đất bao nhiêu?",
  "status": "clarification_needed",
  "answer": null,
  "citations": [],
  "reasoning_steps": [
    "Router: Nhận diện câu hỏi thiếu dữ kiện loại đất và quận/huyện",
    "Clarification: Đưa ra câu hỏi làm rõ có định hướng"
  ],
  "route": "clarification",
  "sub_queries": [],
  "clarification_question": "Để có thể giải đáp chính xác căn cứ bồi thường, bạn vui lòng cho biết: Bạn đang hỏi về loại đất nào (đất ở hay đất nông nghiệp) và tại quận/huyện cụ thể nào trên địa bàn TP. Hà Nội?",
  "processing_time_ms": 110.2,
  "as_of_date_applied": "2026-10-04",
  "metadata": {
    "route_taken": "clarification"
  }
}
```

#### Response: Trạng thái `insufficient_evidence` (200 OK)
```json
{
  "query": "Thủ tục xin visa đi Mỹ diện du học cần những giấy tờ gì?",
  "status": "insufficient_evidence",
  "answer": "Hệ thống không tìm thấy đủ căn cứ pháp lý trong cơ sở dữ liệu chuyên ngành đất đai, quy hoạch và bồi thường tái định cư tại TP. Hà Nội để giải đáp câu hỏi này. Khuyến nghị bạn tra cứu tại cổng dịch vụ công của cơ quan có thẩm quyền hoặc tham vấn chuyên gia pháp lý.",
  "citations": [],
  "reasoning_steps": [
    "Router: Phân tích intent ngoài phạm vi pháp luật đất đai",
    "Grader: Chặn truy vấn ngoài phạm vi (Zero Hallucination Tolerance)"
  ],
  "route": "single_hop",
  "sub_queries": [],
  "clarification_question": null,
  "processing_time_ms": 320.0,
  "as_of_date_applied": "2026-10-04",
  "metadata": {
    "route_taken": "single_hop"
  }
}
```

---

### 2.2 `GET /api/v1/health` (Kiểm tra Sức khỏe Hệ thống & Corpus)

Kiểm tra trạng thái kết nối với Qdrant Vector Cloud và mô hình suy luận LLM (Gemini), đồng thời báo cáo số lượng chunks văn bản pháp lý đang có trong hệ thống.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "qdrant": "connected",
  "llm": "connected",
  "corpus_size": 81
}
```

---

### 2.3 `POST /api/v1/feedback` (Gửi Đánh giá Người dùng)

Tiếp nhận đánh giá hài lòng từ giao diện người dùng phục vụ đánh giá chất lượng và cải tiến liên tục.

#### Request Body (`application/json`)
```json
{
  "query_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "rating": "positive",
  "comment": "Trích dẫn chính xác Điều 94 Luật Đất đai 2024, rất rõ ràng."
}
```

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Feedback recorded successfully"
}
```

---

## 3. Mã Lỗi Chuẩn (Error Codes)

| HTTP Status | Chi tiết | Mô tả |
|---|---|---|
| `422 Unprocessable Entity` | Pydantic ValidationError | Dữ liệu đầu vào không đúng định dạng schema |
| `500 Internal Server Error` | `Internal agent error: <message>` | Lỗi nội bộ trong quá trình điều phối StateGraph |
| `429 Too Many Requests` | Rate limit exceeded | Chạm hạn mức gọi API trên tầng Gateway hoặc Free Tier |
