# Runbook: Agentic RAG Legal QA Hanoi

> Hướng dẫn vận hành, bảo trì và mở rộng hệ thống hỏi đáp pháp luật đất đai Hà Nội.

---

## 1. Kiến trúc Tổng quan

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Next.js Chatbot (IndexedDB History, SSE Streaming)      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Router Node  │ │ Planner Node │ │ Retriever    │            │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              LANGGRAPH AGENT STATE MACHINE              │     │
│  │ Router → Planner/Retriever → Grader → Synthesize → Verify │     │
│  └────────────────────────────────────────────────────────┘     │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌───────────┐        ┌─────────────┐      ┌───────────┐       │
│  │  GROQ     │        │   QDRANT    │      │  REDIS    │       │
│  │  LLM      │        │  VECTOR DB  │      │  CACHE    │       │
│  └───────────┘        └─────────────┘      └───────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Cấu hình Môi trường (.env)

```bash
# Application
APP_NAME="Agentic RAG Legal QA Hanoi"
DEBUG=false
API_V1_STR="/api/v1"
HOST="0.0.0.0"
PORT=8000
LOG_LEVEL="INFO"

# LLM (Groq - Free Tier)
LLM_PROVIDER="groq"
OPENAI_API_KEY="gsk_your_groq_key"
OPENAI_BASE_URL="https://api.groq.com/openai/v1"
MODEL_NAME="llama-3.3-70b-versatile"

# Embeddings (Hugging Face Inference API - Free GPU)
HUGGINGFACE_API_KEY="hf_your_hf_token"
USE_HF_EMBEDDING_API=true
HF_EMBEDDING_MODEL="BAAI/bge-m3"
HF_EMBEDDING_URL="https://api-inference.huggingface.co/models/BAAI/bge-m3"
HF_EMBEDDING_BATCH_SIZE=32
HF_EMBEDDING_TIMEOUT=30.0

# Redis Cache (Embeddings)
REDIS_URL="redis://localhost:6379/0"
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=0
EMBEDDING_CACHE_TTL=2592000  # 30 days

# Qdrant Vector DB
QDRANT_URL="https://your-cluster.qdrant.tech"
QDRANT_API_KEY="your_qdrant_key"
QDRANT_COLLECTION="legal_chunks"
QDRANT_ACTIVE_ALIAS="legal_chunks"
CORPUS_VERSION="2026-10-10.1"

# Security
API_KEY="your_api_key_for_external_consumers"
ALLOWED_ORIGINS="https://your-frontend.vercel.app"
RATE_LIMIT_PER_MINUTE=30
```

---

## 3. Các lệnh Thường dùng

### Development
```bash
# Cài đặt dependencies
make install

# Chạy dev server (auto-reload)
make dev

# Chạy tests
make test

# Lint & format
make lint
make format

# Chạy evaluation
make eval
```

### Docker
```bash
# Khởi động toàn bộ stack (API + Qdrant + Redis + Prometheus + Grafana)
docker compose -f docker-compose.monitoring.yml up -d

# Chỉ API + Qdrant
docker compose up -d

# Xem logs
docker compose logs -f api

# Dừng
docker compose down
```

### Corpus Management
```bash
# Crawl & index P0 + P1 corpus (local development)
PYTHONPATH=. python scripts/run_ingest.py --include-p1 --corpus-version 2026-10-10.1 --target-collection legal_chunks_v3 --alias legal_chunks --use-existing-manifest --allow-unverified

# Chỉ validate (không index)
PYTHONPATH=. python scripts/run_ingest.py --include-p1 --validate-only --report /tmp/validation.json

# Promote alias thủ công
PYTHONPATH=. python -c "
from src.ingest.indexer import QdrantLegalIndexer
indexer = QdrantLegalIndexer()
indexer.promote_alias('legal_chunks_v3', 'legal_chunks')
"
```

### Deployment (Render + Vercel)
```bash
# 1. Push code lên GitHub
git push origin develop

# 2. Render tự động deploy từ GitHub
# 3. Cấu hình Environment Variables trên Render Dashboard
# 4. Vercel tự động deploy frontend
```

---

## 4. Monitoring & Observability

### Prometheus Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Tổng HTTP requests |
| `http_request_duration_seconds` | Histogram | Latency HTTP endpoints |
| `legal_query_duration_seconds` | Histogram | Latency xử lý query pháp lý |
| `legal_queries_total` | Counter | Tổng query pháp lý theo route/status |

### Grafana Dashboards
- **Legal QA Monitoring**: `/d/legal-qa-monitoring`
- **API Health**: Uptime, latency, error rate
- **Query Performance**: P50/P95 latency theo route (single_hop, multi_hop, chat_stream)
- **Query Distribution**: Phân bố theo status (answered, clarification_needed, insufficient_evidence)

### Health Checks
```bash
# Basic health
curl https://your-api.onrender.com/health

# Detailed health (corpus, Qdrant, LLM)
curl https://your-api.onrender.com/api/v1/health

# Prometheus metrics
curl https://your-api.onrender.com/metrics
```

