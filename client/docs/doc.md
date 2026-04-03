# 📚 ChatClient TUI v2.0 - Explicação Detalhada do Código

Explicação passo a passo de cada parte do código atualizado que implementa uma interface de terminal (TUI) para conversar com uma API de chatbot, com **verificação automática de conexão** e melhorias de UX.

---

## 🔹 1. Imports e Bibliotecas

```python
import os
import sys
import time
import requests
import uuid

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
```

| Módulo/Função | Propósito | Novidade v2.0 |
|--------------|-----------|--------------|
| `os` | Acessar variáveis de ambiente (`API_URL`) | — |
| `sys` | Acessar argumentos da linha de comando (`sys.argv`) | — |
| `time` | Pausas controladas para feedback visual | 🆕 Usado em `verify_connection()` |
| `requests` | Requisições HTTP para a API REST | — |
| `uuid` | Gerar identificadores únicos para sessões | — |
| `rich.console.Console` | Interface principal para output formatado | — |
| `rich.panel.Panel` | Criar boxes/bordas ao redor do texto | — |
| `rich.markdown.Markdown` | Renderizar texto Markdown no terminal | — |
| `rich.progress.Progress` | Spinner animado com descrição para health check | 🆕 Nova importação |
| `rich.progress.SpinnerColumn` | Coluna de spinner para `Progress` | 🆕 Nova importação |
| `rich.progress.TextColumn` | Coluna de texto dinâmico para `Progress` | 🆕 Nova importação |

> 💡 **Rich Progress**: Módulo adicionado na v2.0 para exibir spinners profissionais com mensagens descritivas durante operações assíncronas como verificação de conexão.

---

## 🔹 2. Constantes e Configurações Globais (NOVIDADE v2.0)

```python
DEFAULT_PORT = 8000
CONNECTION_TIMEOUT = 5  # segundos
HEALTH_ENDPOINTS = ["/health", "/", "/chat", "/api/health"]
```

| Constante | Valor | Propósito |
|-----------|-------|-----------|
| `DEFAULT_PORT` | `8000` | Porta padrão da API se não especificada |
| `CONNECTION_TIMEOUT` | `5` | Tempo máximo em segundos para health check |
| `HEALTH_ENDPOINTS` | `["/health", "/", "/chat", "/api/health"]` | Lista de endpoints testados sequencialmente para verificar conectividade |

> 🎯 **Estratégia**: Testar múltiplos endpoints aumenta a resiliência — se `/health` não existir, tenta `/`, depois `/chat`, etc.

---

## 🔹 3. Painéis Pré-definidos para Reutilização (NOVIDADE v2.0)

```python
PAINEL_BANNER = Panel.fit(
    "[bold blue]🤖 Gemini ChatBot[/bold blue]\n"
    "Digite 'sair' para encerrar ou 'ajuda' para comandos",
    border_style="green",
    padding=(1, 2)
)

PAINEL_AJUDA = Panel(
    """[b]Comandos disponíveis:[/b] ... """.strip(),
    title="[bold]Ajuda[/bold]",
    border_style="yellow",
    padding=(1, 2)
)
```

| Painel | Propósito | Benefício |
|--------|-----------|-----------|
| `PAINEL_BANNER` | Banner inicial do chat | Consistência visual, fácil manutenção |
| `PAINEL_AJUDA` | Menu de ajuda com comandos | Centraliza conteúdo, evita duplicação |

### Parâmetros do `Panel`:

| Parâmetro | Valor | Efeito |
|-----------|-------|--------|
| `Panel.fit(...)` | — | Ajusta largura automaticamente ao conteúdo |
| `border_style="green"` | `"green"` | Borda verde para sucesso/informação |
| `padding=(1, 2)` | `(linhas, colunas)` | Espaçamento interno: 1 linha acima/abaixo, 2 colunas esquerda/direita |
| `title="[bold]Ajuda[/bold]"` | — | Título em negrito no topo do painel |

> ✅ **Boa prática**: Definir elementos de UI reutilizáveis no escopo global facilita manutenção e garante consistência visual.

---

