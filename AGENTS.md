# Project Instructions: Agentic RAG Legal QA Hanoi

> **Hệ thống hỏi đáp pháp luật đất đai, quy hoạch, thu hồi đất, bồi thường và tái định cư tại Thành phố Hà Nội**  
> Kiến trúc: **Agentic RAG (LangGraph + FastAPI + Qdrant + BGE-M3 + BM25)**  
> Bộ tài liệu định hướng chuẩn mực: [docs/PRD.md](docs/PRD.md) · [docs/Brief.md](docs/Brief.md) · [docs/Wireframe_UI_Flow.md](docs/Wireframe_UI_Flow.md)

---

## 1. Domain & Project Overview

Hệ thống Agentic RAG chuyên sâu phục vụ tra cứu, diễn giải và định vị văn bản quy phạm pháp luật trong lĩnh vực đất đai và quy hoạch trên địa bàn Thủ đô Hà Nội, trong bối cảnh thành phố đang triển khai đồng loạt các đại dự án hạ tầng (Vành đai 4, Metro, đô thị ven sông Hồng, điều chỉnh quy hoạch địa giới).

### Corpus Hạt nhân (Corpus Tiers)
- **P0 (Bắt buộc - MVP)**:
  - Luật Đất đai số 31/2024/QH15.
  - Nghị định số 88/2024/NĐ-CP (bồi thường, hỗ trợ, tái định cư).
  - Nghị định số 102/2024/NĐ-CP (quy định chi tiết thi hành Luật Đất đai).
  - Quyết định số 61/2024/QĐ-UBND TP. Hà Nội (quy định cụ thể về bồi thường, hỗ trợ, TĐC tại Hà Nội).
  - Nghị quyết số 52/2025/NQ-HĐND TP. Hà Nội (Bảng giá đất TP. Hà Nội).
- **P1 (Mở rộng)**: Nghị định 71/2024/NĐ-CP (Giá đất), Nghị định 101/2024/NĐ-CP, Thông tư 10/2024/TT-BTNMT.
- **P2 (Chuyên sâu)**: Văn bản giải đáp nghiệp vụ Bộ TN&MT, án lệ tranh chấp đất đai tại Hà Nội.

---

## 2. Core Architectural & Safety Principles

1. **Evidence-First & Traceable Citations**:
   - 100% kết luận pháp lý **bắt buộc** phải có trích dẫn (`citations`) rõ ràng: tên văn bản, số hiệu, điều, khoản, điểm, đường dẫn nguồn chính thức (`source_url` trên Cổng VBPL / Công báo Hà Nội) và đoạn trích nguyên văn (`snippet`/`quote`).
   - LLM chỉ đóng vai trò tổng hợp, diễn giải dựa trên bằng chứng đã được truy xuất và kiểm chứng; không coi LLM là nguồn tri thức tiên nghiệm.

2. **Temporal Validity Management (`as_of_date`)**:
   - Mọi truy vấn gắn chặt với mốc thời gian áp dụng `as_of_date` (mặc định là ngày truy vấn nếu người dùng không chỉ định).
   - Kiểm tra trạng thái hiệu lực của văn bản (`active`, `superseded`, `amended`) tại thời điểm `as_of_date`. Tuyệt đối không dùng văn bản hết hiệu lực để giải đáp như văn bản đang áp dụng.

3. **Explicit Abstention (`insufficient_evidence`)**:
   - Khi corpus không có đủ căn cứ pháp lý hoặc bằng chứng truy xuất không đủ độ tin cậy để trả lời toàn vẹn, hệ thống **bắt buộc** trả về `status: "insufficient_evidence"` kèm khuyến nghị tham vấn cơ quan có thẩm quyền hoặc luật sư.
   - Thà từ chối trả lời đúng cách hơn là đưa ra câu trả lời phỏng đoán thiếu cơ sở pháp lý (Zero Hallucination Tolerance).

4. **Proactive Clarification (`clarification_needed`)**:
   - Khi câu hỏi của người dùng mơ hồ hoặc thiếu các dữ kiện then chốt để áp dụng luật (ví dụ: thiếu quận/huyện cụ thể tại Hà Nội, thiếu loại đất nông nghiệp hay đất ở, thiếu nguồn gốc sử dụng đất), hệ thống chuyển hướng sang `status: "clarification_needed"` kèm câu hỏi gợi ý (`clarification_question`).

5. **Legal Disclaimer**:
   - Mọi câu trả lời của hệ thống chỉ mang tính chất tham khảo, hỗ trợ tra cứu thông tin; không thay thế tư vấn pháp lý chính thức của luật sư hay quyết định của cơ quan nhà nước có thẩm quyền.

---

## 3. Technology Stack & Directory Structure

- **Ngôn ngữ & Runtime**: Python 3.11+
- **LLM Inference Engine**: Google Gemini API (`gemini-3.8-flash` qua OpenAI-compatible protocol - Free Tier)
- **Embedding Model**: `BAAI/bge-m3` (1024-dim dense + BM25 sparse lexical weights - Local/Free)
- **API Framework**: FastAPI, Pydantic v2, Uvicorn
- **Agent Orchestration**: LangGraph 0.2+, LangChain Core
- **Vector Store & Hybrid Retrieval**: Qdrant (collection: `legal_chunks`, HNSW cosine, payload indexes)
- **Data Acquisition**: Automated Crawler từ Cổng VBPL Chính phủ & Công báo Hà Nội
- **Architecture Decisions**: Tài liệu hóa chi tiết tại `docs/adr/` (ADR-0001 đến ADR-0004)
- **Frontend Specification**: React / Next.js theo [docs/Wireframe_UI_Flow.md](docs/Wireframe_UI_Flow.md) (Palette: Deep Navy `#1B4F72`, Accent Orange `#E67E22`)
- **Code Quality & Formatting**: Ruff (line-length = 88, py311), Pytest (unit, integration, eval)
- **Infrastructure**: Docker, Docker Compose

