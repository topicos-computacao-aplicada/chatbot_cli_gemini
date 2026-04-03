# 📚 Cliente HTTP TUI para ChatBot

Explicação de cada parte deste código que implementa uma interface de terminal (TUI) para conversar com uma API de chatbot.

## 🔹 1. Imports e Bibliotecas

```python
import os
import requests
import json
import uuid

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint
import sys
```

| Módulo/Função | Propósito |
|--------------|-----------|
| `os` | Acessar variáveis de ambiente (ex: `API_URL`) |
| `requests` | Fazer requisições HTTP para a API REST |
| `json` | Manipular dados JSON (embora `requests` já faça isso automaticamente) |
| `uuid` | Gerar identificadores únicos para sessões de chat |
| `rich.console.Console` | Interface principal para output formatado no terminal |
| `rich.panel.Panel` | Criar boxes/bordas ao redor do texto |
| `rich.markdown.Markdown` | Renderizar texto Markdown no terminal |
| `rich.print` | Print colorido (não usado diretamente aqui) |
| `sys` | Acessar argumentos da linha de comando (`sys.argv`) |

> 💡 **Rich**: Biblioteca que permite criar interfaces de terminal ricas em cores, formatação e elementos visuais, similar ao que faríamos em uma interface web.

## 🔹 2. Classe `ChatClient` - Estrutura Geral

```python
class ChatClient:
    def __init__(self, ip_servidor):
        self.base_url = os.getenv("API_URL", f"http://{ip_servidor}:8000")
        self.session_id = str(uuid.uuid4())
        self.console = Console()
```

### Método `__init__` (Construtor):

| Atributo | Descrição |
|----------|-----------|
| `self.base_url` | URL base da API. Prioriza variável de ambiente `API_URL`, senão monta com o IP fornecido + porta `8000` |
| `self.session_id` | UUID único gerado para identificar esta sessão de chat no servidor |
| `self.console` | Instância do `Console` do Rich para formatar output no terminal |

> 🔄 **Padrão de Design**: Encapsulamento — toda a lógica de comunicação com a API fica dentro desta classe.


## 🔹 3. Método `start_chat()` - Loop Principal do Chat

```python
def start_chat(self):
    """Inicia a sessão de chat"""
    self.console.print(
        Panel.fit(
            "[bold blue]🤖 Gemini ChatBot[/bold blue]\n"
            f"[dim]Sessão: {self.session_id}[/dim]\n"
            "Digite 'sair' para encerrar ou 'ajuda' para comandos",
            border_style="green"
        )
    )
```

### 3.1. Exibição do Banner Inicial

```python
Panel.fit(...)  # Cria um box que se ajusta ao conteúdo
```

| Elemento | Significado |
|----------|-------------|
| `[bold blue]...[/bold blue]` | Texto em **negrito** e **azul** (sintaxe do Rich) |
| `[dim]...[/dim]` | Texto com opacidade reduzida (estilo "secundário") |
| `border_style="green"` | Borda verde ao redor do painel |

**Resultado visual no terminal:**
```
┌─────────────────────────────────┐
│ 🤖 Gemini ChatBot               │
│ Sessão: abc123-def456...        │
│ Digite 'sair' para encerrar...  │
└─────────────────────────────────┘
```


### 3.2. Loop Infinito de Interação

```python
while True:
    try:
        user_input = self.console.input("\n[bold yellow]Você:[/bold yellow] ").strip()
```

- `self.console.input(...)`: Exibe prompt colorido e captura entrada do usuário
- `.strip()`: Remove espaços em branco no início/fim da entrada


### 3.3. Processamento de Comandos Especiais

```python
if user_input.lower() in ['sair', 'exit', 'quit']:
    self.console.print("[green]Até logo! 👋[/green]")
    break
elif user_input.lower() in ['ajuda', 'help']:
    self._show_help()
    continue
elif user_input.lower() == 'historico':
    self._show_history()
    continue
elif not user_input:
    continue
```

