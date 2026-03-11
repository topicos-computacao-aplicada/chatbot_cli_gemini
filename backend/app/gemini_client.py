from dotenv import load_dotenv
import os
import google.generativeai as genai
from typing import List, Dict

load_dotenv()

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
        self._configure_client()
    
    def _configure_client(self):
        """Configura o cliente Gemini"""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não encontrada no ambiente")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_response(self, prompt: str, context: str = None) -> Dict:
        """Gera resposta usando Gemini API"""
        try:
            # Construir prompt com contexto se fornecido
            full_prompt = self._build_prompt(prompt, context)
            
            response = self.model.generate_content(full_prompt)
            
            return {
                "text": response.text,
                "tokens_used": self._estimate_tokens(full_prompt + response.text)
            }
        except Exception as e:
            return {
                "text": f"Erro ao gerar resposta: {str(e)}",
                "tokens_used": 0
            }
    
    def _build_prompt(self, prompt: str, context: str = None) -> str:
        """Constrói o prompt final com contexto"""
        base_prompt = """
        Você é um assistente IA útil e prestativo. Responda às perguntas de forma clara e concisa.  
        """
        
        if context:
            base_prompt += f"Contexto adicional: {context}\n\n"
        
        base_prompt += f"Pergunta: {prompt}\nResposta:"
        
        return base_prompt
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimativa simples de tokens (aproximada)"""
        return len(text.split()) + len(text) // 4