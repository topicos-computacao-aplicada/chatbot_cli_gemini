# Chatbot CLI e API Gateway integrado a API do Google Gemini

## 📊 Funcionalidades Implementadas no Protótipo

- ✅ Integração com Google Gemini API
- ✅ Persistência em SQLite com SQLAlchemy ORM
- ✅ API REST com FastAPI
- ✅ Cliente terminal com interface rica (Rich)
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
│   │   └── config.py
│   ├── requirements.txt
│   └── .env
├── client
│   ├── chat_client.py
│   └── requirements.txt
├── start_backend.sh
├── start_client.sh
├── .gitignore
└── README.md
```

### Detalhes do projeto

## B. Ambiente de Desenvolvimento

Existe uma estrutura base que vamos seguir para a construção de nossas aplicações FastAPI.

Vamos usar o gerenciador de pacotes uv.

### 1. As variáveis de ambiente da aplicação são configuradas via .evn

Faça as devidas configurações de variáveis no arquivo backend/.env

```bash
DATABASE_URL=sqlite:///./chatbot.db
GEMINI_API_KEY=?
GEMINI_MODEL=gemini-2.5-flash
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

### 4. Após os scripts de inicialização terem sido executados 

**4.1 Executar a aplicação backend**

Vá até o diretório gemini_chatbot/backend
```bash
python3 run.py
```

**4.2 Executar a aplicação cliente em um novo terminal**

Vá até o diretório gemini_chatbot/client
```bash
python3 chat_client.py IP_Servidor
```

### 5. Observações

Este protótipo só mantem o histórico das mensagens do cliente enquanto sua sessão estiver aberta, ou seja, assim que o cliente fechar sua sessão ele não consegue mais acessar seu histórico. Entretanto, a aplicação backend possui um banco que armazena todas as mensagens de todos os clientes que acessaram a aplicação pelo menos uma vez.