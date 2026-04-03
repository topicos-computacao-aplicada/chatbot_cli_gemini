# 📋 Lista de Funcionalidades - ChatClient TUI v2.0

Abaixo está a lista completa de funcionalidades do código atualizado, organizada por categorias, destacando as **novidades da versão 2.0**.

---

## 🔐 Configuração e Inicialização

| Funcionalidade | Descrição | Implementação |
|---------------|-----------|--------------|
| **Configuração dinâmica da URL da API** | Usa variável de ambiente `API_URL` ou monta URL com IP + porta fornecidos | `os.getenv("API_URL", format_url(ip_servidor, porta))` |
| **Formatação inteligente de URL** | Detecta se IP já é URL completa (`http://`/`https://`) e evita duplicação de protocolo/porta | `format_url(ip, port)` |
| **Geração automática de Session ID** | Cria UUID v4 único para identificar a sessão no servidor | `uuid.uuid4()` |
| **Inicialização via linha de comando** | Recebe IP e porta opcional como argumentos (`sys.argv[1]`, `sys.argv[2]`) | `if len(sys.argv) >= 2` |
| **Validação de argumentos com painel Rich** | Exibe painel formatado com instruções de uso se parâmetros insuficientes | `print_usage()` + `Panel` |
| **🆕 Flag de estado de conexão** | Armazena resultado da verificação para controlar fluxo do chat | `self._connected = False` |

---

## 🔌 Verificação de Conexão (NOVIDADE v2.0)

| Funcionalidade | Descrição | Implementação |
|---------------|-----------|--------------|
| **🆕 Health check automático na inicialização** | Verifica conectividade com a API ANTES de iniciar o chat interativo | `client.verify_connection()` no `main()` |
| **🆕 Múltiplos endpoints de health check** | Testa sequencialmente `/health`, `/`, `/chat`, `/api/health` até encontrar resposta | `HEALTH_ENDPOINTS = ["/health", "/", "/chat", "/api/health"]` |
| **🆕 Timeout configurável para conexão** | Evita travamentos em redes lentas ou servidores indisponíveis | `CONNECTION_TIMEOUT = 5` |
| **🆕 Spinner de progresso com Rich Progress** | Exibe animação profissional durante verificação de conexão | `Progress(SpinnerColumn(), TextColumn(...))` |
| **🆕 Painel de sucesso de conexão** | Mostra endpoint utilizado, status HTTP e Session ID em painel verde | `Panel(..., border_style="green")` |
| **🆕 Painel de erro de conexão com diagnóstico** | Lista causas possíveis e sugestões de troubleshooting em painel vermelho | `Panel(..., border_style="red")` |
| **🆕 Função exportável `check_api_connection()`** | Permite reuso em scripts externos e testes automatizados | `def check_api_connection(base_url, timeout) -> tuple[bool, str]` |
| **🆕 Critério resiliente de "conectado"** | Considera servidor "up" se responder com qualquer HTTP status (2xx-5xx), não apenas 200 | `return True, f"Conectado via {endpoint} (HTTP {response.status_code})"` |

---

## 💬 Interface de Chat (TUI)

| Funcionalidade | Descrição | Biblioteca/Recurso |
|---------------|-----------|-------------------|
| **Banner inicial formatado** | Exibe título, emoji e instruções em box com borda e padding | `PAINEL_BANNER = Panel.fit(..., padding=(1,2))` |
| **Prompt de entrada colorido** | Mostra "Você:" em amarelo/negrito antes do input | `console.input("[bold yellow]Você:[/bold yellow] ")` |
| **Spinner de processamento de mensagem** | Animação "dots" enquanto aguarda resposta da API | `console.status(..., spinner="dots")` |
| **Respostas em painéis formatados** | Exibe resposta do assistente em box com título, borda azul e subtítulo de tokens | `Panel(md, title="🤖 Assistente", border_style="blue", subtitle=...)` |
| **Renderização de Markdown** | Formata texto com listas, código, negrito, tabelas no terminal | `rich.markdown.Markdown` |
| **Cores e estilos no terminal** | Texto em negrito, cores (azul, verde, amarelo, vermelho, ciano), texto "dim" | Sintaxe `[tag]...[/tag]` do Rich |
| **Exibição condicional de metadados** | Mostra tokens usados apenas se valor > 0 | `subtitle=f"[dim]🔢 Tokens: {tokens_used}[/dim]" if tokens_used else None` |
| **🆕 Painéis pré-definidos reutilizáveis** | Centraliza configuração visual de banner e ajuda para consistência | `PAINEL_BANNER`, `PAINEL_AJUDA` no escopo global |

