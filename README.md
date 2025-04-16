# RAG Knowledge Management Service

A Retrieval-Augmented Generation (RAG) microservice for document ingestion, semantic search, and LLM-powered Q&A, secured with centralized authentication via mai-services.

---

## **Authentication**
- All protected endpoints require a valid JWT from mai-services in the `Authorization: Bearer <token>` header.
- Tokens are validated by calling mai-services `/api/v1/auth/validate-token`.

---

## **Endpoints & Example Requests**

### 1. **List Knowledge Bases**
- **GET** `/api/v1/knowledge_bases/`
- **Headers:** `Authorization: Bearer <token>`

```
curl -X GET http://localhost:8000/api/v1/knowledge_bases/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

### 2. **Create Knowledge Base**
- **POST** `/api/v1/knowledge_bases/`
- **Headers:** `Authorization: Bearer <token>`
- **Body:**
```json
{
  "name": "My KB",
  "description": "Test KB",
  "ai_provider": "openai"
}
```

```
curl -X POST http://localhost:8000/api/v1/knowledge_bases/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My KB", "description": "Test KB", "ai_provider": "openai"}'
```

---

### 3. **Ingest Documents (Admin Only)**
- **POST** `/api/v1/knowledge_bases/{kb_id}/ingest`
- **Headers:** `Authorization: Bearer <token>`
- **Body:** Multipart file upload (supports `.txt`, `.pdf`, `.docx`)
- **Note:** For PDF and DOCX, only extracted text is stored and indexed. Binary data is never stored in the DB.

```
curl -X POST "http://localhost:8000/api/v1/knowledge_bases/<KB_ID>/ingest" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "files=@/path/to/your/document.txt"

# Example for PDF
curl -X POST "http://localhost:8000/api/v1/knowledge_bases/<KB_ID>/ingest" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "files=@/path/to/your/document.pdf"

# Example for DOCX
curl -X POST "http://localhost:8000/api/v1/knowledge_bases/<KB_ID>/ingest" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "files=@/path/to/your/document.docx"
```

---

### 4. **Query Knowledge Base**
- **POST** `/api/v1/knowledge_bases/{kb_id}/chat`
- **Headers:** `Authorization: Bearer <token>`
- **Body:**
```json
{
  "query": "What is this document about?"
}
```

```
curl -X POST "http://localhost:8000/api/v1/knowledge_bases/<KB_ID>/api/v1/chat" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}'
```

---

### ⚠️ Note: Database Table Initialization

**To create all tables as defined in your models, run:**
```bash
python -m app.db.init_db
```

For production or advanced migrations, consider using [Alembic](https://alembic.sqlalchemy.org/) to manage schema changes.

---

### 5. **Health Check**
- **GET** `/api/v1/knowledge_bases/health`

```
curl http://localhost:8000/api/v1/knowledge_bases/health
```

---

## **Setup**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # Required for PDF/DOCX support:
   # pip install PyPDF2 python-docx
   ```
2. **Configure environment:**
   - Set up `.env` with your DB and AI provider credentials.
   - Ensure mai-services is running and accessible.
3. **Run the service:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## **Notes**
- Only users with `ADMIN` role (from mai-services) can ingest documents.
- All endpoints expect JWTs issued by mai-services.
- PDF and DOCX files are supported for ingestion; only extracted text is indexed.
- All ingestion is chunked and only non-empty chunks are sent to the embedding model.
- If you see encoding or provider errors, check your `.env` for correct API keys and set `OPENAI_API_TYPE=openai` or `OPENAI_API_TYPE=azure` as needed.
- For Azure OpenAI, ensure `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, and `AZURE_OPENAI_EMBEDDING_MODEL` are set.
- For OpenAI, ensure `OPENAI_API_KEY` and `OPENAI_EMBEDDING_MODEL` are set (and optionally `OPENAI_API_TYPE=openai`).
- Vector search and LLM response are demo/stub; integrate with your preferred vector DB and LLM as needed.

---

## **License**
MIT
