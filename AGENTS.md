# Project Instructions: Agentic RAG Legal QA Hanoi

> **Hệ thống hỏi đáp pháp luật đất đai, quy hoạch, thu hồi đất, bồi thường và tái định cư tại Hà Nội**  
> Kiến trúc: **Agentic RAG (LangGraph + FastAPI + Qdrant + BGE-M3 + BM25)**

---

## 1. Domain & Project Overview

Dự án phát triển hệ thống Agentic RAG chuyên sâu tra cứu và giải đáp văn bản quy phạm pháp luật trong lĩnh vực đất đai và quy hoạch trên địa bàn Thành phố Hà Nội.
- **Corpus hạt nhân**:
  - Luật Đất đai số 31/2024/QH15.
  - Nghị định số 88/2024/NĐ-CP (bồi thường, hỗ trợ, tái định cư).
  - Nghị định số 102/2024/NĐ-CP (quy định chi tiết thi hành Luật Đất đai).
  - Quyết định số 61/2024/QĐ-UBND & Nghị quyết số 52/2025/NQ-HĐND TP. Hà Nội (Bảng giá đất và cơ chế bồi thường tại địa phương).
- **Mục tiêu cốt lõi**:
  - Tìm đúng căn cứ pháp lý ở cấp độ **Điều / Khoản / Điểm**.
  - Kiểm soát nghiêm ngặt thời điểm hiệu lực (`as_of_date`) và phạm vi áp dụng (quận/huyện, loại đất).
  - Tuyệt đối không suy diễn, bịa đặt điều luật (Zero Hallucination Tolerance).

---

## 2. Core Architectural & Safety Principles

1. **Evidence-First & Traceable Citations**:
   - Mọi kết luận pháp lý **bắt buộc** phải có trích dẫn (`citations`) rõ ràng: tên văn bản, số hiệu, điều, khoản, điểm, đường dẫn nguồn chính thức (`source_url`) và đoạn trích nguyên văn (`quote`).
   - LLM chỉ đóng vai trò tổng hợp, diễn giải dựa trên bằng chứng đã truy xuất; không coi LLM là nguồn tri thức tiên nghiệm.

2. **Temporal Validity Management**:
   - Mọi truy vấn mặc định gắn với mốc thời gian áp dụng `as_of_date` (mặc định là ngày truy vấn nếu người dùng không chỉ định).
   - Kiểm tra trạng thái hiệu lực của văn bản (`active`, `superseded`, `amended`) tại thời điểm `as_of_date`. Tuyệt đối không dùng văn bản hết hiệu lực để trả lời như văn bản đang áp dụng.

3. **Explicit Abstention (`insufficient_evidence`)**:
   - Khi corpus không có đủ căn cứ pháp lý hoặc bằng chứng truy xuất không đủ độ tin cậy để trả lời toàn vẹn, hệ thống **bắt buộc** trả về `status: "insufficient_evidence"` kèm giải thích rõ phạm vi chưa đủ dữ liệu.
   - Thà từ chối trả lời đúng cách hơn là đưa ra câu trả lời phỏng đoán thiếu cơ sở pháp lý.

4. **Proactive Clarification (`clarification_needed`)**:
   - Khi câu hỏi của người dùng mơ hồ hoặc thiếu các dữ kiện then chốt để áp dụng luật (ví dụ: thiếu quận/huyện cụ thể tại Hà Nội, thiếu loại đất nông nghiệp hay đất ở, thiếu nguồn gốc sử dụng đất), hệ thống chuyển hướng sang `status: "clarification_needed"` và gợi ý các thông tin cần bổ sung.

5. **Legal Disclaimer**:
   - Mọi câu trả lời của hệ thống chỉ mang tính chất tham khảo, hỗ trợ tra cứu thông tin; không thay thế tư vấn pháp lý chính thức của luật sư hay quyết định của cơ quan nhà nước có thẩm quyền.

---

## 3. Technology Stack & Directory Structure

- **Ngôn ngữ & Runtime**: Python 3.11+
- **API Framework**: FastAPI, Pydantic v2, Uvicorn
- **Agent Orchestration**: LangGraph, LangChain Core
- **Vector Store & Retrieval**: Qdrant (dense 1024-dim BGE-M3 + BM25 lexical search)
- **Code Quality**: Ruff (linter & formatter), Pytest (unit, integration, eval)
- **Infrastructure**: Docker, Docker Compose

```text
agentic-rag-legal-qa-hanoi/
├── docs/                     # PRD, Brief, Wireframes, ADR, Architecture specs
├── eval/                     # Evaluation datasets & benchmark scripts
│   ├── datasets/             # Sample & gold standard questions (JSONL)
│   └── scripts/              # run_eval.py and metric calculation
├── src/
│   ├── agent/                # LangGraph state, nodes, graph, and tools
│   ├── api/                  # FastAPI app, routes, dependencies
│   ├── core/                 # App configuration & structured logging
│   └── models/               # Pydantic request/response schemas
├── tests/                    # Unit, integration, and agent flow tests
├── .agents/                  # Antigravity Workspace Customizations
│   └── skills/               # Project-specific workflows (ingest, eval, agent-dev)
├── Makefile                  # Automation shortcuts (dev, lint, test, eval, docker)
└── ruff.toml                 # Linting and formatting rules
```

---

## 4. Coding & Quality Standards

- **Type Hints**: Toàn bộ mã nguồn Python phải sử dụng đầy đủ type annotations (`typing.Optional`, `typing.List`, `typing.Dict`, Pydantic models).
- **Asynchronous Code**: Tất cả I/O, database access (Qdrant), API handlers trong FastAPI phải là `async`/`await`.
- **Formatting & Linting**:
  - Tuân thủ cấu hình trong `ruff.toml` (line-length = 88, target-version = "py311").
  - Luôn chạy `make lint` và `make format` trước khi commit code.
- **Testing**:
  - Viết unit test cho các model schemas, parsing functions và config.
  - Viết integration test cho các API endpoints trong `tests/integration/`.
  - Viết eval test cho luồng phân nhánh LangGraph trong `tests/eval/test_agent_flow.py`.

---

## 5. Development & Git Workflow

- **Branching**:
  - Branch chính cho phát triển là `develop`.
  - Feature branches được tạo từ `develop`: `feat/<feature-name>`, `fix/<bug-name>`.
- **Remote**:
  - Repository SSH: `git@github.com:dovh25/agentic-rag-legal-qa-hanoi.git`.
- **Conventional Commits**:
  - Định dạng: `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `refactor: ...`, `chore: ...`.
- **Available Commands**:
  - `make dev`: Khởi động FastAPI server ở chế độ live-reload (`http://localhost:8000`).
  - `make test`: Chạy toàn bộ test suite với pytest.
  - `make lint` / `make format`: Kiểm tra và tự động định dạng code với Ruff.
  - `make eval`: Chạy benchmark đánh giá pipeline Agentic RAG.
  - `make docker-up` / `make docker-down`: Quản lý dịch vụ Qdrant và API với Docker Compose.