---

## 🗣️ Comandos de Texto Disponíveis

| Comando | Sinônimos | Ação |
|---------|-----------|------|
| `sair` | `exit`, `quit` | Encerra o chat com mensagem de despedida "Até logo! 👋" |
| `ajuda` | `help` | Exibe menu de ajuda com comandos e exemplos em painel amarelo |
| `historico` | — | Busca e exibe histórico da conversa no servidor com numeração e timestamps |
| *(entrada vazia)* | — | Ignora e solicita nova entrada sem enviar requisição à API |

> ✅ Comandos são **case-insensitive** (`.lower()`).

---

## 🌐 Comunicação com API REST

| Funcionalidade | Endpoint | Método | Descrição |
|---------------|----------|--------|-----------|
| **Envio de mensagens** | `/chat` | `POST` | Envia `{"message": "...", "session_id": "..."}`, recebe `{"response": "...", "tokens_used": N}` |
| **Busca de histórico** | `/conversations/{session_id}` | `GET` | Recupera lista de mensagens com role, content e timestamp |
| **Payload JSON estruturado** | — | — | Serialização automática via `json=payload` do requests |
| **Validação de status HTTP** | — | — | Lança `Exception` com detalhes se `status_code != 200` |
| **Parse automático de JSON** | — | — | `response.json()` converte resposta para `dict` Python |
| **Headers configurados** | — | — | `Content-Type: application/json` explícito |
| **🆕 Timeouts diferenciados por operação** | — | — | `timeout=60s` (chat), `30s` (histórico), `5s` (health check) |
| **🆕 Truncamento seguro de mensagens de erro** | — | — | `response.text[:200]` para evitar logs excessivos |

---

## 🛡️ Tratamento de Erros e Resiliência

| Tipo de Erro | Tratamento | Feedback ao Usuário |
|-------------|-----------|-------------------|
| `KeyboardInterrupt` (Ctrl+C) | `break` no loop + `sys.exit(130)` | `"[red]⚠️ Interrompido pelo usuário (Ctrl+C)[/red]"` |
| Erro HTTP na API (`status != 200`) | `raise Exception` com detalhes | `"[red]❌ Erro: API retornou erro {code}: {text[:200]}[/red]"` |
| `requests.exceptions.ConnectionError` | Tratamento específico no chat | Painel vermelho: `"❌ Conexão perdida com o servidor"` + sugestão |
| Falha na verificação inicial | `sys.exit(2)` com código semântico | Painel de erro com causas possíveis + dica final |
| Histórico não encontrado (404) | Continua execução normalmente | `"[yellow]⚠️ Servidor retornou {code} - Histórico indisponível[/yellow]"` |
| Campo ausente na resposta JSON | `.get("chave", valor_padrao)` | Usa fallback (`"Sem conteúdo"`, `0`) sem quebrar |
| Exceção genérica não tratada | Oferece opção de continuar ou sair | `"[red]❌ Erro: {mensagem}[/red]"` + prompt `"(s/n): "` |
| **🆕 Falha de conexão durante o chat** | Break no loop + encerramento limpo | Painel específico + `sys.exit(1)` |

---

## 🎨 Experiência do Usuário (UX)

