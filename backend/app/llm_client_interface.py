from abc import ABC, abstractmethod
from typing import Dict, Optional

class LLMClientInterface(ABC):
    """
    Interface comum para clientes LLM.
    Garante que todos os clientes retornem o mesmo formato de resposta.
    """
    
    @abstractmethod
    def generate_response(self, prompt: str, context: Optional[str] = None) -> Dict:
        """
        Gera resposta do modelo LLM.
        
        Args:
            prompt: Pergunta do usuário
            context: Contexto opcional do histórico de conversa
            
        Returns:
            Dict com estrutura padronizada:
            {
                "text": str,        # Resposta gerada
                "tokens_used": int  # Estimativa de tokens utilizados
            }
        """
        pass