import asyncio
import time
from collections import defaultdict
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.api.deps import get_agent_graph
from src.core.config import get_settings
from src.core.logging import logger
from src.models.schemas import (
    FeedbackRequest,
    HealthResponse,
    LegalCitation,
    LegalQARequest,
    LegalQAResponse,
    ResponseStatus,
)

router = APIRouter(tags=["Legal QA"])
_request_timestamps: dict[str, list[float]] = defaultdict(list)


def _check_access(api_key: str | None, client_key: str | None) -> None:
    settings = get_settings()
    if settings.API_KEY and api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    key = client_key or "anonymous"
    now = time.time()
    timestamps = [item for item in _request_timestamps[key] if now - item < 60]
    if len(timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    timestamps.append(now)
    _request_timestamps[key] = timestamps


@router.post(
    "/query",
    response_model=LegalQAResponse,
    summary="Query Hanoi Legal QA (PRD canonical endpoint)",
    description="Processes legal question on Hanoi land use, planning, compensation, and resettlement using Agentic RAG.",
)
@router.post(
    "/qa/ask",
    response_model=LegalQAResponse,
    summary="Ask a legal question (alias)",
    include_in_schema=False,
)
async def ask_legal_question(
    request: LegalQARequest,
    agent_graph=Depends(get_agent_graph),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
    client_key: str | None = Header(default=None, alias="X-Client-Key"),
) -> LegalQAResponse:
    start_time = time.time()
    try:
        _check_access(api_key, client_key)
        effective_date = request.as_of_date or str(date.today())
        initial_state = {
            "query": request.query,
            "as_of_date": effective_date,
            "district": request.district,
            "reasoning_steps": [],
        }

        # Invoke LangGraph agent
        final_state = await asyncio.to_thread(agent_graph.invoke, initial_state)

        citations: list[LegalCitation] = []
        for c in final_state.get("citations", []):
            try:
                citations.append(LegalCitation(**c))
            except Exception as parse_err:
                logger.warning(f"Error parsing citation: {parse_err}")

        processing_time = round((time.time() - start_time) * 1000, 2)
        final_status = ResponseStatus(final_state.get("status", ResponseStatus.ANSWERED))

        return LegalQAResponse(
            query=request.query,
            status=final_status,
            answer=final_state.get("answer"),
            citations=citations,
            reasoning_steps=final_state.get("reasoning_steps", [])
            if request.include_reasoning_steps
            else [],
            route=final_state.get("route"),
            sub_queries=final_state.get("sub_queries", []),
            clarification_question=final_state.get("clarification_question"),
            processing_time_ms=processing_time,
            as_of_date_applied=effective_date,
            metadata={
                "as_of_date": request.as_of_date,
                "district": request.district,
                "route_taken": final_state.get("route"),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal agent error: {str(e)}",
        ) from e


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint conforming to PRD Section 10.2",
)
async def health_check() -> HealthResponse:
    """Returns system status, connected components, and corpus size."""
    settings = get_settings()
    qdrant_status = "disconnected"
    corpus_size = 0
    try:
        from src.agent.tools import get_retriever

        retriever = get_retriever()
        client = retriever.get_client()
        if client:
            count_res = client.count(collection_name=retriever.settings.QDRANT_COLLECTION)
            corpus_size = count_res.count
            qdrant_status = "connected"
    except Exception as e:
        logger.warning(f"Health check Qdrant status check: {e}")

    llm_status = "configured" if settings.OPENAI_API_KEY else "not_configured"
    overall_status = (
        "healthy" if qdrant_status == "connected" and llm_status == "configured" else "degraded"
    )
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        qdrant=qdrant_status,
        llm=llm_status,
        corpus_size=corpus_size,
    )


@router.post(
    "/feedback",
    summary="User feedback conforming to PRD Section 10.3",
    status_code=status.HTTP_200_OK,
)
async def submit_feedback(feedback: FeedbackRequest) -> dict[str, Any]:
    """Record user satisfaction rating and feedback."""
    logger.info(f"Feedback received for query {feedback.query_id}: rating={feedback.rating}")
    return {"status": "success", "message": "Feedback recorded successfully"}
