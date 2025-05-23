from pydantic import BaseModel
from typing import Optional, List
import uuid

class QueryRequest(BaseModel):
    knowledge_base_id: str
    query: str
    ai_provider: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    citations: Optional[List[str]] = None
    provider: Optional[str] = None
    log_id: uuid.UUID
