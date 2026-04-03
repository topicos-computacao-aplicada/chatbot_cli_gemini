# Sistema de Chatbot com LLM e Persistência de Contexto

## Solução: Sistema de Chatbot com Suporte Multi-Provider LLM (Gemini/Ollama)

| Atributo | Descrição |
| :--- | :--- |
| **Nome do Projeto** | AI Chat Context Gateway (ACCG) |
| **Versão** | **2.0.0** ⬆️ |
| **Data** | Abril/2026 |
| **Elaborado Por** | Armando Soares |

## 1. Introdução

Esta solução é um sistema de *chatbot* dividido em três camadas principais (Cliente Terminal, API Gateway, LLM Client) que permite aos usuários interagir com **Modelos de Linguagem Grande (LLM) de múltiplos provedores** de forma persistente e configurável. 

**Novidade na Versão 2.0**: O sistema agora suporta **arquitetura multi-provider**, permitindo alternar entre:
- 🌐 **Google Gemini** (API cloud)
- 🖥️ **Ollama** (modelos locais hospedados na máquina do usuário)

O objetivo principal é fornecer um mecanismo robusto, flexível e extensível para gerenciar o estado da conversa (*histórico*) enquanto oferece liberdade na escolha do modelo de IA subjacente, **sem quebrar a compatibilidade com aplicações frontend existentes**.

## 2. Arquitetura da Solução

O sistema adota uma arquitetura Cliente-Servidor de três camadas com **padrão Strategy via Interface Abstrata**:

```
┌─────────────────┐
│   Cliente CLI   │  ← Frontend (inalterado)
└────────┬────────┘
         │ HTTP/JSON (API contracts preservados)
         ▼
┌─────────────────┐
│  API Gateway    │  ← FastAPI + Factory Pattern
│  (Backend)      │     • get_llm_client() factory
│                 │     • LLMClientInterface (ABC)
└────────┬────────┘
         │ Interface Comum
         ▼
┌──────────────────┐
│  LLM Providers   │  ← Implementações intercambiáveis
│  ┌────────────┐  │
│  │GeminiClient│  │  • google-generativeai
│  └────────────┘  │
│  ┌────────────┐  │
│  │OllamaClient│  │  • requests + API local
│  └────────────┘  │
└──────────────────┘
```

### Componentes Principais

| Camada | Componente | Responsabilidade |
|--------|-----------|-----------------|
| **Cliente** | `main.py` (CLI) | Interface de usuário, gerenciamento de sessão UUID, envio de requisições HTTP |
| **API Gateway** | `main.py` (FastAPI) | Rotas REST, persistência SQLAlchemy, factory de LLM clients, tratamento de erros |
| **Abstração** | `llm_client_interface.py` | Interface abstrata comum (`LLMClientInterface`) garantindo contrato único de resposta |
| **Provedor Cloud** | `gemini_client.py` | Integração com Google Gemini API via `google-generativeai` |
| **Provedor Local** | `ollama_client.py` | Integração com Ollama local via HTTP/REST (`requests`) |
| **Persistência** | `models.py` + `database.py` | ORM SQLAlchemy para `Conversation` e `Message` |


## 3. Requisitos Funcionais (RF) - Atualizados

| ID | Módulo | Requisito | Status |
| :--- | :--- | :--- | :--- |
| **RF-001** | Cliente | **Iniciar Sessão:** O cliente deve gerar e manter um ID de sessão único (UUID) no início da execução para rastrear a conversa. | ✅ Mantido |
| **RF-002** | Cliente | **Comunicação:** O cliente deve enviar mensagens via **HTTP POST** para `/chat`, incluindo `session_id` e `message`. | ✅ Mantido |
| **RF-003** | Cliente | **Comandos:** Suporte aos comandos `sair`, `ajuda` e `historico` (gerenciamento local ou via API). | ✅ Mantido |
| **RF-004** | API | **Persistência de Conversa:** Criar/recuperar entidade `Conversation` baseada no `session_id`. | ✅ Mantido |
| **RF-005** | API | **Registro de Mensagem:** Salvar mensagens do usuário e assistente com *roles* `user`/`assistant`. | ✅ Mantido |
| **RF-006** | API | **Gerenciamento de Contexto:** Recuperar últimas N (N=5) mensagens para construir contexto da conversa. | ✅ Mantido |
| **RF-007** | **LLM Factory** | **Seleção Dinâmica de Provider:** O backend deve carregar o cliente LLM baseado na variável de ambiente `LLM_PROVIDER` (`gemini` ou `ollama`). | ✨ **Novo** |
| **RF-008** | **LLM Interface** | **Contrato Comum de Resposta:** Todos os clientes LLM devem implementar `generate_response(prompt, context)` retornando `{"text": str, "tokens_used": int}`. | ✨ **Novo** |
| **RF-009** | Gemini Client | **Geração via Cloud:** Chamar API do Gemini com prompt + contexto + system prompt de persona. | ✅ Atualizado |
| **RF-010** | **Ollama Client** | **Geração via Local:** Chamar API local do Ollama (`/api/generate`) com configuração de modelo, temperatura e timeout via variáveis de ambiente. | ✨ **Novo** |
| **RF-011** | API | **Recuperação de Histórico:** Endpoint **GET** `/conversations/{session_id}` retorna mensagens da sessão. | ✅ Mantido |
| **RF-012** | Cliente | **Visualização de Histórico:** Exibir mensagens salvas ao comando `historico`. | ✅ Mantido |
| **RF-013** | **API** | **Health Check com Provider:** Endpoint `/health` deve retornar o provedor LLM ativo (`llm_provider`). | ✨ **Novo** |
| **RF-014** | **API** | **Listagem de Modelos:** Endpoint opcional `/models` retorna modelos disponíveis no provider configurado. | ✨ **Novo** |
| **RF-015** | **Sistema** | **Compatibilidade Retroativa:** Todas as alterações devem preservar os schemas de request/response existentes para não quebrar frontends consumidores. | ✨ **Novo** |

