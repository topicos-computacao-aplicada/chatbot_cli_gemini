from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 🔥 RELACIONAMENTO COM MENSAGENS
    messages = relationship("Message", back_populates="conversation", lazy="select")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    tokens_used = Column(Integer, default=0)
    
    # 🔥 RELACIONAMENTO COM CONVERSA
    conversation = relationship("Conversation", back_populates="messages")