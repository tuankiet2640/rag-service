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
- **GET** `/api/v1/knowledge_bases/`
  - List all knowledge bases.
- **POST** `/api/v1/knowledge_bases/`
  - Create a new knowledge base.
- **GET** `/api/v1/knowledge_bases/{kb_id}`
  - Get details of a specific knowledge base.
- **POST** `/api/v1/knowledge_bases/{kb_id}/ingest`
  - Ingest one or more documents (multipart upload).
- **POST** `/api/v1/knowledge_bases/{kb_id}/documents`
  - Add a document with raw text (admin only).

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
  - **Response:** `{ answer: string, context: [string] }`
  - Query a knowledge base using the selected provider and FAISS vector search. Returns an LLM-generated answer and supporting context.

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
