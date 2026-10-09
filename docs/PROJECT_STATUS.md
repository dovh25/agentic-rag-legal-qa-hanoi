# Project Status — Production Snapshot

> Cập nhật: 2026-10-09  
> Backend: <https://agentic-rag-legal-qa-api.onrender.com>  
> Frontend: <https://agentic-rag-legal-qa-hanoi.vercel.app>

## Trạng thái đã xác minh

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Frontend Vercel | ✅ Hoạt động | HTTP 200 |
| Backend Render | ⚠️ Partial smoke only | `/health` HTTP 200, nhưng query và SSE smoke bị timeout; production chưa chạy commit hiện tại đầy đủ |
| API contract | ✅ Đã deploy | `/api/v1/query`, `/api/v1/health`, `/api/v1/feedback` |
| Qdrant Cloud | ✅ Verified trực tiếp | Alias `legal_chunks` → `legal_chunks_20261009_2`, 1.956 points, green, 1024/Cosine |
| LLM provider | ⚠️ Chờ cấu hình secret | Groq `llama-3.3-70b-versatile`; key phải đặt trong Render secret |
| Corpus production | ✅ Rebuilt/promoted | `legal_chunks` alias → `legal_chunks_20261009_2`, 1.956 chunks |
| LangGraph flow | ✅ Đã lắp ráp | Router → planner/clarification/retrieval → grader → synthesis → verify |
| OCR/canonical rebuild | ✅ Đã promote | 5 P0 snapshots chính thức, validation 0 lỗi |
| RAGAS benchmark | ⚠️ Scaffold sẵn, chưa đo | Cần Groq judge/provider secret và chạy evaluation dataset |
| Golden set 50 câu | ❌ Chưa hoàn tất | Chưa có bộ đánh giá chuẩn hóa |
| Load test P95 | ❌ Chưa đo | Chưa có k6 report |
| Prompt-injection audit | ❌ Chưa hoàn tất | Chưa có security report |
| Week 3 evaluation scaffolding | ✅ Đã tạo | Golden set 50 cases, evaluator, k6 scenario, security seed matrix |
| Week 3 local evaluator | ✅ Smoke pass | 50-case schema validated; legacy 5-case runner produced report; RAGAS remains `not_measured` |

## Smoke test production

Một request clarification tới `/api/v1/query` đã trả HTTP 200 và trạng thái `answered`
với citations. Đây xác nhận đường truyền frontend/backend/Qdrant/LLM hoạt động, nhưng
không thay thế kiểm thử chất lượng: câu hỏi “Bồi thường đất bao nhiêu?” vẫn quá mơ hồ
và không nên được dùng làm bằng chứng cho citation accuracy hoặc faithfulness.

Health response production trong lần kiểm tra gần nhất:

```json
{
  "status": "healthy"
}
```

Đây là health contract của deployment hiện tại, chưa chứng minh được alias/corpus/LLM
metadata của commit mới. Production smoke script đạt health và clarification nhưng query
đầy đủ và SSE bị `ReadTimeout`; cần redeploy/wake Render, đặt Groq secret và kiểm tra provider secret trước
khi đo latency hoặc tuyên bố Go.

## Kết luận MVP

### Đã đạt: MVP demo/deployment baseline

- Người dùng có thể mở web UI public.
- Backend public có API và health endpoint.
- Qdrant và LLM được kết nối trên production.
- Luồng Agentic RAG đã có routing, planner, clarification, retrieval, grading,
  synthesis và citation verification.

### Chưa đạt: MVP acceptance đầy đủ

Chưa thể tuyên bố MVP hoàn thiện theo PRD vì:

1. Backend Render chưa thể xác minh sau thay đổi mới; cần `/health` trả `corpus_version=2026-10-09.2`
   và `active_collection=legal_chunks`. Qdrant alias đã được promote độc lập và rollback
   snapshot 81 chunks vẫn được giữ lại.
2. Sparse/BM25/RRF chưa được triển khai đầy đủ; retrieval production hiện chủ yếu dense
   vector và payload filtering.
4. Chưa có bằng chứng cho Faithfulness ≥ 0.90, Citation Accuracy ≥ 95%, P95 ≤ 8 giây,
   security audit và manual hallucination audit.

**Đánh giá:** MVP hiện ở mức **deployed demo / conditional MVP**, chưa phải **validated MVP**.
Go có điều kiện chỉ được xem xét sau khi hoàn tất [acceptance matrix](GO_NO_GO_ACCEPTANCE.md).

## Có đủ điều kiện bắt đầu Tuần 3 không?

**Có thể bắt đầu các workstream kỹ thuật của Tuần 3**, đặc biệt:

- xây dựng golden set;
- dựng RAGAS/evaluation pipeline;
- thiết kế k6 load test;
- security/prompt-injection test;
- hoàn thiện tài liệu và demo checklist.

**Chưa đủ điều kiện Go/No-Go cho Demo Day** cho tới khi hoàn thành:

1. Redeploy backend để health hiển thị `corpus_version=2026-10-09.2`.
2. Chạy smoke suite tối thiểu 20 kịch bản trên production.
3. Có report RAGAS, citation accuracy, latency và security với ngưỡng trong PRD.
4. Xử lý hoặc chấp nhận có kiểm soát các lỗi OCR/chất lượng snapshot.

Tuần 3 vì vậy được mở theo chế độ **evaluation gate**, không được coi là đã pass chỉ vì
hai dịch vụ cloud đang trả HTTP 200. Các artifact khởi đầu được mô tả trong
[GO_NO_GO_ACCEPTANCE.md](GO_NO_GO_ACCEPTANCE.md), nhưng chưa phải evidence acceptance.
## Chatbot redesign status

The browser chatbot shell and stateless SSE contract are implemented in the working tree:
IndexedDB local sessions, transcript/composer, sample prompts and citation cards are present.
The backend contract enforces bounded context and the existing query endpoint remains
compatible. Production redeployment and end-to-end browser smoke testing are still required
before calling the redesign production-ready.