## 🔹 4. Funções Auxiliares (NOVIDADE v2.0)

### 4.1. `check_api_connection(base_url, timeout)`

```python
def check_api_connection(base_url: str, timeout: int = CONNECTION_TIMEOUT) -> tuple[bool, str]:
    """
    Verifica se a API está disponível e respondendo.
    
    Returns:
        tuple[bool, str]: (sucesso, mensagem descritiva)
    """
```

#### Fluxo da função:

```python
base_url = base_url.rstrip('/')  # Normaliza URL

for endpoint in HEALTH_ENDPOINTS:  # Testa cada endpoint
    url = f"{base_url}{endpoint}"
    try:
        response = requests.get(url, timeout=timeout)
        # ✅ QUALQUER resposta HTTP = servidor está "up"
        return True, f"Conectado via {endpoint} (HTTP {response.status_code})"
    except requests.exceptions.ConnectionError:
        continue  # ❌ Tenta próximo endpoint
    except requests.exceptions.Timeout:
        continue  # ❌ Tenta próximo endpoint
    except requests.exceptions.RequestException as e:
        # ⚠️ Outros erros (SSL, redirect) - servidor pode estar up
        return True, f"Servidor respondendo (erro esperado: {type(e).__name__})"

# ❌ Nenhum endpoint respondeu
return False, f"Não foi possível conectar em {base_url}"
```

#### Por que considerar 4xx/5xx como "conectado"?

| Status HTTP | Interpretação | Razão |
|------------|--------------|--------|
| `200` | ✅ Online | Endpoint de health retornou OK |
| `400/401/403` | ✅ Online | Servidor responde, mas requisição inválida/sem auth |
| `404` | ✅ Online | Endpoint específico não existe, mas servidor está up |
| `405` | ✅ Online | Método não permitido (ex: GET em endpoint POST-only) |
| `500/502/503` | ✅ Online | Erro interno, mas servidor está respondendo |
| *Timeout/ConnectionError* | ❌ Offline | Servidor não respondeu dentro do timeout |

> 🎯 **Objetivo**: Diferenciar "servidor offline" de "erro de aplicação".

---

### 4.2. `format_url(ip, port)`

```python
def format_url(ip: str, port: int) -> str:
    """Formata URL completa a partir de IP e porta."""
    if ip.startswith(('http://', 'https://')):
        return ip.rstrip('/')  # Já é URL completa
    return f"http://{ip}:{port}"  # Monta URL com protocolo + IP + porta
```

#### Exemplos de uso:

```python
format_url("192.168.1.100", 8000)
# → "http://192.168.1.100:8000"

format_url("https://api.exemplo.com", 8000)
# → "https://api.exemplo.com"  (porta ignorada)

format_url("localhost", 8080)
# → "http://localhost:8080"
```

> ✅ **Benefício**: Permite passar URL completa como argumento sem duplicar protocolo ou porta.

---

## 🔹 5. Classe `ChatClient` - Estrutura Geral Atualizada

```python
class ChatClient:
    def __init__(self, ip_servidor: str, porta: int = DEFAULT_PORT):
        self.console = Console()
        
        # Configura URL base: prioriza variável de ambiente
        self.base_url = os.getenv("API_URL", format_url(ip_servidor, porta))
        
        self.session_id = str(uuid.uuid4())
        self._connected = False  # 🆕 Flag de estado de conexão
```

### Método `__init__` (Construtor) - Atualizações v2.0:

| Atributo | Descrição | Mudança v2.0 |
|----------|-----------|-------------|
| `self.console` | Instância do `Console` do Rich | — |
| `self.base_url` | URL base da API | 🆕 Usa `format_url()` para montagem inteligente |
| `self.session_id` | UUID único para sessão | — |
| `self._connected` | Flag interna de estado de conexão | 🆕 Nova: controla se chat pode ser iniciado |

> 🔑 **Princípio**: Conexão deve ser verificada explicitamente antes de permitir interação.

---

## 🔹 6. Método `verify_connection()` (NOVIDADE v2.0)

