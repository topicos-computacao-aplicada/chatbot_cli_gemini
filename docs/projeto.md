# Sistema de Chatbot com LLM e Persistência de Contexto

Solução de aplicação de IA Generativa, abrangendo o cliente terminal, a API de *backend* e a integração do LLM.

## Documento de Requisitos de Software (DRS)
### Solução: Sistema de Chatbot com LLM e Persistência de Contexto

| Atributo | Descrição |
| :--- | :--- |
| **Nome do Projeto** | AI Chat Context Gateway (ACCG) |
| **Versão** | 1.0.0 |
| **Data** | Outubro/2025 |
| **Elaborado Por** | Armando Soares |

### 1. Introdução

Esta solução é um sistema de *chatbot* dividido em três camadas principais (Cliente Terminal, API Gateway, LLM Client) que permite aos usuários interagir com um Modelo de Linguagem Grande (LLM) de forma persistente. O objetivo principal é fornecer um mecanismo robusto para gerenciar o estado da conversa (*histórico*) e fornecer uma interface de usuário simples.

### 2. Arquitetura da Solução

O sistema adota uma arquitetura Cliente-Servidor e de três camadas:

1.  **Cliente (Frontend):** Aplicação de linha de comando (CLI) que gerencia a entrada/saída do usuário.
2.  **API Gateway (Backend/Servidor):** Um serviço RESTful (FastAPI) que expõe *endpoints*, gerencia a persistência de dados (SQLAlchemy) e orquestra a chamada ao LLM.
3.  **LLM Client:** Módulo Python (GeminiClient) que abstrai a comunicação com o serviço de IA (Google Gemini) e aplica regras básicas de *Prompt Engineering*.

### 3. Requisitos Funcionais (RF)

| ID | Módulo | Requisito |
| :--- | :--- | :--- |
| **RF-001** | Cliente | **Iniciar Sessão:** O cliente deve gerar e manter um ID de sessão único (UUID) no início da execução para rastrear a conversa. |
| **RF-002** | Cliente | **Comunicação:** O cliente deve ser capaz de enviar mensagens do usuário via requisição **HTTP POST** para o *endpoint* `/chat` da API, incluindo o ID da sessão e a mensagem. |
| **RF-003** | Cliente | **Comandos:** O cliente deve suportar os comandos internos `sair`, `ajuda` e `historico`, gerenciando-os localmente sem chamar a API (exceto `historico`). |
| **RF-004** | API | **Persistência de Conversa:** O *backend* deve criar ou recuperar uma entidade `Conversation` (sessão) no banco de dados com base no `session_id` fornecido pelo cliente. |
| **RF-005** | API | **Registro de Mensagem:** O *backend* deve salvar a mensagem do usuário e a resposta do assistente no banco de dados (`Message` com *roles* `user` e `assistant`). |
| **RF-006** | API | **Gerenciamento de Contexto:** Antes de chamar o LLM, o *backend* deve recuperar as **últimas N (N=5)** mensagens da conversa para construir uma *string* de contexto (memória). |
| **RF-007** | LLM Client | **Geração de Resposta:** O LLM Client deve chamar a API do Gemini, passando a nova pergunta do usuário e a *string* de contexto (histórico). |
| **RF-008** | LLM Client | **Persona:** O LLM Client deve injetar um *system prompt* básico de "Assistente útil e prestativo" em todas as chamadas. |
| **RF-009** | API | **Recuperação de Histórico:** O *backend* deve expor um *endpoint* **HTTP GET** `/conversations/{session_id}` que retorna toda a lista de mensagens associadas àquela sessão. |
| **RF-010** | Cliente | **Visualização de Histórico:** O cliente deve chamar o *endpoint* de recuperação de histórico (`RF-009`) e exibir todas as mensagens salvas ao comando `historico`. |

### 4. Requisitos Não-Funcionais (RNF)

| ID | Categoria | Requisito |
| :--- | :--- | :--- |
| **RNF-001** | Performance | A latência da API (tempo de resposta excluindo o tempo de chamada do LLM) deve ser inferior a 100ms. |
| **RNF-002** | Escalabilidade | A API deve ser implementada de forma **assíncrona (ASGI)** para suportar a manipulação eficiente de I/O Bound (espera pela resposta do LLM) e potencialmente escalar para lidar com múltiplas sessões simultâneas. |
| **RNF-003** | Segurança | Todas as chaves de API (`GEMINI_API_KEY`) e configurações sensíveis devem ser carregadas a partir de **variáveis de ambiente** ou arquivos `.env` e **nunca** codificadas no repositório. |
| **RNF-004** | Usabilidade | O Cliente CLI deve utilizar bibliotecas de formatação (`rich`) para melhorar a legibilidade (cores, painéis, *markdown*) das entradas e saídas. |
| **RNF-005** | Manutenibilidade | O código deve aderir aos **Python Type Hints** e o *backend* deve gerar documentação OpenAPI/Swagger automaticamente (via FastAPI) para todos os *endpoints*. |
| **RNF-006** | Robustez | A API deve implementar tratamento de erros (`try/except` e `db.rollback()`) e retornar códigos de status HTTP apropriados (200, 400, 404, 500). |

### 5. Requisitos de Dados (RD)

#### **Modelo de Dados (Via SQLAlchemy)**

| Tabela | Campo | Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| **Conversation** | `id` | Integer (PK) | ID primário |
| | `session_id` | String | ID único para rastreamento de sessão (UUID) |
| | `created_at` | Timestamp | Data/hora da criação da sessão |
| **Message** | `id` | Integer (PK) | ID primário |
| | `conversation_id`| Integer (FK) | Chave estrangeira para `Conversation` |
| | `role` | String | Papel: "user" ou "assistant" |
| | `content` | Text | Conteúdo da mensagem |
| | `tokens_used` | Integer | Estimativa ou contagem real de *tokens* (para o assistente) |
| | `timestamp` | Timestamp | Data/hora do envio da mensagem |

### 6. Detalhes Técnicos Chave

| Componente | Tecnologia | Uso Específico |
| :--- | :--- | :--- |
| **Servidor API** | FastAPI, Uvicorn (ASGI) | Gerenciamento de rotas e alta performance assíncrona. |
| **Banco de Dados** | SQLAlchemy (ORM) | Persistência de `Conversation` e `Message`. |
| **Cliente LLM** | `google-generativeai` | Comunicação direta e oficial com o LLM. |
| **Validação** | Pydantic | Definição dos *schemas* (`ChatRequest`, `ChatResponse`) para validação de entrada/saída no FastAPI. |
| **Interface Cliente**| `requests`, `rich` | Requisições HTTP e formatação avançada do terminal. |
