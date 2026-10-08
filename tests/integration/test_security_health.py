import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.agent import tools
from src.api.deps import get_agent_graph, get_app_settings
from src.api.main import app
from src.api.routes import qa
from src.api.routes.qa import ask_legal_question, health_check
from src.api.security import enforce_rate_limit
from src.core.config import Settings
from src.ingest.indexer import CollectionDimensionMismatchError
from src.models.schemas import LegalQARequest


def test_health_reports_embedding_dimension_mismatch(monkeypatch):
    class FakeRetriever:
        settings = SimpleNamespace(QDRANT_COLLECTION="legacy")

        def get_client(self):
            return object()

        def validate_collection_dimension(self, client):
            raise CollectionDimensionMismatchError("legacy vectors are incompatible")

    monkeypatch.setattr(tools, "get_retriever", lambda: FakeRetriever())

    health = asyncio.run(health_check())

    assert health.status == "degraded"
    assert health.qdrant == "dimension_mismatch"


def test_health_reports_missing_embedding_configuration(monkeypatch):
    settings = Settings(
        ENVIRONMENT="production",
        API_KEY="configured",
        OPENAI_API_KEY="configured-llm-key",
        EMBEDDING_API_KEY=None,
        OPENAI_BASE_URL="https://example.invalid/v1",
    )
    monkeypatch.setattr(qa, "get_settings", lambda: settings)
    monkeypatch.setattr(
        tools,
        "get_retriever",
        lambda: SimpleNamespace(get_client=lambda: None),
    )

    health = asyncio.run(health_check())

    assert health.status == "degraded"
    assert health.embedding == "not_configured"


def test_query_endpoint_does_not_disclose_internal_exceptions():
    class FailingGraph:
        async def ainvoke(self, state):
            raise RuntimeError("private provider endpoint details")

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            ask_legal_question(
                LegalQARequest(query="Câu hỏi pháp luật đất đai"),
                agent_graph=FailingGraph(),
            )
        )

    assert error.value.status_code == 500
    assert "private provider endpoint details" not in error.value.detail


def test_rate_limit_returns_retry_after_after_configured_budget():
    settings = SimpleNamespace(RATE_LIMIT_REQUESTS=1, RATE_LIMIT_WINDOW_SECONDS=60)
    request = SimpleNamespace(client=SimpleNamespace(host="192.0.2.44"))

    assert asyncio.run(enforce_rate_limit(request, settings)) is None
    with pytest.raises(HTTPException) as error:
        asyncio.run(enforce_rate_limit(request, settings))

    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"]


def test_query_route_enforces_api_key_and_allows_authenticated_client():
    class FakeGraph:
        async def ainvoke(self, state):
            return {
                "status": "clarification_needed",
                "route": "clarification",
                "clarification_question": "Bạn có thể cho biết loại đất không?",
                "citations": [],
                "reasoning_steps": [],
            }

    app.dependency_overrides[get_app_settings] = lambda: Settings(
        API_KEY="integration-test-secret",
        ENVIRONMENT="production",
    )
    app.dependency_overrides[get_agent_graph] = lambda: FakeGraph()
    client = TestClient(app)
    try:
        request_body = {"query": "Câu hỏi pháp luật đất đai"}
        unauthorized = client.post("/api/v1/query", json=request_body)
        authenticated = client.post(
            "/api/v1/query",
            json=request_body,
            headers={"X-API-Key": "integration-test-secret"},
        )
    finally:
        app.dependency_overrides.pop(get_app_settings, None)
        app.dependency_overrides.pop(get_agent_graph, None)

    assert unauthorized.status_code == 401
    assert authenticated.status_code == 200
    assert authenticated.json()["status"] == "clarification_needed"