| Comando | Ação |
|---------|--------|
| `sair`/`exit`/`quit` | Exibe mensagem de despedida e encerra o loop (`break`) |
| `ajuda`/`help` | Chama `_show_help()` e volta ao início do loop (`continue`) |
| `historico` | Chama `_show_history()` para buscar histórico do servidor |
| `(vazio)` | Ignora entrada vazia e pede nova entrada |

> ✅ `continue` pula para a próxima iteração do `while`; `break` sai completamente do loop.


### 3.4. Envio da Mensagem para a API

```python
with self.console.status("[bold green]Aguarde...[/bold green]", spinner="dots") as status:
    # Enviar mensagem para API
    response = self._send_message(user_input)
self._display_response(response)
```

#### `console.status(...)`:
- Exibe um **spinner animado** ("dots") enquanto processa
- Context manager (`with`): o spinner para automaticamente ao sair do bloco
- Melhora a UX indicando que o sistema está trabalhando

#### Fluxo:
```
1. Usuário digita mensagem
2. Spinner aparece: "Aguarde..."
3. _send_message() faz requisição HTTP à API
4. Spinner some
5. _display_response() mostra a resposta formatada
```


### 3.5. Tratamento de Exceções

```python
except KeyboardInterrupt:
    self.console.print("\n[red]Interrompido pelo usuário[/red]")
    break
except Exception as e:
    self.console.print(f"[red]Erro: {str(e)}[/red]")
```

| Exceção | Quando ocorre | Ação |
|---------|--------------|--------|
| `KeyboardInterrupt` | Usuário pressiona `Ctrl+C` | Mensagem amigável e encerramento limpo |
| `Exception` | Qualquer erro não tratado (rede, API, etc.) | Exibe mensagem de erro em vermelho |

> 🛡️ **Boa prática**: Nunca deixe o programa "quebrar" sem feedback ao usuário.


## 🔹 4. Método `_send_message()` - Comunicação com a API

```python
def _send_message(self, message: str) -> dict:
    """Envia mensagem para a API"""
    payload = {
        "message": message,
        "session_id": self.session_id
    }
    
    response = requests.post(
        f"{self.base_url}/chat",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        raise Exception(f"Erro na API: {response.text}")
    
    return response.json()
```

### Passo a passo:

1. **Monta o payload JSON**:
```python
{
    "message": "Olá, como funciona machine learning?",
    "session_id": "abc123-def456-..."
}
```

2. **Faz requisição POST**:
```python
requests.post(
    url="http://IP:8000/chat",
    json=payload,           # requests serializa automaticamente para JSON
    headers={"Content-Type": "application/json"}
)
```

3. **Valida resposta**:
```python
if response.status_code != 200:  # 200 = OK
    raise Exception(f"Erro na API: {response.text}")
```

4. **Retorna dados parseados**:
```python
return response.json()  # Converte JSON da resposta para dict Python
```

> 📦 **requests.json()**: Método conveniente que já faz `json.loads(response.text)` automaticamente.


## 🔹 5. Método `_display_response()` - Exibição da Resposta

```python
def _display_response(self, response: dict):
    """Exibe a resposta formatada"""
    response_text = response.get("response", "Sem resposta")
    tokens_used = response.get("tokens_used", 0)
    
    # Usar Markdown para melhor formatação
    md = Markdown(response_text)
    
    self.console.print(
        Panel(
            md,
            title="[bold green]🤖 Assistente[/bold green]",
            title_align="left",
            border_style="blue",
            subtitle=f"[dim]Tokens usados: {tokens_used}[/dim]"
        )
    )
```

### Elementos de formatação:

| Componente | Função |
|------------|--------|
| `response.get("response", "Sem resposta")` | Acesso seguro ao campo; usa valor padrão se não existir |
| `Markdown(response_text)` | Parseia texto Markdown (títulos, listas, código) para formatação Rich |
| `Panel(...)` | Cria box com título, borda e subtítulo |
| `title_align="left"` | Alinha o título à esquerda |
| `subtitle` | Exibe metadado (tokens usados) na parte inferior do painel |

