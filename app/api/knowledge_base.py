from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Body
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from app.schemas import KnowledgeBaseCreate, KnowledgeBaseOut, KnowledgeBaseUpdate
from app.models import KnowledgeBase as KBModel
from app.models.document import Document as DocumentModel
from app.models.document_chunk import DocumentChunk as ChunkModel
from app.models.embedding import Embedding as EmbeddingModel
from app.core.auth import get_current_user_with_role, get_current_user_with_permission, get_current_user
from app.db.database import get_db
import uuid
from sqlalchemy.exc import IntegrityError
from app.services.faiss_manager import get_index_path
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=List[KnowledgeBaseOut])
async def list_knowledge_bases(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KBModel))
    kbs = result.scalars().all()
    return [KnowledgeBaseOut(
        id=str(kb.id),
        name=kb.name,
        description=kb.description,
        ai_provider=kb.ai_provider,
        chunking_strategy=kb.chunking_strategy,
        chunk_size=kb.chunk_size,
        chunk_overlap=kb.chunk_overlap,
        embedding_model=kb.embedding_model
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
    try:
        kb_uuid = uuid.UUID(kb_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Knowledge Base ID format")

    kb = await db.get(KBModel, kb_uuid)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb

@router.put("/{kb_id}", response_model=KnowledgeBaseOut)
async def update_knowledge_base(
    kb_id: str,
    kb_update: KnowledgeBaseUpdate,
    current_admin=Depends(get_current_user_with_role("ROLE_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    try:
        kb_uuid = uuid.UUID(kb_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Knowledge Base ID format")

    db_kb = await db.get(KBModel, kb_uuid)
    if not db_kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    update_data = kb_update.model_dump(exclude_unset=True) # Use model_dump

    for key, value in update_data.items():
        setattr(db_kb, key, value)

    db.add(db_kb)
    try:
        await db.commit()
        await db.refresh(db_kb)
    except IntegrityError:
        await db.rollback()
        # Could be a unique constraint violation (e.g., name)
        raise HTTPException(status_code=400, detail="Update failed, possibly due to conflicting name")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    return db_kb

@router.post("", response_model=KnowledgeBaseOut)
async def create_knowledge_base(kb: KnowledgeBaseCreate, current_admin=Depends(get_current_user_with_role("admin")), db: AsyncSession = Depends(get_db)):
    new_kb = KBModel(
        name=kb.name,
        description=kb.description,
        ai_provider=kb.ai_provider,
        chunking_strategy=kb.chunking_strategy,
        chunk_size=kb.chunk_size,
        chunk_overlap=kb.chunk_overlap,
        embedding_model=kb.embedding_model
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
        ai_provider=new_kb.ai_provider,
        chunking_strategy=new_kb.chunking_strategy,
        chunk_size=new_kb.chunk_size,
        chunk_overlap=new_kb.chunk_overlap,
        embedding_model=new_kb.embedding_model
    )

@router.delete("/{kb_id}", status_code=204) # Use 204 No Content for successful deletion
async def delete_knowledge_base(
    kb_id: str,
    current_admin=Depends(get_current_user_with_role("ROLE_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a Knowledge Base and associated data (if implemented)."""
    try:
        kb_uuid = uuid.UUID(kb_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Knowledge Base ID format")

    db_kb = await db.get(KBModel, kb_uuid)
    if not db_kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    doc_stmt = select(DocumentModel).where(DocumentModel.knowledge_base_id == kb_uuid) # Correct column name
    documents_result = await db.execute(doc_stmt)
    documents = documents_result.scalars().all()
    doc_ids = [doc.id for doc in documents]

    if doc_ids:
        # Find chunk IDs associated with the documents
        chunk_stmt = select(ChunkModel.id).where(ChunkModel.document_id.in_(doc_ids))
        chunks_result = await db.execute(chunk_stmt)
        chunk_ids = chunks_result.scalars().all()

        if chunk_ids:
            # Delete Embeddings related to these Chunks
            embedding_delete_stmt = delete(EmbeddingModel).where(EmbeddingModel.chunk_id.in_(chunk_ids))
            await db.execute(embedding_delete_stmt)
            logger.info(f"Deleted embeddings for chunks in KB {kb_id}")

            # Delete Chunks related to the Documents
            chunk_delete_stmt = delete(ChunkModel).where(ChunkModel.id.in_(chunk_ids))
            await db.execute(chunk_delete_stmt)
            logger.info(f"Deleted chunks for documents in KB {kb_id}")

        # Delete Documents themselves
        doc_delete_stmt = delete(DocumentModel).where(DocumentModel.id.in_(doc_ids))
        await db.execute(doc_delete_stmt)
        logger.info(f"Deleted documents in KB {kb_id}")

    # Delete the Knowledge Base itself
    await db.delete(db_kb)
    logger.info(f"Deleted Knowledge Base DB record {kb_id}")

    # Delete the FAISS index file and chunk map file from the filesystem
    try:
        faiss_index_path = get_index_path(kb_id) # Use centralized function
        chunk_map_path = faiss_index_path + ".chunks.npy" # Path for the chunk map

        # Delete FAISS index
        if os.path.exists(faiss_index_path):
            os.remove(faiss_index_path)
            logger.info(f"Successfully deleted FAISS index file: {faiss_index_path}")
        else:
            logger.warning(f"FAISS index file not found, skipping deletion: {faiss_index_path}")

        # Delete Chunk Map
        if os.path.exists(chunk_map_path):
            os.remove(chunk_map_path)
            logger.info(f"Successfully deleted FAISS chunk map file: {chunk_map_path}")
        else:
            logger.warning(f"FAISS chunk map file not found, skipping deletion: {chunk_map_path}")

    except OSError as e:
        # Log error but don't block the commit if DB deletion was okay
        logger.error(f"Error deleting FAISS file(s) for KB {kb_id}: {e}", exc_info=True)
        # Consider if this error should prevent commit or just be logged

    # Commit the transaction
    await db.commit()

    return None
