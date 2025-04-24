from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .base import Base
from sqlalchemy.orm import relationship

class Embedding(Base):
    __tablename__ = "rag_embedding"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("rag_document_chunk.id"), nullable=False)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    version = Column(String(64), nullable=True)
    vector = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chunk = relationship("DocumentChunk", back_populates="embeddings")
