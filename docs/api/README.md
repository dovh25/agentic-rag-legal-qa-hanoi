# API Documentation — Agentic RAG Legal QA Hà Nội

> Tài liệu đặc tả kỹ thuật và hợp đồng API (API Contracts) cho hệ thống Hỏi đáp Pháp luật Đất đai & Quy hoạch TP. Hà Nội.  
> Framework: **FastAPI** | Data Validation: **Pydantic v2** | Runtime: **Uvicorn**

Khi `API_KEY` được cấu hình, gửi `X-API-Key` cho các endpoint query và feedback. Môi trường `ENVIRONMENT=production` từ chối phục vụ các endpoint này nếu chưa cấu hình key. Query/feedback bị giới hạn mặc định 30 request mỗi 60 giây trên mỗi IP. Health response báo riêng tình trạng embedding, và chỉ trả `healthy` khi corpus khác rỗng, Qdrant dimension tương thích, LLM và embedding đã cấu hình, cùng API key ở production. Xem [deployment security runbook](../ops/deployment-security.md).

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

- `query` (*string, bắt buộc*): Câu hỏi pháp lý của người dùng (3–500 ký tự).
- `as_of_date` (*string, tùy chọn*): Mốc thời gian áp dụng luật theo định dạng ngày ISO `YYYY-MM-DD`; ngày không hợp lệ trả `422` (mặc định là ngày hiện tại).
- `district` (*string, tùy chọn*): Địa bàn quận/huyện tại Hà Nội để lọc chính sách địa phương.
- `max_results` (*integer, tùy chọn, mặc định 5, giới hạn 1–20*): Số lượng đoạn trích tối đa cần lấy.
- `session_id` (*string, tùy chọn*): ID phiên hội thoại.
- `include_reasoning_steps` (*boolean, tùy chọn, mặc định true*): Có trả về các bước suy luận của Agent hay không.
- Header `X-API-Key` (*khi cấu hình*): API key lấy từ secret manager; không gửi key từ mã frontend. Giao diện web chuyển tiếp yêu cầu qua Next.js server route.

Lỗi xác thực trả `401`, cấu hình production thiếu API key trả `503`, và vượt rate limit trả `429` cùng `Retry-After`.

#### Response: Trạng thái `insufficient_evidence` (200 OK)
```json
{
  "query": "Khi bị thu hồi đất tại Đông Anh, tôi được bồi thường theo bảng giá nào?",
  "status": "insufficient_evidence",
  "answer": "Chưa tìm thấy đủ căn cứ trong corpus để xác định chính xác bảng giá áp dụng cho trường hợp này. Vui lòng đối chiếu văn bản chính thức hoặc tham vấn cơ quan có thẩm quyền.",
  "citations": [],
  "reasoning_steps": [
    "Router: single_hop",
    "Retrieval/verification: không đủ bằng chứng có thể kiểm chứng"
  ],
  "route": "single_hop",
  "sub_queries": [],
  "clarification_question": null,
  "processing_time_ms": 850.5,
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