```python
def verify_connection(self, show_progress: bool = True) -> bool:
    """
    Verifica a conexão com a API backend.
    
    Args:
        show_progress: Exibe spinner de carregamento durante verificação
        
    Returns:
        bool: True se conectado com sucesso, False caso contrário
    """
```

### 6.1. Exibição de Spinner com Rich Progress

```python
if show_progress:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=self.console,
        transient=True
    ) as progress:
        task = progress.add_task(
            f"[cyan]Verificando conexão com {self.base_url}...", 
            total=None  # Spinner infinito
        )
        success, message = check_api_connection(self.base_url)
        progress.update(task, completed=True)  # Finaliza spinner
else:
    success, message = check_api_connection(self.base_url)  # Sem UI
```

#### Componentes do `Progress`:

| Componente | Função |
|------------|--------|
| `SpinnerColumn()` | Exibe animação giratória (padrão: "dots") |
| `TextColumn("{task.description}")` | Mostra mensagem dinâmica da tarefa |
| `transient=True` | Remove spinner da tela após conclusão |
| `total=None` | Cria spinner infinito (sem barra de progresso) |

**Resultado visual:**
```
⠋ Verificando conexão com http://192.168.1.100:8000...
```

---

### 6.2. Painel de Sucesso de Conexão

```python
if success:
    self.console.print(
        Panel(
            f"[green]✅ {message}[/green]\n"
            f"[dim]Session ID: {self.session_id}[/dim]",
            title="[bold]Conexão Estabelecida[/bold]",
            border_style="green",
            padding=(1, 2)
        )
    )
    time.sleep(0.8)  # Pausa para usuário ver a mensagem
```

**Renderização:**
```
┌─ Conexão Estabelecida ─────────────┐
│                                    │
│  ✅ Conectado via /health (HTTP 200)│
│  Session ID: a1b2c3d4-e5f6-...    │
│                                    │
└────────────────────────────────────┘
```

---

### 6.3. Painel de Erro de Conexão com Diagnóstico

```python
else:
    self.console.print(
        Panel(
            f"[red]❌ {message}[/red]\n\n"
            "[bold]Possíveis causas:[/bold]\n"
            "• Servidor não está rodando\n"
            "• IP ou porta incorretos\n"
            "• Firewall bloqueando a conexão\n"
            "• Rede indisponível\n\n"
            "[yellow]Sugestão:[/yellow] Verifique se o backend está ativo "
            "e tente novamente.",
            title="[bold]Erro de Conexão[/bold]",
            border_style="red",
            padding=(1, 2)
        )
    )
```

**Renderização:**
```
┌─ Erro de Conexão ──────────────────┐
│                                    │
│  ❌ Não foi possível conectar em...│
│                                    │
│  Possíveis causas:                 │
│  • Servidor não está rodando       │
│  • IP ou porta incorretos          │
│  • Firewall bloqueando             │
│  • Rede indisponível               │
│                                    │
│  Sugestão: Verifique se o backend  │
│  está ativo e tente novamente.    │
│                                    │
└────────────────────────────────────┘
```

> 💡 **UX Profissional**: Em vez de apenas "erro", oferece diagnóstico guiado para troubleshooting.

---

## 🔹 7. Método `start_chat()` - Loop Principal Atualizado

```python
def start_chat(self):
    """
    Inicia a sessão interativa de chat.
    
    Pré-requisito: verify_connection() deve ter sido chamado e retornado True.
    """
```

### 7.1. Verificação Prévia de Conexão (Fail-Fast)

```python
if not self._connected:
    self.console.print(
        "[red]⚠️  Chat não pode ser iniciado sem conexão com a API.[/red]"
    )
    return  # ⛔ Interrompe execução
```

> ✅ **Fail-fast**: Evita que o usuário entre em um chat que inevitavelmente falhará.

---

### 7.2. Banner Inicial com Painel Reutilizável

```python
self.console.print(PAINEL_BANNER)  # Usa constante global definida anteriormente
```

**Renderização:**
```
┌─────────────────────────────────┐
│                                 │
│  🤖 Gemini ChatBot              │
│  Digite 'sair' para encerrar...│
│                                 │
└─────────────────────────────────┘
```

