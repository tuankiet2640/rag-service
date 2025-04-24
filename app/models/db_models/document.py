from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .base import Base
from sqlalchemy.orm import relationship

class Document(Base):
    __tablename__ = "rag_document"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("rag_knowledge_base.id"), nullable=False)
    title = Column(String(256), nullable=False)
    source = Column(Text, nullable=True)
    status = Column(String(32), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