**Exemplo de saída no terminal:**
```
┌─ 🤖 Assistente ──────────────────────┐
│                                      │
│ Machine Learning é um subcampo da   │
│ Inteligência Artificial que...      │
│                                      │
│ • Usa dados para treinar modelos    │
│ • Melhora com a experiência         │
│                                      │
└─ Tokens usados: 142 ─────────────────┘
```


## 🔹 6. Método `_show_help()` - Menu de Ajuda

```python
def _show_help(self):
    """Mostra ajuda dos comandos"""
    help_text = """
[b]Comandos disponíveis:[/b]
• [yellow]sair[/yellow] - Encerra o chat
• [yellow]historico[/yellow] - Mostra histórico da conversa
• [yellow]ajuda[/yellow] - Mostra esta mensagem

[b]Exemplos de perguntas:[/b]
• "Explique o que é machine learning"
• "Como funciona um neural network?"
• "Me ajude a debugar um código Python"
"""
    self.console.print(Panel(help_text, title="[bold]Ajuda[/bold]", border_style="yellow"))
```

### Sintaxe de formatação do Rich:

| Tag | Efeito |
|-----|--------|
| `[b]...[/b]` | **Negrito** |
| `[yellow]...[/yellow]` | Texto na cor amarela |
| `•` | Marcador de lista (caractere Unicode) |

> 💡 O Rich interpreta essas tags no momento do `print`, similar ao Markdown.


## 🔹 7. Método `_show_history()` - Buscar Histórico do Servidor

```python
def _show_history(self):
    """Mostra histórico da conversa"""
    try:
        response = requests.get(f"{self.base_url}/conversations/{self.session_id}")
        if response.status_code == 200:
            conversation = response.json()
            self.console.print("\n[bold cyan]📜 Histórico da Conversa:[/bold cyan]")
            for msg in conversation.get("messages", []):
                role = "👤 Você" if msg["role"] == "user" else "🤖 Assistente"
                self.console.print(f"\n[bold]{role}:[/bold] {msg['content']}")
                self.console.print(f"[dim]{msg['timestamp']}[/dim]")
        else:
            self.console.print("[yellow]Nenhum histórico encontrado[/yellow]")
    except Exception as e:
        self.console.print(f"[red]Erro ao buscar histórico: {str(e)}[/red]")
```

### Fluxo da requisição GET:

```
1. GET /conversations/{session_id}
2. Se status == 200:
   ├─ Parseia JSON da resposta
   ├─ Itera sobre lista de mensagens
   ├─ Para cada mensagem:
   │  ├─ Define avatar/role (👤 ou 🤖)
   │  ├─ Exibe conteúdo em negrito
   │  └─ Exibe timestamp em texto "dim"
3. Se status != 200:
   └─ Exibe "Nenhum histórico encontrado"
4. Se exceção (rede, timeout, etc.):
   └─ Exibe mensagem de erro em vermelho
```

### Exemplo de resposta da API:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "O que é Python?",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "role": "assistant", 
      "content": "Python é uma linguagem de programação...",
      "timestamp": "2024-01-15T10:30:05Z"
    }
  ]
}
```


## 🔹 8. Bloco Principal `if __name__ == "__main__"`

```python
if __name__ == "__main__":
    if len(sys.argv) > 1:
        ip_servidor = sys.argv[1]
        client = ChatClient(ip_servidor)
        client.start_chat()
    else:
        print("Por favor forneça o IP do servidor")
```

### Como funciona:

| Condição | Ação |
|----------|--------|
| `len(sys.argv) > 1` | Usuário forneceu argumento (ex: `python chat_client.py 192.168.1.100`) |
| `sys.argv[1]` | Primeiro argumento após o nome do script |
| `ChatClient(ip_servidor)` | Instancia a classe com o IP fornecido |
| `client.start_chat()` | Inicia o loop interativo do chat |
| `else` | Sem argumentos → exibe mensagem de uso e encerra |

### Exemplos de execução:

```bash
# ✅ Correto: fornece IP do servidor
python chat_client.py 192.168.1.100

# ✅ Usando variável de ambiente para URL customizada
API_URL=https://api.meudominio.com python chat_client.py ignored

