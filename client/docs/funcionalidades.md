# 📋 Lista de Funcionalidades - ChatClient TUI

Abaixo está a lista completa de funcionalidades do código, organizada por categorias:

## 🔐 Configuração e Inicialização

| Funcionalidade | Descrição | Implementação |
|---------------|-----------|--------------|
| **Configuração dinâmica da URL da API** | Usa variável de ambiente `API_URL` ou monta URL com IP fornecido | `os.getenv("API_URL", f"http://{ip_servidor}:8000")` |
| **Geração automática de Session ID** | Cria UUID único para identificar a sessão no servidor | `uuid.uuid4()` |
| **Inicialização via linha de comando** | Recebe IP do servidor como argumento (`sys.argv[1]`) | `if len(sys.argv) > 1` |
| **Validação de argumentos** | Exibe mensagem de erro se IP não for fornecido | `print("Por favor forneça o IP do servidor")` |


## 💬 Interface de Chat (TUI)

| Funcionalidade | Descrição | Biblioteca/Recurso |
|---------------|-----------|-------------------|
| **Banner inicial formatado** | Exibe título, emoji e ID da sessão em box com borda | `rich.panel.Panel` |
| **Prompt de entrada colorido** | Mostra "Você:" em amarelo/negrito antes do input | `rich.console.Console.input()` |
| **Spinner de carregamento** | Animação "dots" enquanto aguarda resposta da API | `console.status(..., spinner="dots")` |
| **Respostas em painéis formatados** | Exibe resposta do assistente em box com título, borda e subtítulo | `Panel` + `Markdown` |
| **Renderização de Markdown** | Formata texto com listas, código, negrito, etc. no terminal | `rich.markdown.Markdown` |
| **Cores e estilos no terminal** | Texto em negrito, cores (azul, verde, amarelo, vermelho), texto "dim" | Sintaxe `[tag]...[/tag]` do Rich |
| **Exibição de metadados** | Mostra quantidade de tokens usados na resposta | `subtitle` do Panel |


## 🗣️ Comandos de Texto Disponíveis

| Comando | Sinônimos | Ação |
|---------|-----------|------|
| `sair` | `exit`, `quit` | Encerra o chat com mensagem de despedida |
| `ajuda` | `help` | Exibe menu de ajuda com comandos e exemplos |
| `historico` | — | Busca e exibe histórico da conversa no servidor |
| *(entrada vazia)* | — | Ignora e solicita nova entrada |

> ✅ Comandos são **case-insensitive** (`.lower()`).


## 🌐 Comunicação com API REST

| Funcionalidade | Endpoint | Método | Descrição |
|---------------|----------|--------|-----------|
| **Envio de mensagens** | `/chat` | `POST` | Envia mensagem + session_id, recebe resposta + tokens |
| **Busca de histórico** | `/conversations/{session_id}` | `GET` | Recupera lista de mensagens da sessão atual |
| **Payload JSON estruturado** | — | — | `{"message": "...", "session_id": "..."}` |
| **Validação de status HTTP** | — | — | Lança exceção se `status_code != 200` |
| **Parse automático de JSON** | — | — | `response.json()` converte resposta para `dict` |
| **Headers configurados** | — | — | `Content-Type: application/json` |


## 🛡️ Tratamento de Erros e Resiliência

| Tipo de Erro | Tratamento | Feedback ao Usuário |
|-------------|-----------|-------------------|
| `KeyboardInterrupt` (Ctrl+C) | `break` no loop | `"Interrompido pelo usuário"` em vermelho |
| Erro HTTP na API (`status != 200`) | `raise Exception` | `"Erro na API: {response.text}"` |
| Erro de rede/timeout | `except Exception` genérico | `"Erro: {mensagem}"` em vermelho |
| Histórico não encontrado | Verifica `status_code` | `"Nenhum histórico encontrado"` em amarelo |
| Campo ausente na resposta JSON | `.get("chave", valor_padrao)` | Usa valor fallback sem quebrar |


## 🎨 Experiência do Usuário (UX)

| Funcionalidade | Benefício |
|---------------|-----------|
| **Feedback visual imediato** | Spinner indica que o sistema está processando |
| **Mensagens de erro claras** | Texto em vermelho destaca problemas |
| **Formatação consistente** | Painéis padronizados para usuário e assistente |
| **Ajuda contextual** | Comando `ajuda` mostra exemplos de uso |
| **Encerramento amigável** | Mensagem "Até logo! 👋" ao sair |
| **Ignora entradas vazias** | Evita requisições desnecessárias à API |


## 🧱 Arquitetura e Boas Práticas de Código

