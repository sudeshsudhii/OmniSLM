# OmniSLM API Server

The reference implementation of a production-grade AI application built with OmniSLM.

## Features

- JWT authentication + multi-tenant support
- Chat completions (streaming and non-streaming)
- Model management (list, pull, info)
- Health checks (liveness + readiness)
- Conversation history (PostgreSQL)
- Rate limiting and CORS

## Quick Start

```bash
# From the project root
cd apps/api-server

# Install dependencies
pip install -e .

# Start the server
python -m src.main
# or
omnislm run --config omnislm.yaml
```

## Architecture

This app uses the OmniSLM framework SDK — it does NOT contain framework logic.
All framework capabilities (runtimes, memory, RAG, agents) come from `pip install omnislm`.

```python
from omnislm import OmniSLM

app = OmniSLM.from_config("omnislm.yaml")
app.enable_auth()
app.enable_memory()
app.run()
```

The app adds:
- Custom API routes (auth, chat, models)
- Database models (SQLAlchemy ORM)
- App-specific services (ChatService, AuthService)