# ❌ Sem argumentos: mostra erro
python chat_client.py
# Output: "Por favor forneça o IP do servidor"
```

> 🔑 `if __name__ == "__main__"`: Garante que o código só execute se o arquivo for rodado diretamente, não se for importado como módulo.


## 🔹 9. Fluxo Completo da Aplicação (Diagrama)

```
🚀 python chat_client.py 192.168.1.100
│
├─▶ __main__: captura IP = "192.168.1.100"
│
├─▶ ChatClient.__init__:
│   ├─ base_url = "http://192.168.1.100:8000"
│   ├─ session_id = uuid4() → "abc123..."
│   └─ console = Console()
│
├─▶ start_chat():
│   ├─ Exibe banner inicial com Panel
│   │
│   └─ 🔄 while True (loop principal):
│       │
│       ├─ 1. Captura input do usuário
│       │
│       ├─ 2. Verifica comandos especiais:
│       │   ├─ 'sair' → break (encerra)
│       │   ├─ 'ajuda' → _show_help() → continue
│       │   ├─ 'historico' → _show_history() → continue
│       │   └─ vazio → continue
│       │
│       ├─ 3. Mensagem normal:
│       │   ├─ Exibe spinner "Aguarde..."
│       │   ├─ _send_message() → POST /chat
│       │   ├─ Spinner some
│       │   └─ _display_response() → mostra resposta em Panel
│       │
│       └─ 4. Tratamento de erros:
│           ├─ Ctrl+C → mensagem + break
│           └─ Exception → erro em vermelho + continua
│
└─✅ Chat encerrado limpo
```


## 🔹 10. Boas Práticas e Padrões Utilizados

| Prática | Benefício |
|---------|-----------|
| ✅ **Encapsulamento em classe** | Código organizado, reutilizável e testável |
| ✅ **Métodos privados (`_nome`)** | Indica que são detalhes de implementação interna |
| ✅ **Tratamento de exceções granular** | Feedback claro ao usuário em diferentes cenários de erro |
| ✅ **Uso de `console.status()`** | UX profissional com feedback visual de processamento |
| ✅ **Formatação com Rich** | Terminal legível, colorido e com estrutura visual |
| ✅ **Fallback para variáveis de ambiente** | Flexibilidade para deploy em diferentes ambientes |
| ✅ **Session ID por instância** | Isolamento de conversas entre múltiplos clientes |
| ✅ **Comandos de texto intuitivos** | Experiência similar a outros CLIs (sair, ajuda, histórico) |


## 🔹 11. Possíveis Melhorias Futuras

```python
# 1. Timeout configurável nas requisições
response = requests.post(..., timeout=30)

# 2. Retry automático para falhas transitórias de rede
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 3. Histórico local em cache (para funcionar offline parcialmente)
import pickle
def _save_local_history(messages): ...

# 4. Autenticação JWT (se a API exigir)
headers = {"Authorization": f"Bearer {os.getenv('API_TOKEN')}"}

# 5. Logging estruturado para debug em produção
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Enviando mensagem para {self.base_url}/chat")

# 6. Suporte a upload de arquivos (se a API aceitar)
# Adicionar opção para anexar arquivos à mensagem
```

## 🔹 12. Resumo Visual da Arquitetura

```
┌─────────────────────┐
│   Terminal (TUI)    │
│  ┌───────────────┐  │
│  │   Rich Console│  │
│  │  • Panels     │  │
│  │  • Markdown   │  │
│  │  • Cores      │  │
│  └───────┬───────┘  │
└──────────┼──────────┘
           │ HTTP/JSON
           ▼
┌────────────────────────────┐
│   API Backend              │
│  • POST /chat              │
│  • GET /conversations/{id} │
│  • Session management      │
└────────────────────────────┘
```


> 💡 **Conclusão**: Este código é um exemplo excelente de como criar uma interface de terminal usando Python + Rich, mantendo separação de responsabilidades, tratamento robusto de erros e uma experiência de usuário agradável — tudo sem sair do terminal!