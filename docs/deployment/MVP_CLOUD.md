# Cloud deployment runbook — MVP

## Topology

MVP dùng ba dịch vụ có free tier:

```text
Vercel (Next.js) ──HTTPS──> Render Web Service (FastAPI Docker)
                                  │
                                  ├──> Qdrant Cloud Free (legal_chunks)
                                  └──> Google Gemini API / provider tương thích
```

Render là runtime stateless. Không dùng filesystem hoặc volume ephemeral của Render để
lưu corpus/vector index; Qdrant Cloud là nguồn dữ liệu bền vững. Local Docker Compose vẫn
là fallback khi free tier ngủ hoặc hết quota.

## Secrets và biến môi trường

Có thể dùng `.env` local trong quá trình phát triển, nhưng không in giá trị key vào log,
không commit `.env`, và không chép `.env.example` thành secret trong image. Trên Render
nhập trực tiếp các biến sau vào Environment; trên Vercel chỉ nhập biến có tiền tố
`NEXT_PUBLIC_`.

### Render API

| Variable | Mục đích |
|---|---|
| `OPENAI_API_KEY` | Gemini/OpenAI-compatible provider key |
| `OPENAI_BASE_URL` | Base URL provider |
| `MODEL_NAME` | Model inference |
| `QDRANT_URL` | HTTPS endpoint của Qdrant Cloud |
| `QDRANT_API_KEY` | Qdrant key, chỉ cấp quyền cần thiết |
| `ALLOWED_ORIGINS` | Domain Vercel production, ngăn CORS wildcard |
| `API_KEY` | API key tùy chọn cho consumer/API |
| `DEBUG=false` | Tắt debug trong production |

### Vercel web

| Variable | Mục đích |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | URL Render API, không có dấu `/` cuối |

## Bootstrap Qdrant Cloud

1. Tạo collection `legal_chunks` với cosine distance và dimension 1024.
2. Cấu hình `QDRANT_URL` và `QDRANT_API_KEY` local trong `.env` (không chia sẻ giá trị).
3. Chạy `python scripts/run_ingest.py` từ môi trường có quyền ghi collection.
4. Kiểm tra `GET <render-url>/api/v1/health`: `qdrant=connected` và `corpus_size > 0`.
5. Chỉ bắt đầu demo sau khi kiểm tra một câu trả lời có citation URL chính thức.

Script ingestion có thể chạy lại nhờ point ID deterministic; vẫn phải kiểm tra count,
ngày hiệu lực và metadata sau mỗi lần cập nhật corpus.

## Deploy và smoke test

1. Push branch đã test lên GitHub.
2. Tạo Render Web Service từ `render.yaml`, chọn Docker và cấu hình secrets.
3. Deploy frontend `web/` trên Vercel với `NEXT_PUBLIC_API_BASE_URL`.
4. Kiểm tra:
   - `GET /health` trả HTTP 200 (liveness).
   - `GET /api/v1/health` báo trạng thái Qdrant/LLM và corpus count.
   - single-hop, multi-hop, clarification và insufficient-evidence.
   - CORS chỉ cho domain Vercel; request thiếu API key bị từ chối nếu `API_KEY` bật.
5. Ghi lại public URLs trong kênh demo, không ghi secret.

## Free-tier caveats và rollback

- Render free tier có thể cold start/sleep; đo latency lần đầu riêng với steady-state.
- Qdrant Cloud Free có giới hạn dung lượng, request và retention; theo dõi quota trước khi
  mở rộng P1.
- Gemini/provider có RPM/quota; giữ giới hạn request, timeout và deterministic fallback.
- Khi deploy lỗi, rollback Render về image/commit trước; frontend Vercel có thể promote
  deployment trước. Nếu cloud unavailable, chạy `make docker-up` và trỏ frontend về
  `http://localhost:8000`.
