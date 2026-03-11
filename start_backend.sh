#!/bin/bash

# Script para iniciar o backend do Gemini ChatBot
# Uso: ./start_backend.sh

set -e  # Sai imediatamente se algum comando falhar

echo "🚀 Iniciando setup do backend..."

# Navegar para o diretório backend
echo "📁 Navegando para o diretório backend..."
cd backend

# Verificar se o requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    echo "❌ Erro: Arquivo requirements.txt não encontrado em backend/"
    exit 1
fi

# checa se o uv está instalado, se não estiver, instala o uv
if ! command -v uv &> /dev/null
then
    echo "🔧 uv não encontrado, instalando uv..."
    python3 -m pip install uv
fi

# Cria o virtual environment
echo "🔧 Verificando ambiente virtual..."

# O uv cria '.venv' por padrão, não 'venv'
if [ ! -d ".venv" ]; then
    echo "🔧 Criando ambiente virtual com uv..."
    uv venv
    echo "✅ Ambiente virtual criado com sucesso!"
else
    echo "⚠️ Ambiente virtual (.venv) já existe, pulando criação."
fi

# Opcional: Ativar o ambiente
# source .venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências Python..."
uv pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas com sucesso!"
else
    echo "❌ Erro na instalação das dependências"
    exit 1
fi

# Executar a aplicação
echo "🎯 Iniciando servidor FastAPI..."
# python3 run.py
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000