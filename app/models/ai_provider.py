from sqlalchemy import Column, String, Integer, Text
from .base import Base

class AIProvider(Base):
    __tablename__ = "rag_ai_provider"
    id = Column(String(64), primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    type = Column(String(32), nullable=False)
    endpoint_url = Column(String(256), nullable=False)
    api_key = Column(String(256), nullable=True)
    enabled = Column(Integer, default=1)
    config_json = Column(Text, nullable=True)
