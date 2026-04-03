# 📚 Explicação Detalhada do Código `app.py`

Explicação do código seção por seção, destacando a lógica, o propósito de cada função e como elas se integram.

## 🔹 1. Imports e Configuração Inicial

```python
import os, sys, requests, uuid, streamlit as st, time, argparse
from datetime import datetime
```

| Módulo | Propósito |
|--------|-----------|
| `os`, `sys` | Acessar variáveis de ambiente e argumentos da linha de comando |
| `requests` | Fazer chamadas HTTP para a API REST |
| `uuid` | Gerar identificadores únicos para sessões de chat |
| `streamlit as st` | Framework para criar a interface web |
| `time` | Pausas para feedback visual ao usuário |
| `argparse` | Parsear argumentos nomeados da CLI |

```python
st.set_page_config(...)
```
Configura metadados da página: título, ícone, layout amplo e sidebar recolhida inicialmente.

## 🔹 2. CSS Personalizado

```python
st.markdown("""<style>...</style>""", unsafe_allow_html=True)
```

Define estilos visuais para:
- `.stChatMessage`: Bolhas de mensagem com bordas arredondadas
- `.connection-success` / `.connection-error`: Boxes coloridos para feedback de conexão
- `.setup-container`: Centraliza a tela de configuração
- `.footer`: Rodapé estilizado

> ⚠️ `unsafe_allow_html=True` é necessário para injetar CSS personalizado no Streamlit.


## 🔹 3. Função `parse_api_url_from_args()`

**Propósito**: Determinar a URL da API usando múltiplas fontes, por ordem de prioridade:

```
1️⃣ Argumento de linha de comando
2️⃣ Variável de ambiente API_URL  
3️⃣ Query parameter da URL (?api_url=...)
4️⃣ Fallback: http://localhost:8000
```

### Como funciona:

```python
# 1. Argumentos posicionais ou nomeados
if len(sys.argv) > 1:
    args = sys.argv[1:]
    # Posicional: streamlit run app.py -- http://192.168.1.100:8000
    if args and not args[0].startswith('-'):
        return args[0].rstrip('/')
    
    # Nomeado: --api-url, --api, --server
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--api-url', '--api', '--server', dest='api_url', type=str)
    parsed, _ = parser.parse_known_args(args)
    if parsed.api_url:
        return parsed.api_url.rstrip('/')

# 2. Variável de ambiente
env_url = os.getenv("API_URL")
if env_url:
    return env_url.rstrip('/')

# 3. Query parameter (para deploys web)
try:
    if "api_url" in st.query_params:
        return st.query_params["api_url"].rstrip('/')
except:
    pass

# 4. Fallback
return "http://localhost:8000"
```

> ✅ A função normaliza a URL removendo `/` no final para evitar erros de concatenação.

## 🔹 4. Classe `StreamlitChatClient`

Encapsula a comunicação com a API REST:

```python
class StreamlitChatClient:
    def __init__(self, api_url: str, session_id: str):
        self.base_url = api_url.rstrip('/')
        self.session_id = session_id
```

### Métodos:

#### `send_message(message: str) -> dict`
```python
# Envia POST para /chat com payload JSON
payload = {"message": message, "session_id": self.session_id}
response = requests.post(f"{self.base_url}/chat", json=payload, ...)
return response.json()
```
- Lança exceção se a requisição falhar
- Timeout de 60 segundos para respostas longas

#### `get_history() -> list`
```python
# Faz GET para /conversations/{session_id}
response = requests.get(f"{self.base_url}/conversations/{self.session_id}")
return response.json().get("messages", [])
```
- Retorna lista vazia se falhar (fail-safe)

## 🔹 5. Função `check_api_connection(api_url, timeout=5)`

**Propósito**: Validar se a API está acessível antes de criar a sessão.

```python
endpoints_to_try = [
    f"{api_url}/health",   # Endpoint padrão de health check
    f"{api_url}/",         # Root da API
    f"{api_url}/chat"      # Endpoint principal
]
```

### Lógica de verificação:
```python
for endpoint in endpoints_to_try:
    try:
        response = requests.get(endpoint, timeout=timeout)
        return True  # Qualquer resposta HTTP = API "existe"
    except (ConnectionError, Timeout):
        continue  # Tenta próximo endpoint
    except RequestException:
        return True  # Erro 4xx/5xx ainda indica que a API está up
return False  # Nenhum endpoint respondeu
```

> 🎯 Estratégia resiliente: considera "conectado" mesmo se o endpoint exigir POST ou autenticação.

