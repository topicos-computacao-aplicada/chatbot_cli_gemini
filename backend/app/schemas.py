from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class MessageBase(BaseModel):
    content: str
    role: str

class MessageCreate(MessageBase):
    conversation_id: Optional[int] = None
    session_id: Optional[str] = None

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    timestamp: datetime
    tokens_used: int
    
    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    session_id: str

class ConversationResponse(BaseModel):
    id: int
    session_id: str
    created_at: datetime
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    session_id: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    message_id: int
    tokens_used: int