---

### 7.3. Loop de Interação com Tratamento de Erros Aprimorado

```python
while True:
    try:
        user_input = self.console.input("\n[bold yellow]Você:[/bold yellow] ").strip()
        cmd = user_input.lower()
        
        # Processa comandos especiais
        if cmd in ['sair', 'exit', 'quit']:
            self.console.print("[green]Até logo! 👋[/green]")
            break
        elif cmd in ['ajuda', 'help']:
            self.console.print(PAINEL_AJUDA)  # 🆕 Usa painel pré-definido
            continue
        elif cmd == 'historico':
            self._show_history()
            continue
        elif not user_input:
            continue
        
        # Envia mensagem com spinner atualizado
        with self.console.status(
            "[bold green]🤔 Processando sua mensagem...[/bold green]", 
            spinner="dots"
        ):
            response = self._send_message(user_input)
        
        self._display_response(response)
        
    except KeyboardInterrupt:
        self.console.print("\n[red]⚠️  Interrompido pelo usuário (Ctrl+C)[/red]")
        break
        
    except requests.exceptions.ConnectionError:  # 🆕 Tratamento específico
        self.console.print(
            Panel(
                "[red]❌ Conexão perdida com o servidor.[/red]\n"
                "Verifique sua conexão de rede e tente novamente.",
                border_style="red"
            )
        )
        break
        
    except Exception as e:
        self.console.print(f"[red]❌ Erro: {str(e)}[/red]")
        # 🆕 Oferece opção de continuar após erro genérico
        cont = self.console.input("[yellow]Continuar tentando? (s/n): [/yellow]").strip().lower()
        if cont not in ['s', 'sim', 'y', 'yes']:
            break
```

#### Novidades no tratamento de erros:

| Exceção | Ação v2.0 | Benefício |
|---------|-----------|-----------|
| `requests.exceptions.ConnectionError` | Painel específico + `break` | Diferencia perda de conexão de outros erros |
| `Exception` genérica | Exibe erro + pergunta se quer continuar | Permite recuperação sem reiniciar aplicação |
| `KeyboardInterrupt` | Mensagem com `(Ctrl+C)` explícito | Clareza sobre causa da interrupção |

---

## 🔹 8. Método `_send_message()` - Comunicação com API Atualizada

```python
def _send_message(self, message: str) -> dict:
    payload = {
        "message": message,
        "session_id": self.session_id
    }
    
    response = requests.post(
        f"{self.base_url}/chat",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60  # 🆕 Timeout maior para respostas longas de LLM
    )
    
    if response.status_code != 200:
        raise Exception(
            f"API retornou erro {response.status_code}: {response.text[:200]}"  # 🆕 Trunca mensagem
        )
    
    return response.json()
```

### Atualizações v2.0:

| Mudança | Código Anterior | Código v2.0 | Benefício |
|---------|----------------|-------------|-----------|
| **Timeout configurável** | Não especificado | `timeout=60` | Evita travamento em respostas longas de LLM |
| **Truncamento de erro** | `response.text` | `response.text[:200]` | Previne logs excessivos com respostas de erro grandes |
| **Mensagem de erro detalhada** | `"Erro na API: {text}"` | `"API retornou erro {code}: {text[:200]}"` | Facilita debug incluindo status HTTP |

---

## 🔹 9. Método `_display_response()` - Exibição da Resposta Atualizada

```python
def _display_response(self, response: dict):
    response_text = response.get("response", "⚠️ Sem conteúdo na resposta")  # 🆕 Mensagem mais clara
    tokens_used = response.get("tokens_used", 0)
    
    md = Markdown(response_text)
    
    self.console.print(
        Panel(
            md,
            title="[bold green]🤖 Assistente[/bold green]",
            title_align="left",
            border_style="blue",
            subtitle=f"[dim]🔢 Tokens: {tokens_used}[/dim]" if tokens_used else None,  # 🆕 Condicional
            padding=(1, 2)  # 🆕 Padding consistente
        )
    )
```

### Atualizações v2.0:

