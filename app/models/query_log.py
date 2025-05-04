# d:\AI\hai-service\rag-service\app\models\query_log.py
import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
from .knowledge_base import KnowledgeBase  # Import for relationship typing

class QueryLog(Base):
    __tablename__ = "rag_query_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("rag_knowledge_base.id"), nullable=False)
    # user_id = Column(String(128), nullable=True) # Optional: Add if you track users

    query_text = Column(Text, nullable=False)
    retrieved_context = Column(Text, nullable=True)
    response_text = Column(Text, nullable=True)

    completion_model = Column(String(128), nullable=True) # e.g., gpt-3.5-turbo
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    latency_ms = Column(Float, nullable=True) # Time taken for the RAG query + LLM call

    # Feedback fields
    feedback_rating = Column(Integer, nullable=True) # e.g., 1 (good), -1 (bad), 0 (neutral/removed)
    feedback_comment = Column(Text, nullable=True)

    # Relationships (optional but good practice)
    knowledge_base = relationship("KnowledgeBase") # If needed for queries

    # Optional: Add fields for other feedback later
