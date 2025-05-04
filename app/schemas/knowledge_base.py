from pydantic import BaseModel, Field
from typing import Optional
import uuid

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ai_provider: Optional[str] = None  # Provider ID or name
    chunking_strategy: Optional[str] = Field(default="recursive", description="Chunking strategy (e.g., 'recursive', 'fixed_size')")
    chunk_size: Optional[int] = Field(default=1000, description="Target chunk size")
    chunk_overlap: Optional[int] = Field(default=200, description="Chunk overlap size")
    embedding_model: Optional[str] = Field(default="text-embedding-ada-002", description="Embedding model name")


class KnowledgeBaseOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    ai_provider: Optional[str] = None
    chunking_strategy: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    embedding_model: Optional[str] = None

    class Config:
        from_attributes = True # Renamed from orm_mode


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ai_provider: Optional[str] = None
    chunking_strategy: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    embedding_model: Optional[str] = None


class KnowledgeBase(KnowledgeBaseOut):
    pass
