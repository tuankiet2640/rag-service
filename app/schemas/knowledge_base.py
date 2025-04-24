from pydantic import BaseModel
from typing import Optional

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
