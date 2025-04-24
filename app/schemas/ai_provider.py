from pydantic import BaseModel
from typing import Optional

class AIProviderCreate(BaseModel):
    id: str
    name: str
    type: str
    endpoint_url: str
    api_key: Optional[str] = None
    enabled: Optional[bool] = True
    config_json: Optional[str] = None

class AIProviderOut(BaseModel):
    id: str
    name: str
    type: str
    endpoint_url: str
    enabled: bool
    config_json: Optional[str] = None
