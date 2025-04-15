from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

class WhatsAppMessageDoc(BaseModel):
    id: str = Field(..., alias="_id")
    content: str
    type: str
    createdAt: datetime = Field(..., alias="createdAt")
    # Campos para vector search
    embedding: Optional[List[float]] = Field(None, description="Vector embedding of the content")
    embedding_model: Optional[str] = Field(None, description="Embedding model used")

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

class WhatsAppChatDoc(BaseModel):
    id: str = Field(..., alias="_id")
    contact_id: str
    contact_name: Optional[str] = None
    mode: str  # 'human' ou 'agent'
    status: str  # 'open', 'closed'
    last_message_ts: Optional[datetime] = None
    unread_count: int = 0
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}