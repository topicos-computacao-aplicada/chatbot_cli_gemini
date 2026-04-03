# Chatbot CLI e API Gateway integrado a API do Google Gemini e Modelos LLM do Ollama local

## 📊 Funcionalidades Implementadas no Protótipo

- ✅ Integração com [Google Gemini API](https://ai.google.dev/gemini-api/docs) e Modelos LLM hospedados localmente via Ollama
- ✅ Persistência em [SQLite](https://sqlite.org/) com [SQLAlchemy](https://www.sqlalchemy.org/) ORM
- ✅ API REST com [FastAPI](https://fastapi.tiangolo.com/)
- ✅ Cliente terminal com interface rica ([Rich](https://rich.readthedocs.io/en/latest/introduction.html))
- ✅ Cliente web com interface síncrona
- ✅ Gerenciamento de sessões (apenas enquanto o cliente está ativo)
- ✅ Histórico de conversas
- ✅ Contagem de tokens
- ✅ Tratamento de erros
- ✅ Documentação automática da API (FastAPI)

## A. Estrutura do Projeto

```bash
chatbot_cli_gemini
├── backend
│   ├── app
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── gemini_client.py
│   │   ├── llm_client_interface.py
│   │   ├── ollama_client.py
│   │   └── config.py
│   ├── requirements.txt
│   └── .env
├── client
│   ├── chat_client.py
│   └── requirements.txt
├── chat-frontend
│   ├── app.py
├── start_backend.sh
├── start_client.sh
├── start_web.sh
├── .gitignore
└── README.md
```

### Detalhes do projeto

## B. Ambiente de Desenvolvimento

Existe uma estrutura base que vamos seguir para a construção de nossas aplicações FastAPI.

Vamos usar o gerenciador de pacotes [uv](https://github.com/astral-sh/uv).

### 1. As variáveis de ambiente da aplicação são configuradas via .evn

Faça as devidas configurações de variáveis no arquivo backend/.env

```bash
DATABASE_URL=sqlite:///./chatbot.db

# Valores permitidos: gemini | ollama
LLM_PROVIDER=ollama

# ===========================================
# CONFIGURAÇÕES GEMINI (quando LLM_PROVIDER=gemini)
# ===========================================
GEMINI_API_KEY=?
GEMINI_MODEL=gemini-2.5-flash

# ===========================================
# CONFIGURAÇÕES OLLAMA (quando LLM_PROVIDER=ollama)
# ===========================================
# URL base da API do Ollama (padrão: localhost)
OLLAMA_BASE_URL=http://localhost:11434

# Nome do modelo instalado no Ollama (ex: llama2, mistral, llama3, etc)
OLLAMA_MODEL=qwen3

# Timeout para requisições em segundos
OLLAMA_TIMEOUT=120

# Temperatura para geração (0.0 a 1.0)
OLLAMA_TEMPERATURE=0.7

# Número máximo de tokens para prever
OLLAMA_NUM_PREDICT=2048

```

### 2. Uma vez criado e ativado o venv execute os scripts de inicialização

Atualização de permissão para execução. Execute no diretório raiz do projeto
```bash
chmod +x start_backend.sh
chmod +x start_client.sh
```

Inicializa o ambiente de backend. Ative o venv e execute no diretório raiz do projeto
```bash
./start_backend.sh
```

Inicializa o ambiente client. Ative o venv e execute no diretório raiz do projeto
```bash
./start_client.sh IP_Servidor
```

Inicializa o ambiente client web. Ative o venv e execute no diretório raiz do projeto
```bash
./start_web.sh IP_Servidor
```

### 3. Após os scripts de inicialização terem sido executados 

**3.1 Executar a aplicação direto pelo uvicorn backend**

Vá até o diretório chatbot_cli_gemini/backend
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**3.2 Executar a aplicação cliente em um novo terminal**

Vá até o diretório chatbot_cli_gemini/client
```bash
python3 chat_client.py IP_Servidor
```

### 4. Observações

Este protótipo só mantem o histórico das mensagens do cliente enquanto sua sessão estiver aberta, ou seja, assim que o cliente fechar sua sessão ele não consegue mais acessar seu histórico. Entretanto, a aplicação backend possui um banco que armazena todas as mensagens de todos os clientes que acessaram a aplicação pelo menos uma vez.

Em caso de dúvidas, pode enviar um e-mail para armando@ufpi.edu.br