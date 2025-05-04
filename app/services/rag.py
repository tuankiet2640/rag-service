import uuid
from typing import Any, List
from app.models import KnowledgeBase as KBModel, Document as DocModel, DocumentChunk, Embedding
from app.models.query_log import QueryLog
from app.services.provider_manager import ProviderManager
from app.services.faiss_manager import FAISSManager, get_index_path
import numpy as np
import json
import os
import io
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
import time

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

        # Use chunking parameters from the KB object
        def simple_chunk(text, size=1000, overlap=200): 
            words = text.split() 
            chunks = []
            i = 0
            while i < len(words):
                chunk = words[i:i+size]
                chunks.append(' '.join(chunk))
                i += size - overlap
            return chunks

        chunks = [c for c in simple_chunk(text, size=kb.chunk_size, overlap=kb.chunk_overlap) if c.strip()]

        ai_provider_name = kb.ai_provider or "openai" 
        embedding_model_name = kb.embedding_model or "text-embedding-ada-002" 

        provider_conf = provider_manager.get_provider_config(ai_provider_name)
        if not provider_conf:
            new_doc.status = "failed"
            new_doc.status_reason = f"AI provider '{ai_provider_name}' not found or not enabled"
            await self.db.commit()
            raise Exception(new_doc.status_reason)

        if ai_provider_name == "openai":
            from app.core.providers.openai_provider import OpenAIProviderClient
            embed_client = OpenAIProviderClient(
                api_key=provider_conf["api_key"],
                embedding_model=embedding_model_name
            )
        else:
             new_doc.status = "failed"
             new_doc.status_reason = f"AI provider '{ai_provider_name}' not implemented yet for embedding."
             await self.db.commit()
             raise NotImplementedError(new_doc.status_reason)

        try:
            vectors = await embed_client.embed_texts(chunks)
        except Exception as e:
            new_doc.status = "failed"
            new_doc.status_reason = f"Embedding failed: {str(e)}"
            await self.db.commit()
            raise Exception(new_doc.status_reason)


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
            await self.db.flush()  
            emb_obj = Embedding(
                chunk_id=chunk_obj.id,
                provider=ai_provider_name, 
                model=embedding_model_name, 
                version=None, 
                vector=json.dumps(vector)
            )
            self.db.add(emb_obj)
            chunk_objs.append(chunk_obj)
            chunk_ids.append(str(chunk_obj.id))
            np_vectors.append(np.array(vector, dtype=np.float32))

        if np_vectors:
            current_faiss_dim = faiss_dim 
            kb_index_path = get_index_path(str(kb.id)) 
            kb_faiss_manager = FAISSManager(dim=current_faiss_dim, index_path=kb_index_path)
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
        start_time = time.time()

        ai_provider_name = kb.ai_provider or "openai"
        embedding_model_name = kb.embedding_model or "text-embedding-ada-002"
        provider_conf = provider_manager.get_provider_config(ai_provider_name)
        if not provider_conf:
            raise Exception(f"AI provider '{ai_provider_name}' not found or not enabled")

        if ai_provider_name == "openai":
            from app.core.providers.openai_provider import OpenAIProviderClient
            embed_client = OpenAIProviderClient(
                api_key=provider_conf["api_key"],
                embedding_model=embedding_model_name
            )
            completion_model_name = provider_conf.get("completion_model", "gpt-3.5-turbo")
        else:
             raise NotImplementedError(f"AI provider '{ai_provider_name}' not implemented yet for query.")

        query_vector = await embed_client.embed_texts([query])

        current_faiss_dim = faiss_dim
        kb_index_path = get_index_path(str(kb.id))
        kb_faiss_manager = FAISSManager(dim=current_faiss_dim, index_path=kb_index_path)

        results = kb_faiss_manager.search(np.array(query_vector[0]), top_k=top_k)

        context = ""
        db_chunks = []
        if results:
            chunk_ids = [r[0] for r in results]
            from sqlalchemy.future import select
            db_chunks = (await self.db.execute(select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids)))).scalars().all()
            context = "\n---\n".join(chunk.text for chunk in db_chunks)

        prompt = (
             f"Use the following context exclusively to answer the question. If the context does not contain the answer, say so.\n\n"
             f"Context:\n{context or 'No context provided.'}\n\n"
             f"Question: {query}\n\n"
             "Answer:"
         )

        completion_response = await embed_client.complete(prompt, model=completion_model_name)
        answer = completion_response["content"]
        usage = completion_response["usage"]
        actual_completion_model = completion_response["model"]

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        log_entry = QueryLog(
            knowledge_base_id=kb.id,
            query_text=query,
            retrieved_context=context,
            response_text=answer,
            completion_model=actual_completion_model,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            latency_ms=latency_ms
        )
        self.db.add(log_entry)

        return {"answer": answer, "context": context}

def get_rag_service(db):
    return RAGService(db)
