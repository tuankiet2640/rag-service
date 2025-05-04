# d:\AI\hai-service\rag-service\app\schemas\query_log.py
from pydantic import BaseModel, Field
from typing import Optional
import uuid

class QueryFeedbackCreate(BaseModel):
    log_id: uuid.UUID = Field(..., description="The ID of the query log entry to provide feedback for.")
    rating: int = Field(..., description="Feedback rating: 1 (good), -1 (bad), 0 (neutral/remove feedback).")
    comment: Optional[str] = Field(None, description="Optional textual feedback.")

class QueryFeedbackOut(BaseModel):
    log_id: uuid.UUID
    rating: Optional[int] = None
    comment: Optional[str] = None
    message: str = "Feedback submitted successfully."
