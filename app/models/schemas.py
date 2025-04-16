from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ai_provider: Optional[str] = None  # Provider ID or name

class KnowledgeBaseOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    ai_provider: Optional[str] = None

class KnowledgeBase(KnowledgeBaseOut):
    pass

class DocumentCreate(BaseModel):
    title: str
    source: Optional[str] = None
    status: Optional[str] = None

class DocumentOut(BaseModel):
    id: str
    knowledge_base_id: str
    title: str
    source: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

class QueryRequest(BaseModel):
    knowledge_base_id: str
    query: str
    ai_provider: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    citations: Optional[List[str]] = None
    provider: Optional[str] = None

class AIProviderCreate(BaseModel):
    id: str
    name: str
    type: str
    endpoint_url: str
    api_key: Optional[str] = None
    enabled: Optional[bool] = True
    config_json: Optional[str] = None

class AIProviderOut(BaseModel):
    id: str
    name: str
    type: str
    endpoint_url: str
    enabled: bool
    config_json: Optional[str] = None
