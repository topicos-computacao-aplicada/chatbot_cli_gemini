# app.py
import os
import sys
import requests
import uuid
import streamlit as st
import time
import argparse
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="🤖 Gemini ChatBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
    }
    .connection-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .connection-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .setup-container {
        max-width: 600px;
        margin: 50px auto;
        text-align: center;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)


def parse_api_url_from_args() -> str:
    """
    Parse da URL da API a partir de múltiplas fontes, por ordem de prioridade:
    1. Argumento de linha de comando (após --)
    2. Variável de ambiente API_URL
    3. Query parameter da URL do navegador
    4. Valor padrão: http://localhost:8000
    
    Retorna a URL normalizada (sem trailing slash)
    """
    default_url = "http://localhost:8000"
    
    # 1️⃣ Tentar argumentos de linha de comando
    # Streamlit: use -- para separar seus args dos args do streamlit
    # Ex: streamlit run app.py -- http://192.168.1.100:8000
    # Ex: streamlit run app.py -- --api-url http://192.168.1.100:8000
    if len(sys.argv) > 1:
        # Remove possíveis flags do streamlit antes do --
        args = sys.argv[1:]
        
        # Caso: argumento posicional direto após --
        if args and not args[0].startswith('-'):
            candidate = args[0].rstrip('/')
            if candidate.startswith(('http://', 'https://')):
                return candidate
        
        # Caso: --api-url ou --api ou --server como flag nomeada
        try:
            parser = argparse.ArgumentParser(add_help=False)
            parser.add_argument('--api-url', '--api', '--server', dest='api_url', type=str)
            parsed, _ = parser.parse_known_args(args)
            if parsed.api_url:
                return parsed.api_url.rstrip('/')
        except:
            pass  # Ignora erro de parse e continua para próximo método
    
    # 2️⃣ Tentar variável de ambiente
    env_url = os.getenv("API_URL")
    if env_url:
        return env_url.rstrip('/')
    
    # 3️⃣ Tentar query parameter da URL (útil para deploy web)
    # Ex: https://meuapp.streamlit.app/?api_url=http://servidor:8000
    try:
        query_params = st.query_params
        if "api_url" in query_params:
            return query_params["api_url"].rstrip('/')
    except:
        pass  # query_params pode não estar disponível em todas as versões
    
    # 4️⃣ Fallback para localhost
    return default_url


