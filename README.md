<p align="center">
  <h1 align="center">🧠 OmniSLM</h1>
  <p align="center">
    <strong>The open-source AI framework for Small Language Models.</strong>
  </p>
  <p align="center">
    Build AI assistants, RAG applications, and autonomous agents — locally or self-hosted.
  </p>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#api">API</a> •
  <a href="#roadmap">Roadmap</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Features

- 🧠 **Multi-Runtime Model Engine** — Ollama, llama.cpp, vLLM, HuggingFace
- 📄 **RAG Pipeline** — PDF, DOCX, Web, GitHub → Chunk → Embed → Retrieve → Rerank
- 🤖 **Agent Framework** — Planner, Research, Coding, Reviewer, Executor agents
- 🔧 **Tool Calling** — Calculator, file ops, database, REST APIs, custom plugins
- 🔄 **Workflow Engine** — DAG pipelines, scheduling, agent orchestration
- 💾 **4-Tier Memory** — Session, conversation, long-term, user memory
- 🏢 **Enterprise** — Multi-tenancy, RBAC, OAuth2, audit logs, billing
- 📱 **Cross-Platform** — Web (Next.js), Mobile (Flutter), Desktop (Flutter)
- 📊 **Observability** — Prometheus metrics, structured logging, health checks
- 🚀 **Deploy Anywhere** — Docker Compose, Kubernetes, or bare metal

## Supported Models

| Family | Models | Parameters |
|--------|--------|------------|
| **Qwen** | Qwen 2.5 | 0.5B – 72B |
| **Gemma** | Gemma 3 | 1B – 27B |
| **Phi** | Phi-4 | 3.8B – 14B |
| **Llama** | Llama 3.2 | 1B – 90B |
| **Mistral** | Mistral 7B, Mixtral | 7B – 47B |

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- (Optional) NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)

### 1. Clone & Setup

```bash
git clone https://github.com/your-username/omnislm.git
cd omnislm
cp .env.example .env
```

### 2. Start All Services

```bash
docker compose up -d
```

This starts:
- **API Server** → http://localhost:8000
- **Swagger Docs** → http://localhost:8000/docs
- **PostgreSQL** → localhost:5432
- **Redis** → localhost:6379
- **Ollama** → localhost:11434

### 3. Pull Your First Model

```bash
curl -X POST http://localhost:8000/api/v1/models/pull \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "qwen2.5:3b"}'
```

### 4. Start Chatting

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:3b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Client Layer                      │
│        Web (Next.js)  •  Mobile/Desktop (Flutter)    │
├─────────────────────────────────────────────────────┤
│                  API Gateway (FastAPI)                │
│     Auth  •  Rate Limiting  •  Request Routing       │
├─────────────────────────────────────────────────────┤
│               Application Services                   │
│   Chat  •  RAG  •  Agents  •  Memory  •  Workflow    │
├─────────────────────────────────────────────────────┤
│                 Core Domain Layer                     │
│  Prompt Engine  •  Memory Engine  •  Agent Framework  │
├─────────────────────────────────────────────────────┤
│              AI Inference Layer                       │
│     Ollama  •  llama.cpp  •  vLLM  •  HuggingFace   │
├─────────────────────────────────────────────────────┤
│                   Data Layer                         │
│     PostgreSQL  •  Redis  •  Qdrant  •  S3           │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database | PostgreSQL 16, Redis 7, Qdrant |
| AI | Ollama, llama.cpp, vLLM, HuggingFace Transformers |
| Frontend | Next.js 14+ |
| Mobile/Desktop | Flutter |
| DevOps | Docker, Kubernetes, GitHub Actions |
| Observability | Prometheus, structlog, OpenTelemetry |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/register` | Register new user |
| `POST /api/v1/auth/login` | Login & get JWT |
| `GET /api/v1/models` | List available models |
| `POST /api/v1/models/pull` | Download a model |
| `POST /api/v1/chat/completions` | Streaming chat completion |
| `GET /api/v1/conversations` | List conversations |
| `GET /healthz` | Liveness probe |
| `GET /readyz` | Readiness probe |

Full API docs at http://localhost:8000/docs

## Development

```bash
# Install dependencies
pip install poetry
poetry install

# Run locally
make dev

# Run tests
make test

# Lint & format
make lint
make format
```

## Roadmap

- [x] **Phase 1**: MVP — Model engine, chat API, auth, Docker
- [ ] **Phase 2**: Memory + RAG pipeline
- [ ] **Phase 3**: Agent framework + workflows
- [ ] **Phase 4**: Enterprise features (RBAC, billing, MLOps)
- [ ] **Phase 5**: AI ecosystem (marketplace, mobile/desktop apps)

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting PRs.

## License

[Apache License 2.0](LICENSE)

---

<p align="center">
  Built with ❤️ for the open-source AI community
</p>
