# Instruções

## 1. Instale as dependências
```bash
uv pip install -r requirements.txt
```

## 2. Execute a aplicação

### Conectar com localhost (padrão implícito)
```bash
uv run streamlit run app.py
```

### Conectar com IP específico
```bash
uv run streamlit run app.py -- http://192.168.1.100:8000
```

### Conectar com HTTPS
```bash
uv run streamlit run app.py -- https://api.meudominio.com
```

## 3. Acesse no navegador

http://localhost:8501
