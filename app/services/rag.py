import uuid
from typing import Any, List
from app.models.db_models import KnowledgeBase as KBModel, Document as DocModel, DocumentChunk, Embedding
from app.services.provider_manager import ProviderManager
from app.services.faiss_manager import FAISSManager, get_index_path
import numpy as np
import json
import os
import io
from PyPDF2 import PdfReader
from docx import Document as DocxDocument

# Provider and vector search abstraction
provider_manager = ProviderManager()
faiss_dim = int(os.getenv("EMBEDDING_DIM", "1536"))  # Default for OpenAI ada-002

class RAGService:
    def __init__(self, db):
        self.db = db

    def extract_text_from_pdf(self, pdf_bytes):
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            return ""

    def extract_text_from_docx(self, docx_bytes):
        try:
            doc = DocxDocument(io.BytesIO(docx_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            return ""

    async def ingest_document(self, kb: KBModel, content: bytes, filename: str = None) -> dict:
        # Determine file type and extract text accordingly
        text = ""
        if filename:
            fname = filename.lower()
            if fname.endswith('.pdf'):
                text = self.extract_text_from_pdf(content)
            elif fname.endswith('.docx'):
                text = self.extract_text_from_docx(content)
            else:
                try:
                    text = content.decode(errors="ignore")
                except Exception:
                    text = ""
        else:
            try:
                text = content.decode(errors="ignore")
            except Exception:
                text = ""

        new_doc = DocModel(
            knowledge_base_id=kb.id,
            title=filename or "Untitled",
            source=text,
            status="processing"
        )
        self.db.add(new_doc)
        await self.db.commit()
        await self.db.refresh(new_doc)

        def simple_chunk(text, size=512, overlap=64):
            words = text.split()
            chunks = []
            i = 0
            while i < len(words):
                chunk = words[i:i+size]
                chunks.append(' '.join(chunk))
                i += size - overlap
            return chunks

        chunks = [c for c in simple_chunk(text) if c.strip()]
        provider_conf = provider_manager.get_provider_config(kb.ai_provider or "openai")
        if not provider_conf:
            raise Exception("AI provider not found or not enabled")
        # Only OpenAI for now; can extend
        from app.core.providers.openai_provider import OpenAIProviderClient
        embed_client = OpenAIProviderClient(api_key=provider_conf["api_key"], embedding_model=provider_conf.get("embedding_model", "text-embedding-ada-002"))
        vectors = await embed_client.embed_texts(chunks)

        chunk_objs = []
        chunk_ids = []
        np_vectors = []
        for idx, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
            chunk_obj = DocumentChunk(
                document_id=new_doc.id,
                chunk_index=idx,
                text=chunk_text
            )
            self.db.add(chunk_obj)
            await self.db.flush()  # Get chunk_obj.id
            emb_obj = Embedding(
                chunk_id=chunk_obj.id,
                provider=kb.ai_provider or "openai",
                model=embed_client.embedding_model,
                version=None,
                vector=json.dumps(vector)
            )
            self.db.add(emb_obj)
            chunk_objs.append(chunk_obj)
            chunk_ids.append(str(chunk_obj.id))
            np_vectors.append(np.array(vector, dtype=np.float32))
        # Add to FAISS (per-KB index)
        if np_vectors:
            kb_index_path = get_index_path(str(kb.name))
            kb_faiss_manager = FAISSManager(dim=faiss_dim, index_path=kb_index_path)
            kb_faiss_manager.add_embeddings(np_vectors, chunk_ids)
        new_doc.status = "ready"
        await self.db.commit()
        await self.db.refresh(new_doc)
        return {
            "document_id": str(new_doc.id),
            "chunks": len(chunk_objs),
            "status": new_doc.status
        }

    async def query(self, kb: KBModel, query: str, top_k: int = 3) -> Any:
        provider_conf = provider_manager.get_provider_config(kb.ai_provider or "openai")
        if not provider_conf:
            raise Exception("AI provider not found or not enabled")
        from app.core.providers.openai_provider import OpenAIProviderClient
        embed_client = OpenAIProviderClient(api_key=provider_conf["api_key"])
        query_vector = await embed_client.embed_texts([query])
        # Use FAISS to find top-k similar chunks (per-KB index)
        kb_index_path = get_index_path(str(kb.name))
        kb_faiss_manager = FAISSManager(dim=faiss_dim, index_path=kb_index_path)
        results = kb_faiss_manager.search(np.array(query_vector[0]), top_k=top_k)
        if not results:
            return {"answer": "No data found in knowledge base."}
        # Retrieve chunk texts from DB
        chunk_ids = [r[0] for r in results]
        from sqlalchemy.future import select
        from app.models.db_models import DocumentChunk
        db_chunks = (await self.db.execute(select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids)))).scalars().all()
        context = "\n".join(chunk.text for chunk in db_chunks)
        prompt = (
            f"Use the following context to answer the question.\n"
            f"Context:\n{context}\n"
            f"Question: {query}\n"
            "Answer:"
        )
        answer = await embed_client.complete(prompt)
        return {"answer": answer, "context": context}

def get_rag_service(db):
    return RAGService(db)
