#!/bin/bash

# Script para iniciar o frontend Streamlit do Gemini ChatBot
# Uso: ./start_web.sh [IP_DO_SERVIDOR]
#      ./start_web.sh                          → usa localhost:8000 (padrão)
#      ./start_web.sh 192.168.1.100           → conecta ao IP especificado
#      ./start_web.sh --port 8501             → altera porta do Streamlit

set -e  # Sai imediatamente se algum comando falhar

# Configurações padrão
DEFAULT_API_URL="http://localhost:8000"
DEFAULT_STREAMLIT_PORT=8501
CLIENT_DIR="chat-frontend"
APP_FILE="app.py"
REQUIREMENTS_FILE="requirements.txt"

# Cores para output (funciona em terminais compatíveis)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens formatadas
info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warning() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
error()   { echo -e "${RED}[ERRO]${NC} $1"; }

# Função de ajuda
show_help() {
    cat << EOF
🤖 Gemini ChatBot - Frontend Streamlit

Uso: $0 [OPÇÕES] [IP_DO_SERVIDOR]

Argumentos:
  IP_DO_SERVIDOR          IP ou URL da API REST (ex: 192.168.1.100)
                          Se omitido, usa: $DEFAULT_API_URL

Opções:
  -p, --port PORTA        Porta para o Streamlit (padrão: $DEFAULT_STREAMLIT_PORT)
  -h, --host HOST         Host para bind do Streamlit (padrão: 0.0.0.0)
  -e, --env ARQUIVO       Arquivo .env com variáveis de ambiente
  -d, --debug             Modo debug: mostra logs detalhados
  --help                  Mostra esta mensagem de ajuda

Exemplos:
  $0                              # Inicia com localhost:8000
  $0 192.168.1.100               # Conecta ao servidor especificado
  $0 -p 8600 10.0.0.50           # Porta customizada + IP
  $0 --host 127.0.0.1            # Bind apenas em localhost
  $0 -e .env.prod 192.168.1.100  # Com arquivo de ambiente

EOF
    exit 0
}

# Parse de argumentos
STREAMLIT_PORT="$DEFAULT_STREAMLIT_PORT"
STREAMLIT_HOST="0.0.0.0"
ENV_FILE=""
DEBUG_MODE=false
SERVER_IP=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--host)
            STREAMLIT_HOST="$2"
            shift 2
            ;;
        -p|--port)
            STREAMLIT_PORT="$2"
            shift 2
            ;;
        -e|--env)
            ENV_FILE="$2"
            shift 2
            ;;
        -d|--debug)
            DEBUG_MODE=true
            shift
            ;;
        --help)
            show_help
            ;;
        -*)
            error "Opção desconhecida: $1"
            echo "Use --help para ver opções válidas"
            exit 1
            ;;
        *)
            # Argumento posicional = IP do servidor
            if [ -z "$SERVER_IP" ]; then
                SERVER_IP="$1"
            else
                error "Múltiplos IPs fornecidos: $SERVER_IP e $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# Definir URL da API