class StreamlitChatClient:
    """Cliente de chat adaptado para Streamlit"""
    
    def __init__(self, api_url: str, session_id: str):
        self.base_url = api_url.rstrip('/')
        self.session_id = session_id
    
    def send_message(self, message: str) -> dict:
        """Envia mensagem para a API REST"""
        payload = {
            "message": message,
            "session_id": self.session_id
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro de conexão com a API: {str(e)}")
    
    def get_history(self) -> list:
        """Busca histórico da conversa"""
        try:
            response = requests.get(
                f"{self.base_url}/conversations/{self.session_id}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("messages", [])
            return []
        except:
            return []


def check_api_connection(api_url: str, timeout: int = 5) -> bool:
    """
    Verifica se a API está disponível e respondendo.
    Tenta endpoints comuns de health check.
    """
    endpoints_to_try = [
        f"{api_url.rstrip('/')}/health",
        f"{api_url.rstrip('/')}/",
        f"{api_url.rstrip('/')}/chat"
    ]
    
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(endpoint, timeout=timeout)
            # Considera conectado se receber qualquer resposta HTTP
            return True
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.RequestException:
            # Endpoint pode exigir POST ou autenticação - ainda assim a API "existe"
            return True
    return False


def initialize_connection_state(default_api_url: str):
    """
    Inicializa o estado de conexão.
    Session_id e client SÓ são criados APÓS conexão estabelecida.
    """
    # Estado de conexão
    if "api_url" not in st.session_state:
        st.session_state.api_url = default_api_url
    
    if "is_connected" not in st.session_state:
        st.session_state.is_connected = False
    
    if "connection_checked" not in st.session_state:
        st.session_state.connection_checked = False
    
    if "connection_error" not in st.session_state:
        st.session_state.connection_error = None
    
    if "connection_attempted_url" not in st.session_state:
        st.session_state.connection_attempted_url = None
    
    # Session_id e client SÓ são criados APÓS conexão estabelecida
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    
    if "client" not in st.session_state:
        st.session_state.client = None
    
    if "messages" not in st.session_state:
        st.session_state.messages = []


def attempt_auto_connect(api_url: str) -> bool:
    """
    Tenta conectar automaticamente com a URL fornecida.
    Retorna True se conseguiu conectar.
    """
    if st.session_state.connection_checked:
        return st.session_state.is_connected
    
    st.session_state.connection_checked = True
    st.session_state.connection_attempted_url = api_url
    
    with st.spinner(f"🔌 Conectando com {api_url}..."):
        if check_api_connection(api_url):
            st.session_state.api_url = api_url
            st.session_state.is_connected = True
            st.session_state.connection_error = None
            
            # ✅ CONEXÃO ESTABELECIDA: Agora gera session_id e client
            if st.session_state.session_id is None:
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.client = StreamlitChatClient(
                    st.session_state.api_url, 
                    st.session_state.session_id
                )
            
            st.success(f"✅ Conectado com {api_url}!")
            time.sleep(1)
            return True
        else:
            st.session_state.is_connected = False
            st.session_state.connection_error = (
                f"❌ Não foi possível conectar com `{api_url}`. "
                f"Verifique se o servidor está rodando ou configure outro IP abaixo."
            )
            return False


def render_connection_setup(current_url: str):
    """
    Renderiza a tela de configuração quando não há conexão.
    Só gera session_id APÓS conexão ser validada.
    """
    st.markdown("<div class='setup-container'>", unsafe_allow_html=True)
    st.title("🔌 Configuração da Conexão")
    st.markdown("### Conecte-se com o servidor da API para começar")
    
    # Info do argumento recebido
    st.info(f"💡 URL configurada via argumento/ambiente: `{current_url}`")
    
    # Exibe erro anterior se houver
    if st.session_state.connection_error:
        st.markdown(
            f"<div class='connection-error'>{st.session_state.connection_error}</div>",
            unsafe_allow_html=True
        )
    
    # Formulário de configuração
    with st.form("connection_form", clear_on_submit=False):
        api_url = st.text_input(
            "🔗 Endereço da API REST",
            value=current_url,
            placeholder="http://localhost:8000",
            help="Ex: http://localhost:8000 ou http://192.168.1.100:8000"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            test_clicked = st.form_submit_button("🧪 Testar", use_container_width=True)
        with col3:
            connect_clicked = st.form_submit_button("✅ Conectar", use_container_width=True, type="primary")
    
    # Lógica dos botões
    if test_clicked or connect_clicked:
        api_url = api_url.rstrip('/')
        with st.spinner(f"🔍 Testando {api_url}..."):
            if check_api_connection(api_url):
                st.session_state.api_url = api_url
                st.session_state.is_connected = True
                st.session_state.connection_error = None
                
                # ✅ CONEXÃO VALIDADA: Agora gera session_id e client
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.client = StreamlitChatClient(api_url, st.session_state.session_id)
                
                st.markdown(
                    f"<div class='connection-success'>✅ Conectado! Session: <code>{st.session_state.session_id[:8]}...</code></div>",
                    unsafe_allow_html=True
                )
                
                time.sleep(1.5)
                st.rerun()
            else:
                st.session_state.connection_error = (
                    f"❌ Falha ao conectar com `{api_url}`. "
                    f"Verifique: servidor rodando? porta correta? firewall?"
                )
                st.session_state.is_connected = False
                st.rerun()
    
    # Ajuda contextual
    with st.expander("💡 Como usar argumentos na execução", expanded=False):
        st.markdown("""
        **Opções para definir a URL da API:**
        
        | Método | Comando | Prioridade |
        |----------|---------|-----------|
        | 🎯 Argumento posicional | `streamlit run app.py -- http://192.168.1.100:8000` | 1ª |
        | 🏷️ Argumento nomeado | `streamlit run app.py -- --api-url http://...` | 1ª |
        | 🌍 Variável de ambiente | `API_URL=http://... streamlit run app.py` | 2ª |
        | 🔗 Query parameter | `?api_url=http://...` na URL do navegador | 3ª |
        | 🏠 Padrão | `streamlit run app.py` (sem args) | 4ª → localhost |
        
        **Dicas:**
        - Use `--` para separar argumentos do Streamlit dos seus argumentos
        - A URL deve incluir o protocolo: `http://` ou `https://`
        - Porta padrão do servidor: `8000`
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar():
    """Renderiza a barra lateral (só aparece após conexão)"""
    with st.sidebar:
        st.title("⚙️ Painel de Controle")
        
        # Status da conexão
        st.success("🟢 Conectado")
        st.metric("API URL", st.session_state.api_url)
        
        # Info da sessão
        st.divider()
        st.subheader("📋 Sessão")
        st.code(st.session_state.session_id, language="text")
        
        # Controles de sessão
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Nova", help="Nova sessão", use_container_width=True):
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.session_state.client = StreamlitChatClient(
                    st.session_state.api_url, 
                    st.session_state.session_id
                )
                st.rerun()
        
        with col2:
            if st.button("🗑️ Limpar", help="Limpar chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        # Histórico
        st.divider()
        if st.button("📜 Carregar Histórico", use_container_width=True):
            try:
                history = st.session_state.client.get_history()
                if history:
                    st.session_state.messages = [
                        {"role": msg["role"], "content": msg["content"], "tokens_used": None}
                        for msg in history
                    ]
                    st.success("✅ Histórico carregado!")
                else:
                    st.info("ℹ️ Sem histórico no servidor")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
        
        # Reconfigurar conexão
        st.divider()
        if st.button("🔧 Reconfigurar API", use_container_width=True):
            st.session_state.is_connected = False
            st.session_state.session_id = None
            st.session_state.client = None
            st.session_state.messages = []
            st.rerun()


def render_chat_interface():
    """Renderiza a interface principal do chat"""
    st.title("🤖 Gemini ChatBot")
    st.caption(f"🔗 {st.session_state.api_url} | 🆔 `{st.session_state.session_id[:8]}...`")
    
    # Exibe histórico de mensagens
    for message in st.session_state.messages:
        avatar = "👤" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            if message.get("tokens_used"):
                st.caption(f"🔢 Tokens: {message['tokens_used']}")
    
    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Adiciona mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Comandos especiais
        cmd = prompt.lower().strip()
        if cmd in ['sair', 'exit', 'quit']:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown("Até logo! 👋")
            return
        
        elif cmd in ['ajuda', 'help']:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown("""
                **Comandos:**
                - `sair` → Encerra o chat
                - `ajuda` → Mostra esta mensagem
                - `historico` → Carrega do servidor
                
                **Exemplos:**
                - "Explique machine learning"
                - "Como criar uma API REST em Python?"
                """)
            return
        
        # Envia para API
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤔 Processando..."):
                try:
                    response = st.session_state.client.send_message(prompt)
                    response_text = response.get("response", "Sem resposta")
                    tokens_used = response.get("tokens_used", 0)
                    
                    st.markdown(response_text)
                    if tokens_used:
                        st.caption(f"🔢 Tokens: {tokens_used}")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "tokens_used": tokens_used
                    })
                    
                except Exception as e:
                    error_msg = f"❌ Erro: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg
                    })


def main():
    """
    Fluxo principal:
    1. Parse da URL da API (args → env → query → default)
    2. Inicializa estados (sem session_id)
    3. Tenta auto-conectar com a URL parseada
    4. Se falhar → tela de configuração
    5. Se sucesso → interface do chat
    """
    
    # 1️⃣ Parse da URL da API a partir de múltiplas fontes
    default_api_url = parse_api_url_from_args()
    
    # 2️⃣ Inicializa estados (session_id = None inicialmente)
    initialize_connection_state(default_api_url)
    
    # 3️⃣ Tenta auto-conectar (apenas na primeira carga)
    if not st.session_state.connection_checked:
        attempt_auto_connect(st.session_state.api_url)
    
    # 4️⃣ Se NÃO conectado → mostra tela de configuração
    if not st.session_state.is_connected:
        render_connection_setup(st.session_state.api_url)
        return  # ⛔ Interrompe - não mostra chat sem conexão
    
    # 5️⃣ Se conectado → renderiza interface completa
    render_sidebar()
    render_chat_interface()
    
    # Rodapé informativo
    st.divider()
    st.markdown(
        "<div class='footer'>"
        "💡 <b>Dica:</b> Use <code>streamlit run app.py -- http://SEU_IP:8000</code> "
        "para definir a API na execução"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()