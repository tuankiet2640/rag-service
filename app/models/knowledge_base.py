from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base
from sqlalchemy.orm import relationship

class KnowledgeBase(Base):
    __tablename__ = "rag_knowledge_base"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text)
    ai_provider = Column(String(64), nullable=True)
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")

    # New configuration fields
    chunking_strategy = Column(String(64), nullable=True, default="recursive")
    chunk_size = Column(Integer, nullable=True, default=1000)
    chunk_overlap = Column(Integer, nullable=True, default=200)
    embedding_model = Column(String(128), nullable=True, default="text-embedding-ada-002")
