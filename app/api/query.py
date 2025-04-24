from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import QueryResponse
from app.models import KnowledgeBase as KBModel
from app.core.auth import get_current_user_with_role, get_current_user_with_permission
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
    """
    try:
        kb = await db.get(KBModel, uuid.UUID(knowledge_base_id))
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        rag_service = get_rag_service(db)
        response = await rag_service.query(kb, query, top_k=top_k)
        return QueryResponse(answer=response["answer"], context=response["context"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