| Funcionalidade | Benefício |
|---------------|-----------|
| **Feedback visual imediato** | Spinners indicam processamento (conexão + mensagem) |
| **Mensagens de erro claras e coloridas** | Texto em vermelho destaca problemas; amarelo para avisos |
| **Formatação consistente com painéis pré-definidos** | UI uniforme em banner, ajuda e respostas |
| **Ajuda contextual acessível** | Comando `ajuda` exibe exemplos sem sair do chat |
| **Encerramento amigável** | Mensagem "Até logo! 👋" e código de saída 0 |
| **Ignora entradas vazias** | Evita requisições desnecessárias à API |
| **🆕 Diagnóstico guiado de falhas de conexão** | Lista causas comuns + sugestão prática para troubleshooting |
| **🆕 Pausa visual pós-conexão** | `time.sleep(0.8)` permite usuário ver confirmação antes do chat |
| **🆕 Recuperação opcional após erro** | Prompt "(s/n)" permite continuar sem reiniciar aplicação |

---

## 🧱 Arquitetura e Boas Práticas de Código

| Prática | Implementação | Benefício |
|---------|--------------|-----------|
| **Encapsulamento em classe** | `class ChatClient` | Código organizado, testável e reutilizável |
| **Métodos privados com prefixo underscore** | `_send_message()`, `_display_response()`, etc. | Indica API interna, não para uso externo |
| **Separação de responsabilidades** | Cada método/função tem propósito único | Facilita testes unitários e manutenção |
| **Funções auxiliares exportáveis** | `check_api_connection()`, `format_url()`, `print_usage()` no escopo global | Reuso em scripts, testes e integrações |
| **Constantes globais configuráveis** | `DEFAULT_PORT`, `CONNECTION_TIMEOUT`, `HEALTH_ENDPOINTS` | Ajuste centralizado sem modificar lógica |
| **Type hints em assinaturas** | `-> tuple[bool, str]`, `message: str` | Melhor autocompletion e verificação estática |
| **Docstrings completas** | Descrição, Args, Returns, Raises em cada método | Documentação embutida para desenvolvedores |
| **Uso de f-strings** | `f"{self.base_url}/chat"` | Código mais legível que concatenação `+` |
| **Acesso seguro a dicionários** | `response.get("chave", default)` | Previne `KeyError` em respostas parciais |
| **Context managers para recursos** | `with console.status(...)`, `with Progress(...)` | Liberação automática de recursos |
| **🆕 Separação clara entre lógica e UI** | Funções de conexão não dependem de Console; métodos de UI não fazem HTTP | Testabilidade e flexibilidade aumentadas |

---

## 🔧 Flexibilidade e Configuração

| Recurso | Como Usar | Exemplo |
|---------|-----------|---------|
| **Variável de ambiente `API_URL`** | Define URL completa da API (sobrescreve argumentos) | `API_URL=https://api.exemplo.com:8443 python chat_client.py ignored` |
| **IP via argumento posicional** | Define servidor na execução | `python chat_client.py 192.168.1.100` |
| **Porta customizada via argumento** | Define porta não-padrão | `python chat_client.py 192.168.1.100 8080` |
| **URL completa como argumento** | Ignora porta se protocolo já presente | `python chat_client.py https://api.segura.com` |
| **🆕 Timeout de conexão ajustável** | Modificar constante no topo do arquivo | `CONNECTION_TIMEOUT = 10` |
| **🆕 Endpoints de health check personalizáveis** | Editar lista `HEALTH_ENDPOINTS` conforme backend | `HEALTH_ENDPOINTS = ["/ping", "/status"]` |
| **🆕 Spinner de conexão opcional** | Chamar `verify_connection(show_progress=False)` para scripts | `if client.verify_connection(show_progress=False): ...` |

---

## 📊 Métricas e Informações Exibidas