| Elemento | Mudança | Benefício |
|----------|---------|-----------|
| `response_text` fallback | `"Sem resposta"` → `"⚠️ Sem conteúdo na resposta"` | Mensagem mais amigável e informativa |
| `subtitle` condicional | Sempre exibia | 🆕 Só exibe se `tokens_used > 0`, evita clutter visual |
| `padding=(1, 2)` | Não especificado | 🆕 Espaçamento interno consistente com outros painéis |

---

## 🔹 10. Método `_show_history()` - Histórico Aprimorado

```python
def _show_history(self):
    try:
        with self.console.status("[cyan]📦 Carregando histórico...[/cyan]"):  # 🆕 Spinner específico
            response = requests.get(
                f"{self.base_url}/conversations/{self.session_id}",
                timeout=30  # 🆕 Timeout dedicado
            )
        
        if response.status_code == 200:
            conversation = response.json()
            messages = conversation.get("messages", [])
            
            if not messages:
                self.console.print("[yellow]ℹ️  Nenhuma mensagem no histórico.[/yellow]")
                return
            
            self.console.print("\n[bold cyan]📜 Histórico da Conversa:[/bold cyan]")
            self.console.print(f"[dim]Total: {len(messages)} mensagem(s)[/dim]\n")  # 🆕 Contagem
            
            for i, msg in enumerate(messages, 1):  # 🆕 Numeração sequencial
                role_icon = "👤" if msg["role"] == "user" else "🤖"
                role_label = "[bold yellow]Você[/bold yellow]" if msg["role"] == "user" else "[bold green]Assistente[/bold green]"
                
                self.console.print(f"[dim]#{i}[/dim] {role_icon} {role_label}:")  # 🆕 Número + emoji
                self.console.print(f"  {msg['content']}")
                if msg.get("timestamp"):
                    self.console.print(f"  [dim]🕐 {msg['timestamp']}[/dim]")  # 🆕 Emoji de relógio
                self.console.print()  # Linha em branco entre mensagens
                    
        else:
            self.console.print(
                f"[yellow]⚠️  Servidor retornou {response.status_code} - Histórico indisponível[/yellow]"  # 🆕 Status HTTP explícito
            )
                
    except requests.exceptions.ConnectionError:
        self.console.print("[red]❌ Erro: Não foi possível conectar ao servidor.[/red]")
    except Exception as e:
        self.console.print(f"[red]❌ Erro ao buscar histórico: {type(e).__name__} - {str(e)}[/red]")  # 🆕 Tipo da exceção
```

### Melhorias de UX no histórico:

| Feature | Implementação | Benefício |
|---------|--------------|-----------|
| **Spinner específico** | `"[cyan]📦 Carregando histórico...[/cyan]"` | Feedback claro sobre operação em andamento |
| **Contagem de mensagens** | `f"Total: {len(messages)} mensagem(s)"` | Contexto imediato sobre volume do histórico |
| **Numeração sequencial** | `enumerate(messages, 1)` + `#{i}` | Facilita referência a mensagens específicas |
| **Labels coloridos por role** | `"[bold yellow]Você[/bold yellow]"` vs `"[bold green]Assistente[/bold green]"` | Distinção visual rápida entre usuário e assistente |
| **Emoji de timestamp** | `🕐 {timestamp}` | Reconhecimento visual imediato de metadado temporal |
| **Status HTTP no erro** | `"Servidor retornou {code}"` | Debug mais preciso para desenvolvedores |
| **Tipo da exceção no erro** | `{type(e).__name__}` | Identificação rápida da categoria do erro |

---

## 🔹 11. Função `print_usage()` (NOVIDADE v2.0)

```python
def print_usage():
    """Exibe mensagem de uso correto do script."""
    console = Console()
    console.print(
        Panel(
            "[bold]Uso correto:[/bold]\n\n"
            "  [cyan]python chat_client.py <IP_DO_SERVIDOR> [PORTA][/cyan]\n\n"
            "[bold]Exemplos:[/bold]\n"
            "  [green]python chat_client.py 127.0.0.1[/green]\n"
            "  [green]python chat_client.py 192.168.1.100 8000[/green]\n"
            "  [green]API_URL=https://api.com python chat_client.py ignored[/green]\n\n"
            "[bold]Variáveis de ambiente:[/bold]\n"
            "  [dim]API_URL[/dim] - URL completa da API (sobrescreve IP/porta)",
            title="[red]❌ Parâmetros insuficientes[/red]",
            border_style="red",
            padding=(1, 2)
        )
    )
```