### Logs
```bash
# Xem logs API
docker compose logs -f api --tail=100

# Xem logs Qdrant
docker compose logs -f qdrant

# Structured logs (JSON) - parse với jq
docker compose logs api | jq '.'
```

---

## 5. Corpus Update Procedure

### 1. Thêm văn bản mới (P1/P2)
1. Thêm entry vào `src/ingest/crawler.py` trong `P1_CORPUS_REGISTRY` hoặc `P2_CORPUS_REGISTRY`
2. Chạy crawl: `PYTHONPATH=. python -m scripts.run_ingest --include-p1 --corpus-version NEW_VERSION --allow-unverified`
2. Verify: `curl API_URL/api/v1/health | jq '.corpus_size'`

### 2. Cập nhật văn bản hiện có
1. Cập nhật `expiry_date` và `replaced_by` trong manifest
3. Re-index: `scripts/run_ingest.py --corpus-version NEW_VERSION --promote`

### 3. Rollback
```bash
# Xem các collection hiện có
curl -H "Authorization: Bearer $QDRANT_KEY" $QDRANT_URL/collections

# Promote alias về version cũ
PYTHONPATH=. python -c "
from src.ingest.indexer import QdrantLegalIndexer
indexer = QdrantLegalIndexer()
indexer.promote_alias('legal_chunks_v2', 'legal_chunks')
"
```

---

## 6. Troubleshooting

### Lỗi thường gặp

| Symptom | Nguyên nhân | Giải pháp |
|---------|-------------|-----------|
| `HF embedding failed: ConnectError` | Không kết nối được HF API | Kiểm tra network, API key; fallback sang mock embeddings |
| `Qdrant 422: indices must be unique` | Sparse vector trùng index | Đã fix bằng `used_indices` set |
| `DuplicateTimeseries` Prometheus | Metrics đăng ký 2 lần | Đã fix bằng shared module `src/api/metrics.py` |
| `Redis connection failed` | Redis không chạy | Khởi động Redis hoặc bỏ qua cache |
| `Groq rate limit` | Vượt 15 RPM | Tăng retry delay, dùng fallback synthesis |
| `SSE timeout` | Render proxy timeout | Tăng timeout, kiểm tra `X-Accel-Buffering: no` |

### Debug Commands
```bash
# Test embedding
python -c "
from src.embedding.hf_client import get_hf_embedding_client
import asyncio
client = get_hf_embedding_client()
print(asyncio.run(client.embed(['test'])))
"

# Test retrieval
python -c "
from src.agent.tools import retrieve_legal_documents
import asyncio
result = asyncio.run(retrieve_legal_documents('hạn mức giao đất', limit=3))
for r in result: print(r['doc_id'], r['article_ref'], r['score'])
"

# Check Qdrant collection
curl -H "Authorization: Bearer $QDRANT_KEY" $QDRANT_URL/collections/legal_chunks
```

---

## 7. Security Checklist

- [ ] API Key được cấu hình trên Render/Vercel (không trong .env)
- [ ] `ALLOWED_ORIGINS` chỉ chứa domain frontend production
- [ ] Rate limiting bật (30 req/min/IP)
- [ ] Input sanitization cho prompt injection
- [ ] CORS headers đúng
- [ ] Secrets không commit vào git
- [ ] HTTPS enforced trên production
- [ ] Qdrant API key có quyền tối thiểu (read/write collection)

---

## 8. Scaling Guidelines

| Component | Current | Scale Up |
|-----------|---------|----------|
| API | 1 replica (Render Free) | Render Paid plan + multiple replicas |
| Qdrant | Cloud Free (1M vectors) | Qdrant Cloud Paid / Self-hosted cluster |
| Redis | Single instance | Redis Cluster / Sentinel |
| Groq LLM | 15 RPM free | Groq Paid / Multiple providers |
| HF Embedding | Free tier | HF Inference Endpoints (dedicated) |

---

## 9. Backup & Disaster Recovery

```bash
# Backup Qdrant snapshot
curl -X POST -H "Authorization: Bearer $QDRANT_KEY" \
  "$QDRANT_URL/collections/legal_chunks/snapshots"

# Restore từ snapshot
curl -X PUT -H "Authorization: Bearer $QDRANT_KEY" \
  "$QDRANT_URL/collections/legal_chunks/snapshots/<snapshot_name>/recover"

# Backup Redis
redis-cli BGSAVE
# Copy dump.rdb to safe location

# Backup manifest
cp data/corpus/raw/manifest.json backups/manifest_$(date +%Y%m%d).json
```

---

## 10. Liên hệ & Escalation

| Issue | Contact | SLA |
|-------|---------|-----|
| Production down | Dev team | 30 min |
| Corpus corrupt | Dev team | 2 hours |
| Security incident | Security team | 1 hour |
| Performance degradation | Dev team | 4 hours |

---

*Runbook version: 1.0 | Cập nhật: 2026-10-10*