```text
agentic-rag-legal-qa-hanoi/
├── docs/                     # PRD, Brief, Wireframe_UI_Flow, ADR, Architecture specs
├── eval/                     # Evaluation datasets & benchmark scripts
│   ├── datasets/             # Sample & gold standard questions (JSONL)
│   └── scripts/              # run_eval.py and metric calculation
├── src/
│   ├── agent/                # LangGraph state, nodes (router, planner, retrieval, grader, synthesize, verify, clarification)
│   ├── api/                  # FastAPI app, routes (POST /query, GET /health, POST /feedback)
│   ├── core/                 # App configuration & structured logging (Loguru)
│   └── models/               # Pydantic request/response schemas
├── tests/                    # Unit, integration, and agent flow tests
├── .agents/                  # Antigravity Workspace Customizations
│   └── skills/               # Project-specific workflows (ingest, eval, agent-dev)
├── Makefile                  # Automation shortcuts (dev, lint, test, eval, docker)
└── ruff.toml                 # Linting and formatting rules
```

---

## 4. API Specification & System Contracts

Bám sát đặc tả tại **PRD Section 10**:
- **`POST /api/v1/query`**: Nhận `query`, `as_of_date`, `district`, `max_results`, `session_id`. Trả về `answer`, `status` (`answered` | `clarification_needed` | `insufficient_evidence`), `citations`, `reasoning_steps`, `route`, `sub_queries`, `clarification_question`, `processing_time_ms`.
- **`GET /api/v1/health`**: Trả về `status`, `version`, `qdrant`, `llm`, `corpus_size`.
- **`POST /api/v1/feedback`**: Tiếp nhận đánh giá người dùng (`query_id`, `rating`, `comment`).

---

## 5. Lộ trình Triển khai 3 Tuần (Sprint Roadmap)

> **Tổng thời gian: 3 tuần | Hoàn thành MVP: Cuối Tuần 2**

- **Tuần 1: Foundation & Agent Core** (M1):
  - Ingestion pipeline hoàn chỉnh: parse cấu trúc Chương > Điều > Khoản, gắn breadcrumb context.
  - Đánh chỉ mục toàn bộ Corpus P0 vào Qdrant collection `legal_chunks`.
  - Hoàn thiện 4 node lõi LangGraph: `router_node`, `retrieval_node`, `grader_node`, `synthesize_node`.
- **Tuần 2: MVP Complete** (M2 - Go/No-Go Checkpoint):
  - `planner_node` (xử lý truy vấn đa bước Multi-hop), `clarification_node`, bộ lọc `as_of_date`.
  - Lắp ráp đồ thị LangGraph hoàn chỉnh + kết nối FastAPI endpoints.
  - Giao diện Web Chat (Next.js) bám sát [docs/Wireframe_UI_Flow.md](docs/Wireframe_UI_Flow.md).
  - MVP Smoke test trên 20 kịch bản thực tế.
- **Tuần 3: Evaluation & Demo** (M3):
  - Benchmark RAGAS trên Golden set 50 câu hỏi (Faithfulness ≥ 0.90, Citation Accuracy ≥ 95%).
  - Load test k6 (P95 latency ≤ 8s) & kiểm tra bảo mật prompt injection.
  - Mở rộng Corpus P1, hoàn thiện tài liệu và Demo Day.

---

## 6. Coding & Quality Standards

- **Type Hints**: Toàn bộ mã nguồn Python sử dụng cú pháp Python 3.11 (`X | None`, `list[...]`, `dict[...]`, Pydantic models).
- **Asynchronous Code**: Tất cả I/O, database access (Qdrant), API handlers trong FastAPI phải là `async`/`await`.
- **Formatting & Linting**: Tuân thủ `ruff check` và `ruff format`. Không commit khi còn lỗi linter.
- **Testing**:
  - Unit test cho schemas, parser và config (`tests/unit/`).
  - Integration test cho API endpoints (`tests/integration/`).
  - Flow test cho luồng LangGraph (`tests/eval/`).
  - Chạy toàn bộ với `make test`.

---

## 7. Development & Git Workflow

- **Branching**:
  - Nhánh phát triển chính: `develop`.
  - Feature branches phân nhánh từ `develop`: `feat/<feature-name>`, `fix/<bug-name>`.
- **Remote**: `git@github.com:dovh25/agentic-rag-legal-qa-hanoi.git`.
- **Conventional Commits**: `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `refactor: ...`, `chore: ...`.
- **Lệnh thực thi**:
  - `make dev`: Khởi động FastAPI server ở chế độ live-reload.
  - `make test`: Chạy toàn bộ test suite.
  - `make lint` / `make format`: Kiểm tra và tự động format code.
  - `make eval`: Chạy benchmark đánh giá pipeline Agentic RAG.
  - `make docker-up` / `make docker-down`: Quản lý Docker services (API + Qdrant).
