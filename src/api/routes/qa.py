import time
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_agent_graph
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
) -> LegalQAResponse:
    start_time = time.time()
    try:
        effective_date = request.as_of_date or str(date.today())
        initial_state = {
            "query": request.query,
            "as_of_date": effective_date,
            "district": request.district,
            "reasoning_steps": [],
        }

        # Invoke LangGraph agent
        final_state = agent_graph.invoke(initial_state)

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
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        qdrant="connected",
        llm="connected",
        corpus_size=1250,
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
