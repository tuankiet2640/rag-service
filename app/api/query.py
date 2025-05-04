from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import QueryResponse
from app.models import KnowledgeBase as KBModel
from app.models.query_log import QueryLog 
from app.schemas.query_log import QueryFeedbackCreate, QueryFeedbackOut 
from app.core.auth import get_current_user_with_role, get_current_user_with_permission, get_current_user 
from app.db.database import get_db
from app.services.rag import get_rag_service
import uuid

router = APIRouter()

@router.post("", response_model=QueryResponse, summary="Query knowledge base (generic)", response_description="LLM answer and context")
async def query_knowledge_base(
    knowledge_base_id: str = Body(..., embed=True, description="Knowledge base UUID"),
    query: str = Body(..., embed=True, description="User query"),
    top_k: int = Body(3, embed=True, description="Number of relevant chunks to use for context"),
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Query any knowledge base using RAGService. Returns an LLM-generated answer and the supporting context.
    Also logs the query details, response, and token usage.
    """
    try:
        kb = await db.get(KBModel, uuid.UUID(knowledge_base_id))
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        rag_service = get_rag_service(db)
        response = await rag_service.query(kb, query, top_k=top_k)

        # Include log_id in the response
        return QueryResponse(answer=response["answer"], context=response["context"], log_id=response["log_id"])
    except Exception as e:
        import traceback
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/feedback", response_model=QueryFeedbackOut, summary="Submit feedback for a query", response_description="Feedback submission confirmation")
async def submit_query_feedback(
    feedback: QueryFeedbackCreate,
    current_user=Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Submits feedback (rating and optional comment) for a specific query log entry identified by its UUID.
    """
    log_entry = await db.get(QueryLog, feedback.log_id)
    if not log_entry:
        raise HTTPException(status_code=404, detail=f"Query log entry with ID {feedback.log_id} not found.")

    if feedback.rating not in [-1, 0, 1]:
         raise HTTPException(status_code=400, detail="Invalid rating value. Must be -1, 0, or 1.")

    log_entry.feedback_rating = feedback.rating
    log_entry.feedback_comment = feedback.comment

    try:
        await db.commit()
        await db.refresh(log_entry)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")

    return QueryFeedbackOut(
        log_id=log_entry.id,
        rating=log_entry.feedback_rating,
        comment=log_entry.feedback_comment
    )