| Dado | Origem | Local de Exibição |
|------|--------|------------------|
| Session ID | `uuid.uuid4()` | Painel de conexão estabelecida + banner inicial |
| Tokens usados | Resposta da API (`tokens_used`) | Subtitle do painel de resposta (condicional) |
| Timestamp das mensagens | Resposta do histórico (`timestamp`) | Abaixo de cada mensagem no histórico com emoji 🕐 |
| Role da mensagem | Campo `role` da API | Avatar/emoji (👤 ou 🤖) + label colorido no histórico |
| **🆕 Status HTTP do health check** | Resposta do endpoint testado | Painel de sucesso: `"Conectado via /health (HTTP 200)"` |
| **🆕 Contagem de mensagens no histórico** | `len(messages)` da resposta | `"Total: N mensagem(s)"` antes da lista |
| **🆕 Número sequencial das mensagens** | Enumeração no loop de exibição | `"#1 👤 Você:"`, `"#2 🤖 Assistente:"` |

---

## 🔄 Fluxo de Execução Atualizado (v2.0)

```
1️⃣  Inicialização com verificação prévia
   ├─ Parse de argumentos (IP + porta opcional)
   ├─ Banner de inicialização com diagnóstico
   ├─ Instanciação do ChatClient
   ├─ 🔌 verify_connection(show_progress=True)
   │  ├─ Testa HEALTH_ENDPOINTS sequencialmente
   │  ├─ Exibe spinner Rich Progress
   │  ├─ ✅ Sucesso: painel verde + session_id + sleep(0.8)
   │  └─ ❌ Falha: painel vermelho + causas + sys.exit(2)
   └─ Prossegue apenas se conectado

2️⃣  Loop Principal (start_chat) - PRÉ-REQUISITO: _connected == True
   ├─ Exibe PAINEL_BANNER
   ├─ 🔄 while True:
   │  ├─ Captura input do usuário com prompt colorido
   │  ├─ Processa comandos especiais (sair/ajuda/historico/vazio)
   │  ├─ Mensagem normal:
   │  │  ├─ Spinner "🤔 Processando..."
   │  │  ├─ _send_message() com timeout=60s
   │  │  ├─ _display_response() com Markdown + tokens
   │  │  └─ Append ao histórico local (implícito via API)
   │  └─ Tratamento de exceções:
   │     ├─ KeyboardInterrupt → mensagem + break + exit(130)
   │     ├─ ConnectionError → painel específico + break + exit(1)
   │     └─ Exception genérica → erro + prompt continuar/sair
   └─ Encerramento limpo com "Até logo! 👋" + exit(0)

3️⃣  Funcionalidades Auxiliares
   ├─ check_api_connection(): Health check resiliente e exportável
   ├─ format_url(): Normalização inteligente de URL
   ├─ print_usage(): Ajuda formatada para erros de argumento
   ├─ _send_message(): POST /chat com validação e timeout
   ├─ _display_response(): Renderização Rich + Markdown
   ├─ _show_help(): Exibe PAINEL_AJUDA pré-definido
   └─ _show_history(): GET histórico + exibição numerada com timestamps
```

---

## 📦 Dependências Externas

| Pacote | Versão Mínima | Propósito | Notas v2.0 |
|--------|--------------|-----------|-----------|
| `requests` | ≥ 2.28.0 | Requisições HTTP para a API REST | Inalterado |
| `rich` | ≥ 13.0.0 | Interface de terminal formatada | **Atualizado**: requer `rich.progress` para spinner de conexão |

> ✅ Instalação: `pip install "requests>=2.28.0" "rich>=13.0.0"`  
> ✅ Via uv: `uv pip install requests rich`

---

## 🎯 Casos de Uso Habilitados (Atualizados)

