# ADR-0002: Lựa chọn LLM Engine — Google Gemini API (Free Tier qua OpenAI Protocol)

- **Trạng thái**: Superseded by ADR-0006
- **Ngày quyết định**: 2026-10-04
- **Người quyết định**: Vũ Huy Đô (Senior AI Engineer / Tech Lead)
- **Tài liệu liên quan**: [docs/PRD.md](../PRD.md), [docs/Brief.md](../Brief.md), [.env.example](../../.env.example)

---

## 1. Bối cảnh & Vấn đề (Context)
Các node trong Agentic RAG (`router_node`, `planner_node`, `grader_node`, `synthesize_node`, `verify_node`, `clarification_node`) yêu cầu một mô hình ngôn ngữ lớn (LLM):
1. Có khả năng suy luận logic, phân loại intent và trích xuất cấu trúc (JSON / Pydantic structured output) chuẩn xác.
2. Hiểu sâu sắc sắc thái tiếng Việt hành chính - pháp lý.
3. Chi phí vận hành: 0 VNĐ (sử dụng gói Free Tier miễn phí không yêu cầu thẻ tín dụng).
4. Độ trễ thấp (P95 latency ≤ 6s cho câu hỏi Single-hop).
5. Khả năng tích hợp liền mạch với codebase hiện tại (đang sử dụng thư viện `langchain-openai`).

## 2. Quyết định (Decision)
Dự án quyết định chọn **Google Gemini API** với mô hình **`gemini-3.8-flash`** (hoặc `gemini-2.0-flash` / cơ chế grounded deterministic fallback) thông qua giao thức tương thích OpenAI (**OpenAI-compatible endpoint**):
- **Base URL**: `https://generativelanguage.googleapis.com/v1beta/openai/`
- **Mô hình chính**: `gemini-3.8-flash`
- **Nhà cung cấp**: Google AI Studio (Free Tier)
- **Phương thức gọi**: Sử dụng OpenAI client tương thích trỏ `base_url` về Google Gemini endpoint với cơ chế fallback tự động đảm bảo tính liên tục của hệ thống.

## 3. Các phương án đã cân nhắc (Alternatives Considered)

| Tiêu chí | Google Gemini (Được chọn) | OpenAI (GPT-4o-mini) | Groq (Llama-3.3-70B) | Ollama Local |
|---|---|---|---|---|
| **Chi phí** | **0 VNĐ (Free Tier rộng rãi)** | Có phí per-token | 0 VNĐ (Free tier) | 0 VNĐ |
| **Yêu cầu thẻ tín dụng** | **Không** | Có | Không | Không |
| **Tiếng Việt pháp luật** | **Rất tốt** | Tốt | Khá | Trung bình |
| **Context Window** | 1M tokens | 128k tokens | 128k tokens | Phụ thuộc RAM |
| **Tương thích OpenAI SDK** | Có sẵn qua `/v1beta/openai/` | Gốc | Có sẵn | Có sẵn |

## 4. Hệ quả (Consequences)

### Tích cực:
- Chi phí 0 VNĐ cho toàn bộ quá trình phát triển, kiểm thử và demo đồ án.
- Tốc độ phản hồi cực nhanh nhờ kiến trúc Flash của Gemini, đáp ứng chỉ tiêu SLA P95 latency ≤ 8s.
- Khả năng xử lý ngữ cảnh lớn (Long Context) giúp tổng hợp đồng thời nhiều văn bản pháp luật mà không lo tràn context window.

### Hạn chế & Giảm thiểu:
- Giới hạn tần suất gọi API (Rate limits) trên gói Free Tier: 15 RPM (Requests Per Minute).
  *Giảm thiểu:* Tích hợp bộ đệm (Rate limiter) và cơ chế exponential backoff retry trong `src/api/deps.py` và các LangGraph nodes. Hỗ trợ cấu hình chuyển đổi nhanh sang Groq API hoặc Ollama nếu chạm rate limit.
