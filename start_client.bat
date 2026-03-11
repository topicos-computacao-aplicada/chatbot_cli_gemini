@echo off
REM Script para iniciar o cliente do Gemini ChatBot no Windows
REM Uso: start_client.bat [IP_DO_SERVIDOR]

if "%1"=="" (
    echo ❌ Erro: IP do servidor não fornecido
    echo Uso: %0 ^<IP_DO_SERVIDOR^>
    echo Exemplo: start_client.bat 10.13.63.20
    pause
    exit /b 1
)

set SERVER_IP=%1

echo 🚀 Iniciando setup do cliente...
echo 📡 Conectando ao servidor: %SERVER_IP%

cd client || (
    echo ❌ Erro: Não foi possível navegar para o diretório client
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ❌ Erro: Arquivo requirements.txt não encontrado em client/
    pause
    exit /b 1
)

if not exist "chat_client.py" (
    echo ❌ Erro: Arquivo chat_client.py não encontrado em client/
    pause
    exit /b 1
)

echo 📦 Instalando dependências Python...
pip install -r requirements.txt || (
    echo ❌ Erro na instalação das dependências
    pause
    exit /b 1
)

echo ✅ Dependências instaladas com sucesso!
echo 🎯 Iniciando cliente de chat...
echo 🔗 Conectando ao servidor: %SERVER_IP%

python chat_client.py %SERVER_IP%
