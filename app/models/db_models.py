from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class KnowledgeBase(Base):
    __tablename__ = "rag_knowledge_base"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text)
    ai_provider = Column(String(64), nullable=True)
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "rag_document"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("rag_knowledge_base.id"), nullable=False)
    title = Column(String(256), nullable=False)
    source = Column(Text, nullable=True)
    status = Column(String(32), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

class DocumentChunk(Base):
    __tablename__ = "rag_document_chunk"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("rag_document.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    embeddings = relationship("Embedding", back_populates="chunk", cascade="all, delete-orphan")

class Embedding(Base):
    __tablename__ = "rag_embedding"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("rag_document_chunk.id"), nullable=False)
    provider = Column(String(64), nullable=False)
    model = Column(String(128), nullable=False)
    version = Column(String(64), nullable=True)
    vector = Column(Text, nullable=False)  # Store as JSON/text for now; can switch to pgvector later
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chunk = relationship("DocumentChunk", back_populates="embeddings")

class AIProvider(Base):
    __tablename__ = "rag_ai_provider"
    id = Column(String(64), primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    type = Column(String(32), nullable=False)
    endpoint_url = Column(String(256), nullable=False)
    api_key = Column(String(256), nullable=True)
    enabled = Column(Integer, default=1)
    config_json = Column(Text, nullable=True)