## 🔹 6. Função `initialize_connection_state(default_api_url)`

**Propósito**: Inicializar `st.session_state` com valores padrão, **sem criar session_id ainda**.

```python
# Estados de conexão
st.session_state.setdefault("api_url", default_api_url)
st.session_state.setdefault("is_connected", False)
st.session_state.setdefault("connection_checked", False)
st.session_state.setdefault("connection_error", None)

# Session_id e client = None até conexão ser validada ✅
st.session_state.setdefault("session_id", None)
st.session_state.setdefault("client", None)
st.session_state.setdefault("messages", [])
```

> 🔑 Princípio chave: **conexão primeiro, sessão depois**.

## 🔹 7. Função `attempt_auto_connect(api_url)`

**Propósito**: Tentar conectar automaticamente na primeira carga da aplicação.

```python
if st.session_state.connection_checked:
    return st.session_state.is_connected  # Evita reconexão em reruns

st.session_state.connection_checked = True

with st.spinner(f"🔌 Conectando com {api_url}..."):
    if check_api_connection(api_url):
        # ✅ SUCESSO: Agora cria session_id e client
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.client = StreamlitChatClient(api_url, session_id)
        st.success("✅ Conectado!")
        time.sleep(1)  # Feedback visual
        return True
    else:
        # ❌ FALHA: Mantém session_id = None
        st.session_state.connection_error = "Mensagem de erro..."
        return False
```

> ⏱️ `time.sleep(1)` dá tempo do usuário ver a mensagem de sucesso antes da interface mudar.

## 🔹 8. Função `render_connection_setup(current_url)`

**Propósito**: Exibir tela de configuração quando a conexão automática falha.

### Elementos da UI:
```python
st.title("🔌 Configuração da Conexão")
st.info(f"💡 URL configurada: `{current_url}`")  # Mostra origem da URL

# Box de erro (se houver)
if st.session_state.connection_error:
    st.markdown(f"<div class='connection-error'>...</div>", unsafe_allow_html=True)

# Formulário para novo IP
with st.form("connection_form"):
    api_url = st.text_input("🔗 Endereço da API", value=current_url)
    col1, col2, col3 = st.columns([2,1,1])
    with col2: test_clicked = st.form_submit_button("🧪 Testar")
    with col3: connect_clicked = st.form_submit_button("✅ Conectar", type="primary")
```

### Lógica dos botões:
```python
if test_clicked or connect_clicked:
    if check_api_connection(api_url):
        # ✅ Conectou: gera session_id, client e força rerun
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.client = StreamlitChatClient(api_url, session_id)
        st.rerun()  # Recarrega a app agora conectado
    else:
        # ❌ Falhou: atualiza erro e rerun para exibir mensagem
        st.session_state.connection_error = "..."
        st.rerun()
```

### Expander de ajuda:
```python
with st.expander("💡 Como usar argumentos..."):
    st.markdown("""Tabela com métodos de configuração e dicas""")
```

## 🔹 9. Função `render_sidebar()`

**Propósito**: Barra lateral com controles, **só exibida após conexão**.

### Conteúdo:
```python
st.success("🟢 Conectado")
st.metric("API URL", st.session_state.api_url)

st.code(st.session_state.session_id)  # Exibe ID da sessão

# Botões de controle
col1, col2 = st.columns(2)
with col1: 
    if st.button("🔄 Nova"):  # Nova sessão
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
with col2:
    if st.button("🗑️ Limpar"):  # Limpa chat local
        st.session_state.messages = []
        st.rerun()

# Carregar histórico do servidor
if st.button("📜 Carregar Histórico"):
    history = st.session_state.client.get_history()
    # Atualiza st.session_state.messages com histórico

# Botão para reconfigurar conexão
if st.button("🔧 Reconfigurar API"):
    # Reseta estados de conexão para voltar à tela de setup
    st.session_state.is_connected = False
    st.session_state.session_id = None
    st.rerun()
```

## 🔹 10. Função `render_chat_interface()`

**Propósito**: Interface principal do chat com mensagens e input.

### Exibição do histórico local:
```python
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])  # Suporta Markdown
        if message.get("tokens_used"):
            st.caption(f"🔢 Tokens: {message['tokens_used']}")
```