if [ -n "$SERVER_IP" ]; then
    # Se for apenas IP, monta URL completa
    if [[ "$SERVER_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || [[ "$SERVER_IP" =~ ^[a-zA-Z0-9.-]+$ ]]; then
        API_URL="http://${SERVER_IP}:8000"
    else
        # Já é uma URL completa
        API_URL="$SERVER_IP"
    fi
else
    API_URL="$DEFAULT_API_URL"
fi

# Carregar arquivo .env se especificado
if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
    info "Carregando variáveis de ambiente de: $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
elif [ -n "$ENV_FILE" ]; then
    warning "Arquivo .env especificado não encontrado: $ENV_FILE"
fi

# Exportar API_URL para a aplicação Streamlit
export API_URL="$API_URL"

echo ""
echo "🚀 Iniciando setup do frontend Streamlit..."
echo "📡 API URL: $API_URL"
echo "🌐 Streamlit: http://${STREAMLIT_HOST}:${STREAMLIT_PORT}"
if [ "$DEBUG_MODE" = true ]; then
    echo "🐛 Modo debug: ATIVADO"
fi
echo ""

# Navegar para o diretório do cliente
info "Navegando para o diretório: $CLIENT_DIR/"
if [ ! -d "$CLIENT_DIR" ]; then
    error "Diretório '$CLIENT_DIR' não encontrado!"
    echo "💡 Certifique-se de executar este script a partir da raiz do projeto."
    exit 1
fi
cd "$CLIENT_DIR"

# Verificar se o app.py existe
if [ ! -f "$APP_FILE" ]; then
    error "Arquivo '$APP_FILE' não encontrado em $CLIENT_DIR/"
    exit 1
fi

# Verificar se requirements.txt existe
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    error "Arquivo '$REQUIREMENTS_FILE' não encontrado em $CLIENT_DIR/"
    exit 1
fi

# Verificar/instalar uv
info "Verificando gerenciador uv..."
if ! command -v uv &> /dev/null; then
    warning "uv não encontrado no PATH, instalando via pip..."
    if command -v pip3 &> /dev/null; then
        pip3 install --user uv
    elif command -v pip &> /dev/null; then
        pip install --user uv
    else
        error "pip não encontrado! Instale uv manualmente: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    
    # Verificar se a instalação funcionou
    if ! command -v uv &> /dev/null; then
        error "Falha ao instalar uv. Tente adicionar ~/.local/bin ao PATH ou instale manualmente."
        exit 1
    fi
    success "uv instalado com sucesso!"
else
    UV_VERSION=$(uv --version 2>/dev/null || echo "desconhecida")
    success "uv encontrado: $UV_VERSION"
fi

# Criar/verificar ambiente virtual
info "Verificando ambiente virtual (.venv)..."
if [ ! -d ".venv" ]; then
    info "Criando ambiente virtual com uv..."
    uv venv
    
    if [ -d ".venv" ]; then
        success "Ambiente virtual criado em: $(pwd)/.venv"
    else
        error "Falha ao criar ambiente virtual!"
        exit 1
    fi
else
    warning "Ambiente virtual já existe, pulando criação."
fi

# Instalar/atualizar dependências
info "Instalando dependências Python com uv..."

if [ "$DEBUG_MODE" = true ]; then
    # Modo debug: mostra output completo
    uv pip install -r "$REQUIREMENTS_FILE"
else
    # Modo normal: output silencioso, só mostra se falhar
    if uv pip install -r "$REQUIREMENTS_FILE" -q 2>/dev/null; then
        success "Dependências verificadas/atualizadas!"
    else
        # Tenta novamente com output para debug
        warning "Tentando reinstalação com output detalhado..."
        uv pip install -r "$REQUIREMENTS_FILE"
    fi
fi

# Verificar instalação do streamlit
info "Verificando instalação do Streamlit..."
if ! uv run --quiet python -c "import streamlit" 2>/dev/null; then
    error "Streamlit não está instalado no ambiente virtual!"
    warning "Tentando instalar streamlit..."
    uv pip install streamlit
fi

# Banner final antes de iniciar
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  🤖 Gemini ChatBot - Frontend Web                     ║"
echo "╠════════════════════════════════════════════════════════╣"
echo "║  🔗 API:        $API_URL"
echo "║  🌐 Frontend:   http://${STREAMLIT_HOST}:${STREAMLIT_PORT}"
echo "║  📁 Diretório:  $(pwd)"
echo "║  🐍 Python:     $(uv run --quiet python --version 2>/dev/null || echo 'N/A')"
echo "╠════════════════════════════════════════════════════════╣"
echo "║  💡 Para parar: pressione Ctrl+C                       ║"
echo "║  🔄 Para reiniciar: execute este script novamente      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Comando para executar o Streamlit
STREAMLIT_CMD="uv run streamlit run $APP_FILE"
STREAMLIT_CMD+=" --server.address $STREAMLIT_HOST"
STREAMLIT_CMD+=" --server.port $STREAMLIT_PORT"
STREAMLIT_CMD+=" --server.headless true"  # Para rodar em servidores/containers
STREAMLIT_CMD+=" --browser.gatherUsageStats false"  # Privacidade
STREAMLIT_CMD+=" --"  # Separador: tudo depois é argumento para app.py
STREAMLIT_CMD+=" $API_URL"  # Passa a URL da API para o app.py

# Modo debug: mostra o comando exato
if [ "$DEBUG_MODE" = true ]; then
    info "Comando de execução:"
    echo "  $STREAMLIT_CMD"
    echo ""
fi

# Executar o Streamlit
info "Iniciando servidor Streamlit..."
echo ""

# Trap para limpeza ao receber SIGINT/SIGTERM
cleanup() {
    echo ""
    warning "Recebido sinal de interrupção..."
    info "Encerrando frontend Streamlit..."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Executa e mantém o processo em primeiro plano
eval "$STREAMLIT_CMD"

# Se chegar aqui, o streamlit encerrou inesperadamente
if [ $? -ne 0 ]; then
    error "Streamlit encerrou com código de erro $?"
    exit 1
fi