### Características:

| Elemento | Propósito |
|----------|-----------|
| `Panel` com `border_style="red"` | Destaca visualmente que é um erro |
| `title="[red]❌ Parâmetros insuficientes[/red]"` | Mensagem clara no topo do painel |
| Exemplos em `[green]` | Facilita cópia/cola de comandos válidos |
| Explicação de `API_URL` | Documenta variável de ambiente para usuários avançados |

**Renderização:**
```
┌─ ❌ Parâmetros insuficientes ──────┐
│                                    │
│  Uso correto:                      │
│    python chat_client.py <IP> [PORTA]│
│                                    │
│  Exemplos:                         │
│    python chat_client.py 127.0.0.1 │
│    python chat_client.py 192.168...│
│    API_URL=https://... python ...  │
│                                    │
│  Variáveis de ambiente:            │
│    API_URL - URL completa da API   │
│                                    │
└────────────────────────────────────┘
```

> ✅ **UX Profissional**: Em vez de `print("Erro")`, oferece ajuda contextual para corrigir o problema.

---

## 🔹 12. Função `main()` - Orquestração Atualizada

```python
def main():
    """Função principal: orquestra inicialização e execução."""
    console = Console()
    
    # Parse de argumentos
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)  # 🆕 Código semântico para erro de argumento
    
    ip_servidor = sys.argv[1]
    porta = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    
    # Banner de inicialização com diagnóstico
    console.print(
        Panel(
            f"[bold cyan]🚀 Inicializando ChatClient TUI[/bold cyan]\n"
            f"[dim]Servidor: {ip_servidor}:{porta}[/dim]\n"
            f"[dim]API_URL env: {os.getenv('API_URL', 'não definido')}[/dim]",
            border_style="cyan",
            padding=(1, 2)
        )
    )
    
    try:
        client = ChatClient(ip_servidor, porta)
        
        # 🔌 VERIFICA CONEXÃO ANTES DE PROSSEGUIR (NOVIDADE v2.0)
        if not client.verify_connection(show_progress=True):
            console.print("\n[yellow]💡 Dica: Certifique-se que o servidor backend está rodando.[/yellow]")
            sys.exit(2)  # 🆕 Código semântico para falha de conexão
        
        # ✅ Conexão bem-sucedida: inicia chat
        client.start_chat()
        
    except KeyboardInterrupt:
        console.print("\n[red]⚠️  Encerramento forçado pelo usuário.[/red]")
        sys.exit(130)  # 🆕 Código padrão POSIX para SIGINT
    except Exception as e:
        console.print(f"\n[red]❌ Erro inesperado: {type(e).__name__}: {str(e)}[/red]")
        sys.exit(1)  # 🆕 Código semântico para erro geral
```

### Fluxo da função `main()`:

```
1️⃣ Parse de argumentos
   ├─ Se < 2 argumentos → print_usage() + exit(1)
   └─ Extrai ip_servidor e porta (com fallback para DEFAULT_PORT)

2️⃣ Banner de diagnóstico inicial
   └─ Exibe IP:porta + status de API_URL em painel cyan

3️⃣ Instanciação do cliente
   └─ client = ChatClient(ip_servidor, porta)

4️⃣ 🔌 Verificação de conexão (NOVIDADE v2.0)
   ├─ Chama client.verify_connection(show_progress=True)
   ├─ Se False → exibe dica + sys.exit(2)
   └─ Se True → prossegue para chat

5️⃣ Inicia chat interativo
   └─ client.start_chat()

6️⃣ Tratamento de exceções no nível principal
   ├─ KeyboardInterrupt → exit(130)  # SIGINT
   ├─ Exception genérica → exit(1)    # Erro geral
   └─ (Sucesso implícito → exit(0))
```