### Input do usuário:
```python
if prompt := st.chat_input("Digite sua mensagem..."):
    # 1. Adiciona mensagem do usuário ao histórico local
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Processa comandos especiais
    cmd = prompt.lower().strip()
    if cmd in ['sair', 'exit', 'quit']:
        st.markdown("Até logo! 👋")
        return
    elif cmd in ['ajuda', 'help']:
        st.markdown("Lista de comandos...")
        return
    
    # 3. Envia para API e exibe resposta
    with st.spinner("🤔 Processando..."):
        response = st.session_state.client.send_message(prompt)
        st.markdown(response["response"])
        # Salva resposta no histórico local
```

> 🛡️ Tratamento de erro: se a API falhar, exibe mensagem de erro no chat em vez de quebrar a app.

## 🔹 11. Função `main()` - Fluxo Principal

```python
def main():
    # 1️⃣ Parse da URL (args → env → query → default)
    default_api_url = parse_api_url_from_args()
    
    # 2️⃣ Inicializa estados (session_id = None)
    initialize_connection_state(default_api_url)
    
    # 3️⃣ Tenta auto-conectar (apenas na 1ª carga)
    if not st.session_state.connection_checked:
        attempt_auto_connect(st.session_state.api_url)
    
    # 4️⃣ Se NÃO conectado → tela de configuração + return
    if not st.session_state.is_connected:
        render_connection_setup(st.session_state.api_url)
        return  # ⛔ Interrompe execução
    
    # 5️⃣ Se conectado → interface completa
    render_sidebar()
    render_chat_interface()
    
    # Rodapé informativo
    st.markdown("<div class='footer'>Dica de uso...</div>", unsafe_allow_html=True)
```

### Diagrama do fluxo:

```
🚀 main() inicia
│
├─▶ parse_api_url_from_args() 
│   └─▶ Retorna URL (ex: http://localhost:8000)
│
├─▶ initialize_connection_state()
│   └─▶ session_id = None, is_connected = False
│
├─▶ attempt_auto_connect(url) [apenas 1ª vez]
│   ├─✅ Sucesso → session_id = uuid4(), client criado
│   └─❌ Falha → is_connected = False, mostra erro
│
├─▶ if not is_connected:
│   └─▶ render_connection_setup() + return ⛔
│
└─▶ else:
    ├─▶ render_sidebar()
    ├─▶ render_chat_interface()
    └─▶ Chat funcional 🎉
```

## 🔹 12. Conceitos Chave do Streamlit Utilizados

| Conceito | Por que foi usado? |
|----------|-------------------|
| `st.session_state` | Manter estado entre reruns (mensagens, conexão, session_id) |
| `st.rerun()` | Forçar recarregamento após mudança crítica de estado |
| `st.chat_message()` | Componente nativo para interface de chat |
| `st.spinner()` / `st.success()` / `st.error()` | Feedback visual assíncrono |
| `st.form()` + `st.form_submit_button()` | Agrupar inputs para evitar reruns prematuros |
| `st.markdown(..., unsafe_allow_html=True)` | Injetar CSS personalizado |
| `st.query_params` | Suporte a parâmetros na URL para deploys web |

## 🔹 13. Boas Práticas Implementadas

✅ **Fail-fast**: Interrompe execução se não houver conexão  
✅ **Separação de responsabilidades**: Funções específicas para conexão, UI, cliente HTTP  
✅ **Feedback ao usuário**: Spinners, mensagens de sucesso/erro, tooltips  
✅ **Resiliência**: Múltiplos endpoints de health check, fallbacks de configuração  
✅ **Segurança básica**: Session_id gerado apenas após validação da API  
✅ **UX consistente**: Comandos de texto (`sair`, `ajuda`) funcionam como na CLI original  


## 🔹 14. Possíveis Melhorias Futuras

```python
# 1. Suporte a autenticação JWT
headers = {"Authorization": f"Bearer {os.getenv('API_TOKEN')}"}

# 2. Streaming de resposta (se a API suportar Server-Sent Events)
with requests.post(..., stream=True) as resp:
    for line in resp.iter_lines():
        st.markdown(line.decode(), unsafe_allow_html=True)

# 3. Cache de respostas com @st.cache_data
@st.cache_data(ttl=300)
def cached_send_message(message, session_id): ...

# 4. Logging estruturado para debug em produção
import logging
logger = logging.getLogger(__name__)
logger.info(f"Conectando a {api_url}...")
```

> 💡 **Resumo em uma frase**: O código implementa um frontend Streamlit que **primeiro valida a conexão com a API** e **só então cria a sessão de chat**, garantindo que o usuário nunca interaja com uma sessão inválida, com múltiplas formas flexíveis de configuração da URL da API.

Precisa de esclarecimentos sobre alguma função específica ou quer ver como adaptar para um caso de uso diferente? É só perguntar! 🚀