## 4. Requisitos Não-Funcionais (RNF) - Atualizados

| ID | Categoria | Requisito | Status |
| :--- | :--- | :--- | :--- |
| **RNF-001** | Performance | Latência da API (excluindo tempo do LLM) < 100ms. | ✅ Mantido |
| **RNF-002** | Escalabilidade | API assíncrona (ASGI) para I/O bound e múltiplas sessões simultâneas. | ✅ Mantido |
| **RNF-003** | Segurança | Chaves de API e configurações sensíveis via **variáveis de ambiente** ou `.env`. | ✅ Mantido |
| **RNF-004** | Usabilidade | CLI com formatação avançada (`rich`) para legibilidade. | ✅ Mantido |
| **RNF-005** | Manutenibilidade | Type hints, documentação OpenAPI/Swagger automática, código modular. | ✅ Mantido |
| **RNF-006** | Robustez | Tratamento de erros com `try/except`, `db.rollback()` e HTTP status apropriados. | ✅ Mantido |
| **RNF-007** | **Configurabilidade** | **Troca de Provider sem Rebuild:** Alterar `LLM_PROVIDER` no `.env` deve permitir mudar entre Gemini/Ollama sem recompilar ou alterar código. | ✨ **Novo** |
| **RNF-008** | **Extensibilidade** | **Novos Providers:** Adicionar novo provedor (ex: OpenAI) deve requerer apenas nova classe herdando `LLMClientInterface` + atualização mínima na factory. | ✨ **Novo** |
| **RNF-009** | **Resiliência Local** | **Fallback para Ollama Offline:** Se `LLM_PROVIDER=ollama` e o serviço local estiver indisponível, retornar erro descritivo sem crash da API. | ✨ **Novo** |
| **RNF-010** | **Consistência de Resposta** | **Schema Unificado:** Independente do provider, a resposta da API deve seguir exatamente o mesmo `ChatResponse` schema. | ✨ **Novo** |

## 5. Requisitos de Dados (RD) - Atualizados

### Modelo de Dados (SQLAlchemy) - *Inalterado*

| Tabela | Campo | Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| **Conversation** | `id` | Integer (PK) | ID primário |
| | `session_id` | String (UUID) | ID único para rastreamento de sessão |
| | `created_at` | Timestamp | Data/hora da criação |
| **Message** | `id` | Integer (PK) | ID primário |
| | `conversation_id`| Integer (FK) | Chave estrangeira para `Conversation` |
| | `role` | String | `"user"` ou `"assistant"` |
| | `content` | Text | Conteúdo da mensagem |
| | `tokens_used` | Integer | Estimativa de tokens (para métricas) |
| | `timestamp` | Timestamp | Data/hora do envio |

> ✅ **Nota:** O modelo de dados **não requer alterações** pois a abstração do provider é tratada na camada de aplicação, não na persistência.

### Variáveis de Ambiente - *Expandidas*

```bash
# ===========================================
# CONFIGURAÇÃO DO PROVEDOR LLM (NOVO)
# ===========================================
LLM_PROVIDER=gemini  # Valores: gemini | ollama

# ===========================================
# CONFIGURAÇÕES GEMINI (quando LLM_PROVIDER=gemini)
# ===========================================
GEMINI_API_KEY=sua_chave_api
GEMINI_MODEL=gemini-pro

# ===========================================
# CONFIGURAÇÕES OLLAMA (quando LLM_PROVIDER=ollama) [NOVO]
# ===========================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120
OLLAMA_TEMPERATURE=0.7
OLLAMA_NUM_PREDICT=2048
```


