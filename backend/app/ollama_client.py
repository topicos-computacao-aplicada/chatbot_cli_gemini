from dotenv import load_dotenv
import os
import requests
from typing import Dict, Optional
from app.llm_client_interface import LLMClientInterface

load_dotenv()

class OllamaClient(LLMClientInterface):
    """Cliente para interação com modelos LLM locais via Ollama"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama2")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
        self.num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "2048"))
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict:
        """Gera resposta usando a API local do Ollama"""
        try:
            full_prompt = self._build_prompt(prompt, context)
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.num_predict
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            response_text = result.get("response", "").strip()
            
            return {
                "text": response_text,
                "tokens_used": self._estimate_tokens(full_prompt + response_text)
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "text": "Erro: Não foi possível conectar ao Ollama. Verifique se o serviço está rodando em localhost:11434",
                "tokens_used": 0
            }
        except requests.exceptions.Timeout:
            return {
                "text": "Erro: Timeout ao gerar resposta. O modelo pode estar processando uma requisição longa.",
                "tokens_used": 0
            }
        except requests.exceptions.HTTPError as e:
            return {
                "text": f"Erro HTTP do Ollama: {str(e)}",
                "tokens_used": 0
            }
        except Exception as e:
            return {
                "text": f"Erro ao gerar resposta: {str(e)}",
                "tokens_used": 0
            }
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Constrói o prompt final com contexto, mantendo consistência com GeminiClient"""
        base_prompt = """Você é um assistente IA útil e prestativo. Responda às perguntas de forma clara e concisa."""
        
        if context:
            base_prompt += f"\n\nContexto adicional:\n{context}"
        
        base_prompt += f"\n\nPergunta: {prompt}\nResposta:"
        
        return base_prompt
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimativa simples de tokens (compatível com a implementação do GeminiClient)"""
        # Aproximação: 1 token ≈ 4 caracteres ou 1 palavra
        return len(text.split()) + len(text) // 4
    
    def list_models(self) -> list:
        """Lista modelos disponíveis no Ollama (utilitário opcional)"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return [model["name"] for model in response.json().get("models", [])]
        except Exception:
            return []