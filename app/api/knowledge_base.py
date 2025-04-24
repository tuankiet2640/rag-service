from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.schemas import KnowledgeBaseCreate, KnowledgeBaseOut
from app.models import KnowledgeBase as KBModel
from app.core.auth import get_current_user_with_role, get_current_user_with_permission
from app.db.database import get_db
import uuid
from app.services.rag import get_rag_service

router = APIRouter()

@router.get("", response_model=List[KnowledgeBaseOut])
async def list_knowledge_bases(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KBModel))
    kbs = result.scalars().all()
    return [KnowledgeBaseOut(
        id=str(kb.id),
        name=kb.name,
        description=kb.description,
        ai_provider=kb.ai_provider
    ) for kb in kbs]

@router.post("/{kb_id}/ingest", summary="Ingest documents", response_description="Ingestion results")
async def ingest_documents(
    kb_id: str,
    files: List[UploadFile] = File(..., description="Files to ingest"),
    current_admin=Depends(get_current_user_with_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest one or more documents into a knowledge base. Only accessible by admins.
    Returns a list of ingestion results for each file.
    """
    try:
        kb = await db.get(KBModel, uuid.UUID(kb_id))
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        rag_service = get_rag_service(db)
        results = []
        for file in files:
            content = await file.read()
            res = await rag_service.ingest_document(kb, content, filename=file.filename)
            results.append(res)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

from fastapi import Body

@router.post("/{kb_id}/chat", summary="Query knowledge base", response_description="LLM answer and context")
async def chat(
    kb_id: str,
    query: str = Body(..., embed=True, description="User query for the knowledge base"),
    top_k: int = Body(3, embed=True, description="Number of relevant chunks to use for context"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Query the knowledge base using RAG. Returns an LLM-generated answer and the supporting context.
    """
    try:
        kb = await db.get(KBModel, uuid.UUID(kb_id))
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        rag_service = get_rag_service(db)
        response = await rag_service.query(kb, query, top_k=top_k)
        return {"answer": response["answer"], "context": response["context"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.get("health")
async def health():
    return {"status": "ok"}

@router.get("/{kb_id}", response_model=KnowledgeBaseOut)
async def get_knowledge_base(kb_id: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    kb = await db.get(KBModel, uuid.UUID(kb_id))
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return KnowledgeBaseOut(
        id=str(kb.id),
        name=kb.name,
        description=kb.description,
        ai_provider=kb.ai_provider
    )

@router.post("", response_model=KnowledgeBaseOut)
async def create_knowledge_base(kb: KnowledgeBaseCreate, current_admin=Depends(get_current_user_with_role("admin")), db: AsyncSession = Depends(get_db)):
    new_kb = KBModel(
        name=kb.name,
        description=kb.description,
        ai_provider=kb.ai_provider
    )
    db.add(new_kb)
    try:
        await db.commit()
        await db.refresh(new_kb)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Knowledge base already exists")
    return KnowledgeBaseOut(
        id=str(new_kb.id),
        name=new_kb.name,
        description=new_kb.description,
        ai_provider=new_kb.ai_provider
    )

@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str, current_admin=Depends(get_current_user_with_role("admin")), db: AsyncSession = Depends(get_db)):
    kb = await db.get(KBModel, uuid.UUID(kb_id))
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    await db.delete(kb)
    await db.commit()
    return {"detail": "Deleted"}
