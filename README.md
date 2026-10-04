<div align="center">

# ⚖️ Agentic RAG Legal QA — Hà Nội

**Hệ thống hỏi đáp pháp luật dựa trên Agentic RAG phục vụ tra cứu quy hoạch, thu hồi đất, bồi thường và tái định cư tại Hà Nội**

> **Đồ án Liên ngành — Khoa Trí tuệ nhân tạo và Khoa học dữ liệu**  
> **Giảng viên hướng dẫn:** ThS. Nguyễn Văn Sơn  
> **Sinh viên thực hiện:** Vũ Huy Đô  

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-blueviolet?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## 📖 Giới thiệu đề tài

Hệ thống hỏi đáp tiếng Việt tăng cường truy xuất (Agentic RAG) chuyên sâu cho văn bản quy phạm pháp luật và cơ chế chính sách về **đất đai, quy hoạch, thu hồi đất, bồi thường và tái định cư** trên địa bàn thành phố Hà Nội.

### Các nguyên tắc cốt lõi:
1. **Evidence-backed & Verifiable Citations**: Mọi câu trả lời đều có trích dẫn điều, khoản, văn bản xác thực kèm provenance URL; không hallucinate căn cứ pháp lý.
2. **Quản trị thời điểm áp dụng (`as_of_date`)**: Tự động đối chiếu văn bản còn hiệu lực hoặc đã được sửa đổi, bổ sung, thay thế tại thời điểm yêu cầu tra cứu.
3. **Agentic Router có kiểm soát**: Câu hỏi đơn giản đi luồng Single-hop retrieval trực tiếp; câu hỏi đa khía cạnh kích hoạt Planner để phân rã câu hỏi (Multi-hop); câu hỏi mơ hồ kích hoạt cơ chế yêu cầu làm rõ (`clarification_needed`).
4. **An toàn & Từ chối trả lời (`insufficient_evidence`)**: Khi không đủ bằng chứng pháp lý trong corpus, hệ thống từ chối đưa ra kết luận suy diễn.

---

## 🗂️ Cấu trúc thư mục dự án

```text
agentic-rag-legal-qa-hanoi/
├── src/
│   ├── agent/           # LangGraph Agent logic
│   │   ├── __init__.py
│   │   ├── graph.py     # State graph definition
│   │   ├── state.py     # State schema
│   │   ├── nodes.py     # Node functions
│   │   └── tools.py     # Agent tools
│   ├── api/             # FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── main.py      # FastAPI app entry point
│   │   ├── routes/      # API route modules
│   │   └── deps.py      # Dependencies injection
│   ├── core/            # Shared config & utilities
│   │   ├── __init__.py
│   │   ├── config.py    # Pydantic settings
│   │   └── logging.py   # Logging setup
│   └── models/          # Data models (Pydantic)
│       ├── __init__.py
│       └── schemas.py   # Request/Response schemas
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── eval/            # Agent evaluation tests
├── docs/
│   ├── architecture/    # Architecture diagrams
│   ├── api/             # API documentation
│   └── adr/             # Architecture Decision Records
├── eval/                # Evaluation datasets & scripts
│   ├── datasets/        # Test questions & expected outputs
│   └── scripts/         # Evaluation runner scripts
├── presentation/        # Demo Day slides & materials
├── .env.example         # Mẫu biến môi trường
├── .gitignore           # Git ignore rules
├── Dockerfile           # Container definition
├── docker-compose.yml   # Multi-container orchestration
├── requirements.txt     # Danh sách dependencies
├── ruff.toml            # Cấu hình linter/formatter
├── Makefile             # Common commands shortcut
└── README.md            # Project documentation
```

---

## 🚀 Hướng dẫn cài đặt & Khởi chạy

### 1. Chuẩn bị môi trường

Yêu cầu: **Python 3.11+**

```bash
# Tạo môi trường ảo
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường

```bash
cp .env.example .env
# Chỉnh sửa .env với API key tương ứng (OpenAI, Qdrant...)
```

### 3. Chạy ứng dụng FastAPI

```bash
# Sử dụng Makefile
make dev

# Hoặc chạy trực tiếp với uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Truy cập tài liệu API tương tác tại:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Kiểm thử & Đánh giá

```bash
# Chạy toàn bộ test suite (Unit, Integration, Eval)
make test

# Chạy kiểm tra và format mã nguồn với Ruff
make lint
make format

# Chạy script đánh giá benchmark
make eval
```

---

## 🐳 Triển khai với Docker & Docker Compose

Khởi động đồng thời cả API Server và Qdrant Vector Database:

```bash
# Khởi động dịch vụ
docker compose up -d

# Dừng dịch vụ
docker compose down
```
