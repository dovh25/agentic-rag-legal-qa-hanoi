import asyncio
import time
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

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
        effective_date = (request.as_of_date or date.today()).isoformat()
        initial_state = {
            "query": request.query,
            "as_of_date": effective_date,
            "district": request.district,
            "max_results": request.max_results,
            "reasoning_steps": [],
        }

        # Invoke LangGraph agent
        final_state = await agent_graph.ainvoke(initial_state)

        citations: list[LegalCitation] = []
        for c in final_state.get("citations", []):
            try:
                citations.append(LegalCitation(**c))
            except ValidationError as parse_err:
                logger.error(f"Invalid citation returned by agent: {parse_err}")
                final_state["status"] = ResponseStatus.INSUFFICIENT_EVIDENCE
                final_state["answer"] = (
                    "Không đủ bằng chứng pháp lý có thể kiểm chứng để khẳng định câu trả lời."
                )
                citations = []
                break

        if final_state.get("status") == ResponseStatus.ANSWERED and not citations:
            final_state["status"] = ResponseStatus.INSUFFICIENT_EVIDENCE
            final_state["answer"] = (
                "Không đủ bằng chứng pháp lý có thể kiểm chứng để khẳng định câu trả lời."
            )

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
    qdrant_status = "disconnected"
    corpus_size = 0
    settings = get_settings()
    try:
        from src.agent.tools import get_retriever

        retriever = get_retriever()
        client = await asyncio.to_thread(retriever.get_client)
        if client:
            count_res = await asyncio.to_thread(
                client.count, collection_name=retriever.settings.QDRANT_COLLECTION
            )
            corpus_size = count_res.count
            qdrant_status = "connected"
    except Exception as e:
        logger.warning(f"Health check Qdrant status check failed: {e}")

    llm_status = "configured" if settings.OPENAI_API_KEY else "not_configured"
    system_status = "healthy" if qdrant_status == "connected" else "degraded"

    return HealthResponse(
        status=system_status,
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