| Prática | Implementação | Benefício |
|---------|--------------|-----------|
| **Encapsulamento em classe** | `class ChatClient` | Código organizado e reutilizável |
| **Métodos privados** | `_send_message()`, `_display_response()`, etc. | Indica API interna, não para uso externo |
| **Separação de responsabilidades** | Cada método faz uma coisa específica | Facilita testes e manutenção |
| **Uso de f-strings** | `f"{self.base_url}/chat"` | Código mais legível que concatenação |
| **Acesso seguro a dicionários** | `response.get("chave", default)` | Previne `KeyError` |
| **Context manager para spinner** | `with console.status(...)` | Recursos liberados automaticamente |
| **Docstrings em métodos** | `"""Descrição"""` | Documentação embutida para desenvolvedores |


## 🔧 Flexibilidade e Configuração

| Recurso | Como Usar | Exemplo |
|---------|-----------|---------|
| **Variável de ambiente `API_URL`** | Define URL completa da API | `API_URL=https://api.exemplo.com python chat_client.py ignored` |
| **IP via argumento** | Define servidor na execução | `python chat_client.py 192.168.1.100` |
| **Porta padrão 8000** | Montada automaticamente se não usar `API_URL` | `http://{ip}:8000` |
| **Session ID por instância** | Cada execução gera UUID único | Isolamento de conversas |

## 📊 Métricas e Informações Exibidas

| Dado | Origem | Local de Exibição |
|------|--------|------------------|
| Session ID | `uuid.uuid4()` | Banner inicial |
| Tokens usados | Resposta da API (`tokens_used`) | Subtitle do painel de resposta |
| Timestamp das mensagens | Resposta do histórico (`timestamp`) | Abaixo de cada mensagem no histórico |
| Role da mensagem | Campo `role` da API | Avatar/emoji (👤 ou 🤖) no histórico |


## 🔄 Fluxo de Execução Resumido

```
1️⃣  Inicialização
   ├─ Parse de argumentos
   ├─ Configuração da URL da API
   └─ Geração de session_id

2️⃣  Loop Principal (start_chat)
   ├─ Exibe banner inicial
   ├─ 🔄 while True:
   │  ├─ Captura input do usuário
   │  ├─ Processa comandos especiais (sair/ajuda/historico)
   │  ├─ Envia mensagem para API com spinner
   │  ├─ Exibe resposta formatada em Panel + Markdown
   │  └─ Trata exceções (Ctrl+C, erros de rede/API)
   └─ Encerramento limpo

3️⃣  Funcionalidades Auxiliares
   ├─ _send_message(): POST /chat
   ├─ _display_response(): Renderiza resposta com formatação
   ├─ _show_help(): Menu de ajuda
   └─ _show_history(): GET /conversations/{id}
```

## 📦 Dependências Externas

| Pacote | Versão Mínima (sugerida) | Propósito |
|--------|-------------------------|-----------|
| `requests` | ≥ 2.28.0 | Requisições HTTP para a API REST |
| `rich` | ≥ 12.0.0 | Interface de terminal formatada (cores, panels, markdown) |

> ✅ Ambas disponíveis no PyPI: `pip install requests rich`


## 🎯 Casos de Uso Habilitados

| Cenário | Como o código atende |
|---------|---------------------|
| **Desenvolvimento local** | IP via argumento + fallback para localhost |
| **Deploy em servidor remoto** | Variável de ambiente `API_URL` para configuração flexível |
| **Sessões múltiplas isoladas** | UUID único por instância do cliente |
| **Debug de API** | Mensagens de erro detalhadas da resposta HTTP |
| **Uso por usuários finais** | Comandos intuitivos + ajuda embutida + feedback visual |
| **Integração em scripts** | Classe pode ser importada e usada programaticamente |

## 🚀 Possíveis Extensões Futuras

```python
# 1. Autenticação JWT
headers = {"Authorization": f"Bearer {os.getenv('API_TOKEN')}"}

# 2. Timeout configurável
requests.post(..., timeout=30)

# 3. Retry automático para falhas de rede
from urllib3.util.retry import Retry

# 4. Histórico local em cache
import json, pathlib
def _save_cache(session_id, messages): ...

# 5. Streaming de resposta (Server-Sent Events)
for chunk in response.iter_lines(): ...

# 6. Upload de arquivos/anexos
files = {"attachment": open("arquivo.pdf", "rb")}
requests.post(..., files=files)

# 7. Logging estruturado
import logging
logger = logging.getLogger(__name__)
```

> 💡 **Resumo em uma frase**: Este cliente TUI combina uma interface de terminal rica e amigável (via Rich) com comunicação robusta a uma API REST, oferecendo comandos intuitivos, tratamento de erros claro e flexibilidade de configuração — tudo em um script Python autocontido.