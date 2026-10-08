from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.api.deps import get_agent_graph
from src.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_cors_allows_local_frontend_only():
    allowed = client.options(
        "/api/v1/query",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    blocked = client.options(
        "/api/v1/query",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-origin" not in blocked.headers


def test_ask_endpoint():
    payload = {
        "query": "Quy định bồi thường đất nông nghiệp tại Hà Nội",
        "district": "Đông Anh",
        "as_of_date": "2024-08-01",
    }
    response = client.post("/api/v1/qa/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["answered", "insufficient_evidence", "clarification_needed"]


def test_canonical_query_endpoint():
    payload = {
        "query": "Hạn mức giao đất ở tại quận Cầu Giấy theo quy định mới?",
        "district": "Cầu Giấy",
        "as_of_date": "2024-08-01",
        "max_results": 5,
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "processing_time_ms" in data
    assert data["status"] in ["answered", "insufficient_evidence", "clarification_needed"]


def test_feedback_endpoint():
    payload = {
        "query_id": "test-uuid-1234",
        "rating": "positive",
        "comment": "Trích dẫn chính xác",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_query_endpoint_passes_date_and_max_results_to_graph():
    captured = {}

    class FakeGraph:
        async def ainvoke(self, state):
            captured.update(state)
            return {
                "status": "clarification_needed",
                "route": "clarification",
                "clarification_question": "Bạn đang hỏi về loại đất nào?",
                "citations": [],
                "reasoning_steps": [],
            }

    app.dependency_overrides[get_agent_graph] = lambda: FakeGraph()
    try:
        response = client.post(
            "/api/v1/query",
            json={
                "query": "Bồi thường đất tại Đông Anh",
                "as_of_date": "2024-08-01",
                "max_results": 9,
            },
        )
    finally:
        app.dependency_overrides.pop(get_agent_graph, None)

    assert response.status_code == 200
    assert captured["as_of_date"] == "2024-08-01"
    assert captured["max_results"] == 9
    assert response.json()["as_of_date_applied"] == "2024-08-01"


def test_query_endpoint_rejects_invalid_as_of_date():
    response = client.post(
        "/api/v1/query",
        json={"query": "Tra cứu quy định đất đai", "as_of_date": "2024-8-1"},
    )
    assert response.status_code == 422


def test_detailed_health_reports_disconnected_qdrant(monkeypatch):
    monkeypatch.setattr(
        "src.agent.tools.get_retriever",
        lambda: SimpleNamespace(get_client=lambda: None),
    )

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["qdrant"] == "disconnected"
    assert response.json()["corpus_size"] == 0
