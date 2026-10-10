# Project Status — Production Snapshot

> Cập nhật: 2026-10-10  
> Backend: <https://agentic-rag-legal-qa-api.onrender.com>  
> Frontend: <https://agentic-rag-legal-qa-hanoi.vercel.app>

## Trạng thái đã xác minh

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Frontend Vercel | ✅ Hoạt động | HTTP 200, Next.js build success |
| Backend Render | ✅ Hoạt động | `/health` HTTP 200, Qdrant connected, LLM configured, corpus_size=1956 |
| API contract | ✅ Đã deploy | `/api/v1/query`, `/api/v1/health`, `/api/v1/feedback`, `/api/v1/chat/stream` |
| Qdrant Cloud | ✅ Verified trực tiếp | Alias `legal_chunks` → `legal_chunks_20261010_1`, 1.956 points, green, 1024/Cosine |
| LLM provider | ✅ Configured | Groq `openai/gpt-oss-20b`; key in Render secret |
| Corpus production | ✅ Rebuilt/promoted | `legal_chunks` alias → `legal_chunks_20261010_1`, 1.956 chunks (P0+P1) |
| LangGraph flow | ✅ Đã lắp ráp | Router → planner/clarification/retrieval → grader → synthesis → verify |
| Hybrid Retrieval | ✅ Active | Dense 1024-dim + Sparse BM25 + RRF fusion active in production |
| Embedding | ✅ HF API + Redis | Hugging Face Inference API (GPU) + Redis cache (TTL 30 days) |
| OCR/canonical rebuild | ✅ Đã promote | 5 P0 snapshots chính thức, validation 0 lỗi |
| RAGAS benchmark | ⚠️ Scaffold sẵn, chưa đo | Cần Groq judge/provider secret và chạy evaluation dataset |
| Golden set 50 câu | ✅ Ready | 50 cases defined, evaluator ready |
| Load test P95 | ❌ Chưa đo | Chưa có k6 report |
| Prompt-injection audit | ⚠️ Scaffold sẵn | 13/15 vectors blocked (86.7%); scripts/security_audit.py ready |

## Smoke test production

Một request clarification tới `/api/v1/query` đã trả HTTP 200 và trạng thái `answered`
với citations. Health endpoint trả về full metadata (corpus_version, active_collection, corpus_size).

## Kết luận MVP

### Đã đạt: Validated MVP baseline

- Người dùng có thể mở web UI public.
- Backend public có API và health endpoint đầy đủ metadata.
- Qdrant và LLM được kết nối trên production.
- Luồng Agentic RAG đầy đủ: routing, planner, clarification, retrieval (hybrid dense+sparse), grading, synthesis và citation verification.
- Hybrid retrieval (Dense 1024-dim + Sparse BM25 + RRF) active trong production.
- Embedding qua Hugging Face Inference API (GPU) với Redis cache (TTL 30 ngày).
- Embedding local fallback (sentence-transformers) khi HF API недоступный.

### Còn cần hoàn thiện cho Demo Day

1. Chạy RAGAS evaluation trên golden set 50 câu (cần Groq judge secret).
2. Chạy load test k6 (P95 single-hop ≤ 8s, multi-hop ≤ 15s).
3. Hoàn tất security audit report (13/15 pass).
4. Manual citation audit 50 cases.
5. SUS score survey với pilot users.
