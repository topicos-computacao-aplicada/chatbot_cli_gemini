from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import os

from app.database import get_db, engine
from app import models, schemas
from app.llm_client_interface import LLMClientInterface

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_llm_client() -> LLMClientInterface:
    """
    Factory para criar o cliente LLM baseado na variável de ambiente.
    
    Variável: LLM_PROVIDER
    Valores: 'gemini' (padrão) ou 'ollama'
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    
    if provider == "ollama":
        from app.ollama_client import OllamaClient
        return OllamaClient()
    elif provider == "gemini":
        from app.gemini_client import GeminiClient
        return GeminiClient()
    else:
        # Fallback seguro para Gemini se o provider for inválido
        from app.gemini_client import GeminiClient
        return GeminiClient()


# Inicializar cliente LLM (singleton por instância da aplicação)
llm_client: LLMClientInterface = get_llm_client()


@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db)
):
    """Endpoint principal para chat - Compatível com Gemini e Ollama"""
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
        
        # Buscar histórico para contexto (últimas 5 mensagens)
        history_messages = db.query(models.Message).filter(
            models.Message.conversation_id == conversation.id
        ).order_by(models.Message.timestamp.desc()).limit(5).all()
        
        history_context = build_history_context(history_messages)
        
        # 🔄 Gerar resposta com o cliente LLM configurado (polimorfismo)
        llm_response = llm_client.generate_response(
            prompt=request.message,
            context=history_context
        )
        
        # Salvar resposta do assistente
        assistant_message = models.Message(
            conversation_id=conversation.id,
            role="assistant",
            content=llm_response["text"],
            tokens_used=llm_response["tokens_used"]
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        # ✅ Resposta mantém o mesmo schema independente do provedor
        return schemas.ChatResponse(
            response=llm_response["text"],
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            tokens_used=llm_response["tokens_used"]
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
    
    conversation = db.query(models.Conversation)\
        .options(joinedload(models.Conversation.messages))\
        .filter(models.Conversation.session_id == session_id)\
        .first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    return conversation


@app.get("/health")
async def health_check():
    """Health check endpoint com informação do provedor ativo"""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    return {
        "status": "healthy", 
        "service": "Chatbot API", 
        "llm_provider": provider
    }


@app.get("/models")
async def list_available_models():
    """
    Endpoint opcional para listar modelos disponíveis.
    Útil para debugging e configuração.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    
    if provider == "ollama" and hasattr(llm_client, "list_models"):
        return {
            "provider": "ollama",
            "models": llm_client.list_models()
        }
    
    return {
        "provider": provider,
        "models": [os.getenv("GEMINI_MODEL", "gemini-pro")] if provider == "gemini" else []
    }
    
@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está rodando"""
    return {"message": "Chatbot API está rodando!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)