| Cenário | Como o código atende |
|---------|---------------------|
| **Desenvolvimento local** | IP via argumento + fallback localhost + health check automático |
| **Deploy em servidor remoto** | Variável `API_URL` + múltiplos endpoints de health + diagnóstico de falha |
| **Sessões múltiplas isoladas** | UUID único por instância + session_id exibido para auditoria |
| **Debug de API** | Mensagens de erro com status HTTP + truncamento seguro + códigos de saída semânticos |
| **Scripts de automação/CI** | Funções exportáveis (`check_api_connection`) + exit codes (0/1/2/130) + `show_progress=False` |
| **Usuários finais não-técnicos** | Comandos intuitivos + ajuda embutida + diagnóstico guiado de conexão + feedback visual claro |
| **Ambientes com rede instável** | Timeouts configuráveis + retry implícito via múltiplos endpoints + recuperação opcional pós-erro |

---

## 🚀 Possíveis Extensões Futuras (Atualizadas)

```python
# 🔐 Autenticação JWT/OAuth2
headers = {"Authorization": f"Bearer {os.getenv('API_TOKEN')}"}
# → Integrar em _send_message() e _show_history()

# 📡 Streaming de resposta (Server-Sent Events / WebSockets)
for chunk in response.iter_lines():
    # Atualizar painel em tempo real
# → Requer backend com suporte a streaming

# 📎 Upload de arquivos/anexos
files = {"attachment": open("arquivo.pdf", "rb")}
requests.post(..., files=files)
# → Adicionar comando /anexar ou interface de seleção

# 💾 Cache local de histórico para modo offline
import sqlite3, json
def _save_local_cache(session_id, messages): ...
# → Sincronização bidirecional com backend

# 🎨 Temas personalizáveis para TUI
THEMES = {"dark": {...}, "light": {...}, "auto": detect_terminal()}
# → Comando /tema ou variável de ambiente RICH_THEME

# 🤖 Suporte a múltiplos modelos de IA
# → Comando /modelo gpt4, /modelo gemini, /modelo local
# → Backend deve suportar parâmetro "model" no payload

# ⚡ Comandos slash estilo Discord
# → /reset (nova sessão), /export txt, /tokens (estatísticas)
# → Parser simples de comandos com prefixo "/"

# 🔁 Retry automático com backoff exponencial
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
# → Para falhas transitórias de rede em ambientes corporativos

# 📊 Logging estruturado para produção
import logging, json
logger = logging.getLogger(__name__)
logger.info("connection_check", extra={"url": base_url, "success": ok})
# → Integração com ELK, Datadog, CloudWatch

# 🧪 Testes unitários automatizados
# → Mock de requests para testar check_api_connection()
# → Testes de integração com backend de teste em CI/CD
```

---

## 🔢 Códigos de Saída Semânticos (NOVIDADE v2.0)

| Código | Significado | Quando Ocorre | Uso em Automação |
|--------|-------------|--------------|-----------------|
| `0` | ✅ Sucesso | Chat encerrado normalmente pelo usuário (`sair`) | `if [ $? -eq 0 ]; then echo "OK"; fi` |
| `1` | ❌ Erro geral | Parâmetros inválidos, exceção não tratada, erro durante chat | `if [ $? -eq 1 ]; then alert_error; fi` |
| `2` | 🔌 Conexão falhou | `verify_connection()` retornou `False` na inicialização | `if [ $? -eq 2 ]; then restart_backend; fi` |
| `130` | ⚠️ Interrupt | Usuário pressionou `Ctrl+C` (SIGINT) | `if [ $? -eq 130 ]; then log_user_exit; fi` |

> 💡 **Dica**: Use `echo $?` no terminal ou `$?` em scripts bash para capturar o código de saída e implementar lógica condicional.

---

> 💡 **Resumo em uma frase**: O ChatClient TUI v2.0 combina uma interface de terminal rica (via Rich 13+) com **verificação automática de conexão resiliente**, comunicação robusta à API REST, tratamento granular de erros e códigos de saída semânticos — oferecendo experiência profissional para usuários finais e integrabilidade para automação, tudo em um script Python autocontido e bem estruturado.