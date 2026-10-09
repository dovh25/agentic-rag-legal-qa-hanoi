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

1. Dùng collection alias `legal_chunks`; không xóa collection đang active trực tiếp.
2. Cấu hình `QDRANT_URL` và `QDRANT_API_KEY` local trong `.env` (không chia sẻ giá trị).
3. Kiểm tra trước khi index:
   `PYTHONPATH=. python scripts/run_ingest.py --include-p1 --validate-only --report /tmp/corpus.json`.
4. Tạo collection version mới, index, validate rồi promote:
   `PYTHONPATH=. python scripts/run_ingest.py --include-p1 --target-collection legal_chunks_v2 --promote`.
   Lệnh này chỉ promote khi schema, provenance và tính duy nhất của chunk hợp lệ.
5. Kiểm tra `GET <render-url>/api/v1/health`: `qdrant=connected` và `corpus_size > 0`.
6. Chỉ bắt đầu demo sau khi kiểm tra một câu trả lời có citation URL chính thức.

Production demo hiện tại:

- API: <https://agentic-rag-legal-qa-api.onrender.com>
- Web: <https://agentic-rag-legal-qa-hanoi.vercel.app>
- Health đã kiểm tra ngày 2026-10-09: `healthy`, Qdrant `connected`, LLM `configured`,
  `corpus_size=1956` after the 2026-10-09.2 collection promotion.
- Backend must be redeployed with `CORPUS_VERSION=2026-10-09.2`; the Qdrant alias is already
  promoted and the 81-point legacy collection is retained for rollback.
  đã được promote. Xem [project status](../PROJECT_STATUS.md).

Các collection version cũ phải được giữ lại để rollback. Rollback là thao tác promote alias
về version trước, sau khi kiểm tra health và một truy vấn smoke test; không dùng thao tác
delete collection production. Seed/fallback không được promote lên cloud nếu chưa xác minh
nguồn chính thức; `official_mismatch`, `official_unextractable` và `official_unavailable`
cũng bị chặn. Crawler hiện tải attachment PDF chính thức và dùng OCR local cho bản scan,
đồng thời đối chiếu số hiệu văn bản trước khi gắn trạng thái `official_verified`.
`--allow-unverified` chỉ dành cho kiểm tra local.

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
