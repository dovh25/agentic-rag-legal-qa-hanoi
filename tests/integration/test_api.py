from fastapi.testclient import TestClient

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


def test_ask_endpoint():
    payload = {
        "query": "Quy định bồi thường đất nông nghiệp tại Hà Nội",
        "district": "Đông Anh",
        "as_of_date": "2024-08-01",
    }
    response = client.post("/api/v1/qa/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "status" in data
    assert data["status"] in ["answered", "insufficient_evidence", "clarification_needed"]