---

## 🔹 13. Bloco Principal `if __name__ == "__main__"`

```python
if __name__ == "__main__":
    main()
```

### Por que usar `main()` em vez de código direto?

| Benefício | Explicação |
|-----------|-----------|
| **Testabilidade** | Função `main()` pode ser importada e testada isoladamente |
| **Reusabilidade** | Outras partes do código podem chamar `main()` programaticamente |
| **Clareza** | Separa configuração de execução da lógica de negócio |
| **Padrão profissional** | Convenção comum em scripts Python de produção |

---

## 🔹 14. Fluxo Completo da Aplicação v2.0 (Diagrama Atualizado)

```
🚀 python chat_client.py 192.168.1.100 [8000]
│
├─▶ main(): parse argumentos
│   ├─ len(sys.argv) < 2? → print_usage() + exit(1)
│   └─ Extrai ip_servidor, porta (fallback DEFAULT_PORT)
│
├─▶ Banner de diagnóstico inicial (Panel cyan)
│
├─▶ Instancia ChatClient(ip_servidor, porta)
│   ├─ self.base_url = getenv("API_URL") ou format_url(...)
│   ├─ self.session_id = uuid4()
│   └─ self._connected = False
│
├─▶ 🔌 client.verify_connection(show_progress=True) [NOVIDADE v2.0]
│   │
│   ├─ Com spinner: Progress(SpinnerColumn(), TextColumn(...))
│   ├─ Testa HEALTH_ENDPOINTS sequencialmente:
│   │  ├─ GET {base_url}/health → se responder: ✅ conectado
│   │  ├─ GET {base_url}/ → se responder: ✅ conectado
│   │  ├─ GET {base_url}/chat → se responder: ✅ conectado
│   │  └─ GET {base_url}/api/health → se responder: ✅ conectado
│   │
│   ├─ ✅ Sucesso:
│   │  ├─ self._connected = True
│   │  ├─ Exibe Panel verde com endpoint + status HTTP + session_id
│   │  ├─ time.sleep(0.8) para feedback visual
│   │  └─ Retorna True → prossegue para chat
│   │
│   └─ ❌ Falha:
│      ├─ self._connected = False
│      ├─ Exibe Panel vermelho com causas possíveis + sugestão
│      └─ Retorna False → main() exibe dica + sys.exit(2)
│
├─▶ ✅ Conexão OK: client.start_chat()
│   │
│   ├─ Verifica self._connected (fail-fast)
│   ├─ Exibe PAINEL_BANNER
│   │
│   └─ 🔄 while True (loop principal):
│       │
│       ├─ 1. Captura input com prompt colorido
│       │
│       ├─ 2. Processa comandos:
│       │   ├─ 'sair'/'exit'/'quit' → mensagem + break → exit(0)
│       │   ├─ 'ajuda'/'help' → exibe PAINEL_AJUDA + continue
│       │   ├─ 'historico' → _show_history() + continue
│       │   └─ vazio → continue
│       │
│       ├─ 3. Mensagem normal:
│       │   ├─ Spinner "🤔 Processando..."
│       │   ├─ _send_message() com timeout=60s
│       │   ├─ _display_response() com Markdown + tokens (condicional)
│       │   └─ Loop continua
│       │
│       └─ 4. Tratamento de exceções:
│           ├─ KeyboardInterrupt → mensagem + break → exit(130)
│           ├─ ConnectionError → Panel específico + break → exit(1)
│           └─ Exception genérica → erro + prompt (s/n) → decide continuar ou break
│
└─✅ Encerramento limpo com código de saída semântico
```

---

## 🔹 15. Boas Práticas e Padrões Utilizados (Atualizados v2.0)

