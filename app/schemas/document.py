from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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
