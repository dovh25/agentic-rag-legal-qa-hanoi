from fastapi import APIRouter, Depends, HTTPException, status
from src.api.deps import get_agent_graph
from src.core.logging import logger
from src.models.schemas import LegalCitation, LegalQARequest, LegalQAResponse, ResponseStatus

router = APIRouter(prefix="/qa", tags=["Legal QA"])


@router.post(
    "/ask",
    response_model=LegalQAResponse,
    summary="Ask a legal question",
    description="Processes legal question on Hanoi land use, planning, compensation, and resettlement using Agentic RAG.",
)
async def ask_legal_question(
    request: LegalQARequest,
    agent_graph=Depends(get_agent_graph),
) -> LegalQAResponse:
    try:
        initial_state = {
            "query": request.query,
            "as_of_date": request.as_of_date,
            "district": request.district,
            "reasoning_steps": [],
        }

        # Invoke LangGraph agent
        final_state = agent_graph.invoke(initial_state)

        citations = [
            LegalCitation(**c) for c in final_state.get("citations", [])
        ]

        return LegalQAResponse(
            query=request.query,
            status=ResponseStatus(final_state.get("status", ResponseStatus.ANSWERED)),
            answer=final_state.get("answer", ""),
            citations=citations,
            reasoning_steps=final_state.get("reasoning_steps", []) if request.include_reasoning_steps else [],
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
