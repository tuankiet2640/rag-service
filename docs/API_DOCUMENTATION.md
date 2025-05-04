# RAG Service API Documentation

## Overview
This document provides comprehensive documentation for the RAG Service API, including authentication, knowledge base, document, and query endpoints. It also describes provider management and error handling practices.

---

## Authentication
- **POST** `/auth/login`
  - **Body:** `{ username: string, password: string }`
  - **Response:** `{ accessToken, refreshToken, user }`
  - **Notes:** Use username (not email) for login. Store tokens and user info in localStorage.

---

## Knowledge Base Endpoints
- **GET** `/api/v1/knowledge-bases/`
  - List all available knowledge bases.
  - **Response:** `List[{ id: string, name: string, description: string, ai_provider: string, chunking_strategy: string, chunk_size: int, chunk_overlap: int, embedding_model: string }]`
- **POST** `/api/v1/knowledge-bases/`
  - **Body:** `{ name: string, description?: string, ai_provider?: string, chunking_strategy?: string, chunk_size?: int, chunk_overlap?: int, embedding_model?: string }`
  - **Response:** `{ id: string, name: string, description: string, ai_provider: string, chunking_strategy: string, chunk_size: int, chunk_overlap: int, embedding_model: string }`
  - Create a new knowledge base (admin only). Allows specifying chunking and embedding settings. Defaults are used if not provided.
- **GET** `/api/v1/knowledge-bases/{kb_id}`
  - Get details of a specific knowledge base.
  - **Response:** `{ id: string, name: string, description: string, ai_provider: string, chunking_strategy: string, chunk_size: int, chunk_overlap: int, embedding_model: string }`
- **DELETE** `/api/v1/knowledge-bases/{kb_id}`
  - Delete a knowledge base (admin only).
- **POST** `/api/v1/knowledge-bases/{kb_id}/ingest`
  - **File Upload:** `file: UploadFile`
  - Ingest a document (PDF, DOCX, TXT) into the specified knowledge base (admin only). Uses the KB's configured chunking strategy.

---

## Document Endpoints
- **GET** `/api/v1/documents/{doc_id}`
  - Get a document by ID.
- **DELETE** `/api/v1/documents/{doc_id}`
  - Delete a document (admin only).

---

## Query Endpoints
- **POST** `/api/v1/query/`
  - **Body:** `{ knowledge_base_id: string, query: string, top_k?: int }`
  - **Response:** `{ answer: string, context: string }`
  - Query a knowledge base using its configured provider and vector search. Returns an LLM-generated answer and supporting context.
  - **Note:** Each query, its context, response, token usage, and latency are automatically logged for analysis and feedback.
- **POST** `/api/v1/query/feedback`
  - **Body:** `{ log_id: string (UUID), rating: int (-1, 0, or 1), comment?: string }`
  - **Response:** `{ log_id: string, rating: int, comment: string, message: string }`
  - Submit feedback for a previously executed query identified by its log ID.

---

## Provider Management
- Providers (OpenAI, Azure, Ollama, Cohere, Anthropic, etc.) are configured via environment variables (`.env`).
- Use the `ProviderManager` to dynamically select and instantiate providers.
- If a provider is not configured, a clear error message is returned.
- See `.env.example` for all required variables for each provider.

---

## Error Handling
- All endpoints return descriptive error messages and codes.
- If a provider is not setup, the error will clearly indicate which provider is missing and which environment variables to check.

---

## Example Error (Provider Not Setup)
```
{
  "detail": "Provider 'cohere' is not configured in your environment variables. Please set the required environment variables for this provider (see .env.example)."
}
```

---

## Security Notes
- API keys and sensitive config  stored in `.env` file.
- Use HTTPS and secure token storage in production.

---

## Further Reading
- See FastAPI auto-generated docs at `/docs` when the service is running.
- For provider-specific setup, see the comments in `.env.example`.

---

*Last updated: 2025-04-16*
