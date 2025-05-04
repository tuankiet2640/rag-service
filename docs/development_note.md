# RAG Service Development Notes & Improvement Plan

This document outlines potential improvements and a roadmap for enhancing the Knowledge Base (KB) management and querying capabilities of the RAG service.

**Vision:** A highly configurable RAG system where users can precisely control ingestion, retrieval, and generation for each Knowledge Base to optimize performance for their specific use case and data.

## Key Improvement Areas

### 1. Deep KB Configuration

*   **Provider Selection:**
    *   Allow selection of specific AI Providers/Models for **Embedding** per KB.
    *   Allow selection of specific AI Providers/Models for **Generation** per KB.
    *   Frontend should fetch available providers/models from the backend API (`/api/v1/ai_providers`).
*   **Granular Chunking Control:**
    *   Offer multiple strategies (e.g., Recursive Character, Fixed Size, Sentence-based).
    *   Allow user configuration of `chunk_size` and `chunk_overlap` per KB.
    *   Provide UI hints or explanations about different strategies.
*   **Retrieval Tuning:**
    *   Configure number of retrieved chunks (`top_k`).
    *   Set similarity score thresholds for filtering results.
    *   (Future) Introduce Hybrid Search options (Vector + Keyword like BM25).
*   **Reranker Integration:**
    *   Optionally enable a reranking step after initial retrieval.
    *   Potentially allow selection of reranker model.
*   **Prompt Engineering:**
    *   Allow users to define custom prompt templates per KB.
    *   Provide sensible default templates.

### 2. Advanced Document Management

*   **Multiple Data Sources:**
    *   File Uploads: PDF, DOCX, TXT, MD, CSV, JSON, HTML.
    *   Direct Text Input.
    *   Web Scraping (provide URL, crawl depth).
*   **Asynchronous Processing:**
    *   Use background tasks (e.g., Celery) for parsing, chunking, embedding.
    *   Implement clear status tracking (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`) with error messages.
    *   Update status dynamically in the frontend UI.
*   **Metadata & Filtering:**
    *   Extract basic metadata (filename, type, date).
    *   Allow users to add custom tags.
    *   Filter documents within a KB based on metadata/tags.
*   **Incremental Updates (Advanced):**
    *   Detect document changes and only re-process modified content.
*   **Chunk Visualization (Advanced):**
    *   Allow users to view text chunks created for a document.

### 3. Enhanced Chat & Query Experience

*   **Source Citations:**
    *   Clearly display source document chunks used for generation.
    *   Link back to the source document/section if possible.
*   **Query Configuration:**
    *   Allow overriding default LLM generation parameters (temperature, max tokens) per query.
*   **Conversation History:**
    *   Store and display chat history per KB session.

### 4. Evaluation & Monitoring

*   **Feedback Dashboard:**
    *   Aggregate and visualize user feedback (👍/👎).
*   **Query Logs:**
    *   Store detailed logs for each query (input, chunks, prompt, response, feedback, etc.).
*   **RAG Evaluation (Future):**
    *   Integrate basic RAG evaluation metrics (e.g., using Ragas) against test datasets.

## Proposed Implementation Roadmap

1.  **Foundation (Must-Haves):**
    *   Provider Selection (Embedding/Generation).
    *   Granular Chunking Config (Strategies, Size, Overlap).
    *   Basic Retrieval Tuning (`top_k`).
    *   Async Processing & Status Tracking.
    *   Basic File Uploads (PDF/DOCX/TXT).
    *   Source Citations.
2.  **Enhancements (High Impact):**
    *   Reranker Integration.
    *   Prompt Engineering.
    *   More File Types & Data Sources (Web, Text).
    *   Conversation History.
3.  **Advanced (Longer Term):**
    *   Hybrid Search.
    *   Incremental Updates.
    *   Metadata & Filtering.
    *   Chunk Visualization.
    *   Feedback Dashboard & Query Logs.
    *   RAG Evaluation Metrics.
