from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.schemas import DocumentCreate, DocumentOut
from app.models import Document as DocModel, KnowledgeBase as KBModel
from app.core.auth import get_current_user, get_current_user_with_role, get_current_user_with_permission
from app.db.database import get_db
import uuid

router = APIRouter()

@router.get("knowledge_bases/{kb_id}/documents", response_model=List[DocumentOut])
async def list_documents(kb_id: str, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    kb = await db.get(KBModel, uuid.UUID(kb_id))
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    result = await db.execute(select(DocModel).where(DocModel.knowledge_base_id == kb.id))
    docs = result.scalars().all()
    return [DocumentOut(
        id=str(doc.id),
        knowledge_base_id=str(doc.knowledge_base_id),
        title=doc.title,
        source=doc.source,
        status=doc.status,
        created_at=doc.created_at
    ) for doc in docs]

from app.services.rag import get_rag_service
import json

@router.post("knowledge_bases/{kb_id}/documents", response_model=DocumentOut, summary="Add document", response_description="Document metadata")
async def add_document(kb_id: str, doc: DocumentCreate, current_admin=Depends(get_current_user_with_role("admin")), db: AsyncSession = Depends(get_db)):
    """
    Add a document to a knowledge base (admin only). Accepts raw text in 'source'.
    Chunks, embeds, and stores using the new RAGService abstraction (FAISS+provider_manager).
    """
    try:
        kb = await db.get(KBModel, uuid.UUID(kb_id))
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        if not doc.source:
            raise HTTPException(status_code=400, detail="Document 'source' (raw text) required for ingestion")
        rag_service = get_rag_service(db)
        # Simulate file ingestion with in-memory bytes
        ingestion_result = await rag_service.ingest_document(kb, doc.source.encode("utf-8"), filename=doc.title)
        # Fetch the document metadata after ingestion
        new_doc = await db.get(DocModel, uuid.UUID(ingestion_result["document_id"]))
        return DocumentOut(
            id=str(new_doc.id),
            knowledge_base_id=str(new_doc.knowledge_base_id),
            title=new_doc.title,
            source=new_doc.source,
            status=new_doc.status,
            created_at=new_doc.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")

@router.delete("{doc_id}")
async def delete_document(doc_id: str, current_admin=Depends(get_current_user_with_role("admin")), db: AsyncSession = Depends(get_db)):
    doc = await db.get(DocModel, uuid.UUID(doc_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
    return {"detail": "Deleted"}
