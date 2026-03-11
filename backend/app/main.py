from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List
import uuid

from app.database import get_db, engine
from app import models
from app import schemas
from app.gemini_client import GeminiClient

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gemini Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

gemini_client = GeminiClient()

@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    """Endpoint principal para chat"""
    try:
        # Buscar ou criar conversa
        conversation = db.query(models.Conversation).filter(
            models.Conversation.session_id == request.session_id
        ).first()
        
        if not conversation:
            conversation = models.Conversation(session_id=request.session_id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # Salvar mensagem do usuário
        user_message = models.Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()
        
        # Buscar histórico para contexto
        history_messages = db.query(models.Message).filter(
            models.Message.conversation_id == conversation.id
        ).order_by(models.Message.timestamp.desc()).limit(5).all()
        
        history_context = build_history_context(history_messages)
        
        # Gerar resposta com Gemini
        gemini_response = gemini_client.generate_response(
            prompt=request.message,
            context=history_context
        )
        
        # Salvar resposta do assistente
        assistant_message = models.Message(
            conversation_id=conversation.id,
            role="assistant",
            content=gemini_response["text"],
            tokens_used=gemini_response["tokens_used"]
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return schemas.ChatResponse(
            response=gemini_response["text"],
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            tokens_used=gemini_response["tokens_used"]
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

def build_history_context(messages: List[models.Message]) -> str:
    """Constrói contexto do histórico de conversa"""
    if not messages:
        return ""
    
    history = "Histórico recente da conversa:\n"
    
    for msg in reversed(messages):  # Ordem cronológica
        role = "Usuário" if msg.role == "user" else "Assistente"
        history += f"{role}: {msg.content}\n"
    
    return history

@app.get("/conversations/{session_id}", response_model=schemas.ConversationResponse)
async def get_conversation(session_id: str, db: Session = Depends(get_db)):
    """Recupera conversa por session_id com todas as mensagens"""
    
    # 🔥 CARREGAR CONVERSA COM MENSAGENS (EAGER LOADING)
    conversation = db.query(models.Conversation)\
        .options(joinedload(models.Conversation.messages))\
        .filter(models.Conversation.session_id == session_id)\
        .first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    return conversation

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Gemini Chatbot API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)