| Prática | Implementação | Benefício |
|---------|--------------|-----------|
| ✅ **Fail-fast na inicialização** | `verify_connection()` antes de `start_chat()` | Evita chat inútil se API indisponível |
| ✅ **Códigos de saída semânticos** | `exit(0/1/2/130)` com significados claros | Integração com scripts e CI/CD |
| ✅ **Funções auxiliares exportáveis** | `check_api_connection()`, `format_url()` no escopo global | Reuso em testes e automação |
| ✅ **Constantes configuráveis no topo** | `DEFAULT_PORT`, `CONNECTION_TIMEOUT`, `HEALTH_ENDPOINTS` | Ajuste centralizado sem modificar lógica |
| ✅ **Type hints em assinaturas** | `-> tuple[bool, str]`, `message: str` | Melhor autocompletion e verificação estática |
| ✅ **Docstrings completas** | Descrição, Args, Returns, Raises em cada método | Documentação embutida para desenvolvedores |
| ✅ **Painéis pré-definidos reutilizáveis** | `PAINEL_BANNER`, `PAINEL_AJUDA` no escopo global | Consistência visual + manutenção facilitada |
| ✅ **Timeouts diferenciados por operação** | `5s` (health), `30s` (histórico), `60s` (chat) | Balanceia responsividade e tolerância a latência |
| ✅ **Truncamento seguro de mensagens de erro** | `response.text[:200]` | Previne logs excessivos em produção |
| ✅ **Recuperação opcional após erro** | Prompt `"(s/n)"` permite continuar sem reiniciar | Melhora UX em ambientes instáveis |

---

## 🔹 16. Possíveis Melhorias Futuras (Atualizadas para v2.1+)

```python
# 🔐 Autenticação JWT/OAuth2
headers = {"Authorization": f"Bearer {os.getenv('API_TOKEN')}"}
# → Integrar em _send_message() e _show_history()

# 📡 Streaming de resposta (Server-Sent Events)
for chunk in response.iter_lines():
    # Atualizar painel em tempo real sem esperar resposta completa
# → Requer backend com suporte a streaming

# 📎 Upload de arquivos/anexos
files = {"attachment": open("arquivo.pdf", "rb")}
requests.post(..., files=files)
# → Adicionar comando /anexar ou interface de seleção

# 💾 Cache local de histórico para modo offline
import sqlite3
def _save_local_cache(session_id, messages): ...
# → Sincronização bidirecional com backend

# 🎨 Temas personalizáveis para TUI
THEMES = {"dark": {...}, "light": {...}, "auto": detect_terminal()}
# → Comando /tema ou variável de ambiente RICH_THEME

# 🤖 Suporte a múltiplos modelos de IA
# → Comando /modelo gpt4, /modelo gemini, /modelo local
# → Backend deve suportar parâmetro "model" no payload

# 🔁 Retry automático com backoff exponencial
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
# → Para falhas transitórias de rede em ambientes corporativos

# 📊 Logging estruturado para produção
import logging, json
logger = logging.getLogger(__name__)
logger.info("connection_check", extra={"url": base_url, "success": ok})
# → Integração com ELK, Datadog, CloudWatch
```

---

## 🔹 17. Resumo Visual da Arquitetura v2.0

```
┌─────────────────────┐
│   Terminal (TUI)    │
│  ┌───────────────┐  │
│  │   Rich Console│  │
│  │  • Panels     │  │
│  │  • Markdown   │  │
│  │  • Progress   │  │ ← 🆕 Spinner de conexão
│  │  • Cores      │  │
│  └───────┬───────┘  │
└──────────┼──────────┘
           │ HTTP/JSON
           ▼
┌────────────────────────────┐
│   API Backend              │
│  • GET /health (ou similares) │ ← 🆕 Health check
│  • POST /chat              │
│  • GET /conversations/{id} │
│  • Session management      │
└────────────────────────────┘

Fluxo v2.0:
1. Inicialização → 2. Health Check → 3. [Se OK] Chat Interativo
                          ↓
                  [Se Falha] Diagnóstico + Exit(2)
```

---

> 💡 **Conclusão**: O ChatClient TUI v2.0 evolui significativamente em relação à v1.0 ao adicionar **verificação automática de conexão resiliente**, **feedback visual profissional com Rich Progress**, **códigos de saída semânticos** e **diagnóstico guiado de falhas** — mantendo a simplicidade de um script Python autocontido enquanto oferece experiência de usuário comparável a aplicações web modernas.