## 6. Detalhes Técnicos Chave - Atualizados

| Componente | Tecnologia | Uso Específico | Status |
| :--- | :--- | :--- | :--- |
| **Servidor API** | FastAPI, Uvicorn (ASGI) | Rotas, injeção de dependência, docs OpenAPI | ✅ Mantido |
| **Banco de Dados** | SQLAlchemy (ORM) + SQLite/PostgreSQL | Persistência de conversas e mensagens | ✅ Mantido |
| **Abstração LLM** | **ABC (Abstract Base Class)** | `LLMClientInterface` garante contrato comum | ✨ **Novo** |
| **Provider Cloud** | `google-generativeai` | Comunicação oficial com Gemini API | ✅ Atualizado (herda interface) |
| **Provider Local** | **`requests` + HTTP/REST** | Comunicação com API local do Ollama | ✨ **Novo** |
| **Factory Pattern** | Função `get_llm_client()` | Seleção dinâmica do provider via env var | ✨ **Novo** |
| **Validação** | Pydantic | Schemas `ChatRequest`/`ChatResponse` | ✅ Mantido |
| **Interface Cliente**| `requests`, `rich` | HTTP CLI + formatação terminal | ✅ Mantido |
| **Configuração** | `python-dotenv` | Carregamento seguro de variáveis de ambiente | ✅ Mantido |

## 7. Contratos de API - Preservados ✅

### Endpoint `/chat` (POST) - *Inalterado*

```json
// Request
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Qual é a capital do Brasil?"
}

// Response (mesmo schema para Gemini ou Ollama)
{
  "response": "A capital do Brasil é Brasília.",
  "conversation_id": 1,
  "message_id": 2,
  "tokens_used": 28
}
```

### Endpoint `/health` (GET) - *Enhanced*

```json
{
  "status": "healthy",
  "service": "Chatbot API",
  "llm_provider": "ollama"  // ← Novo campo informativo
}
```

### Endpoint `/models` (GET) - *Novo*

```json
// Quando LLM_PROVIDER=ollama
{
  "provider": "ollama",
  "models": ["llama2", "mistral", "llama3:8b"]
}

// Quando LLM_PROVIDER=gemini
{
  "provider": "gemini", 
  "models": ["gemini-pro"]
}
```


## 8. Matriz de Compatibilidade

| Funcionalidade | Gemini | Ollama | Frontend Impact |
|---------------|--------|--------|----------------|
| Envio de mensagem | ✅ | ✅ | ✅ Nenhum |
| Histórico de conversa | ✅ | ✅ | ✅ Nenhum |
| Schema de resposta | ✅ | ✅ | ✅ Nenhum |
| Estimativa de tokens | ✅ | ✅ (aproximada) | ✅ Nenhum |
| Tratamento de erros | ✅ | ✅ | ✅ HTTP 500 padrão |
| Configuração | Via env vars | Via env vars | ✅ Nenhum |
| **Troca de provider** | ⚙️ `.env` | ⚙️ `.env` | ✅ **Zero downtime** |


## 9. Guia Rápido de Configuração

### 🌐 Usando Google Gemini (Padrão)
```bash
# .env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-pro

# Iniciar
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 🖥️ Usando Ollama Local
```bash
# 1. Instalar Ollama: https://ollama.ai/download
# 2. Baixar modelo:
ollama pull llama2

# 3. Configurar .env:
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434

# 4. Iniciar API:
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 🔄 Alternar sem Reiniciar (Hot Reload em Dev)
```bash
# Com uvicorn --reload ativo, apenas edite .env:
LLM_PROVIDER=ollama  # ← muda de gemini para ollama
# A API recarrega automaticamente com o novo provider
```

## 10. Considerações para Futuras Extensões

Esta arquitetura baseada em interface (`LLMClientInterface`) foi projetada para facilitar a adição de novos provedores:

```python
# Exemplo: Adicionar OpenAI no futuro
# 1. Criar app/openai_client.py
class OpenAIClient(LLMClientInterface):
    def generate_response(self, prompt: str, context: str = None) -> Dict:
        # Implementação usando openai library
        pass

# 2. Atualizar factory em main.py:
def get_llm_client():
    provider = os.getenv("LLM_PROVIDER")
    if provider == "openai":
        from app.openai_client import OpenAIClient
        return OpenAIClient()
    # ... demais providers
```

> 🎯 **Princípio Aberto/Fechado**: O sistema está **aberto para extensão** (novos providers) mas **fechado para modificação** (código existente do frontend e contratos de API permanecem inalterados).

*Documento revisado e atualizado para a versão 2.0.0 em conformidade com a implementação de suporte multi-provider LLM.* 🚀