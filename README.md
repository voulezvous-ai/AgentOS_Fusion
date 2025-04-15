# AgentOS Fusion – Production-Ready AI Automation Platform

Welcome to the **AgentOS Fusion** backend. This is a high-performance, modular, and secure backend system powered by FastAPI, Celery, Redis, MongoDB, and JWT authentication. Built for real-time conversational agents, secure admin panels, and tool-integrated AI workflows — all deployable via **Railway**.

---

## 🔒 Features

- ✅ JWT Auth (no mocks, real DB)
- ✅ Admin panel with WS session viewer, recent logs, chat modes
- ✅ WebSocket secured with JWT
- ✅ Redis short-term memory
- ✅ MongoDB Atlas long-term memory (Vector Search)
- ✅ Tool-based AI via MCP (multi-tool command pattern)
- ✅ Agent Handoff between personas (SalesAgent, SupportAgent etc.)
- ✅ Secure service-to-service (S2S) stub tokens
- ✅ Full exception handling with JSON response models
- ✅ Rate limiting via `slowapi`
- ✅ Production-ready Dockerfile + Gunicorn + CI/CD workflow

---

## 📁 Project Structure (Backend)

```
promptos_backend/
├── app/
│   ├── api/              # Endpoints (auth, websocket, admin, etc)
│   ├── core/             # Security, config, logging, redis
│   ├── db/               # Mongo connection & schemas
│   ├── models/           # Pydantic schemas for admin panel etc.
│   ├── services/         # UserService, AI service, memory
│   ├── tools/            # MCP tool wrappers
├── gunicorn_conf.py
├── Dockerfile
```

---

## 🚀 Deployment (Railway)

> You can deploy automatically via GitHub integration **OR** Railway CLI.

### 📦 Prerequisites

- [x] Railway account
- [x] MongoDB URI + Redis URI
- [x] `.env` file with your config (see `.env.example`)
- [x] Project linked to GitHub

### 🛠️ Using Railway CLI

```bash
railway up
```

This will auto-detect:
- `.railway/project.json`
- Backend service in `promptos_backend/`
- Dockerfile + Port 8000

---

## 🧪 Testing Locally

Run the backend:

```bash
cd promptos_backend
uvicorn app.main:app --reload
```

Run the test suite:

```bash
./scripts/run_tests.sh
```

---

## 🔐 Environment Variables (.env)

```
JWT_SECRET_KEY=your-secret
MONGO_URI=mongodb://...
MONGO_DB_NAME=agentos
REDIS_URL=redis://localhost:6379
USE_ATLAS_VECTOR_SEARCH=true
AGENT_USE_VECTOR_MEMORY=true
TAVILY_API_KEY=your-tavily-key
```

---

## 📜 License

MIT License — see `LICENSE`

---

## 🙌 Credits

Developed by Daniel Amarilho and collaborators.  
See the `6_AgentOS.pdf` for full architectural decisions and rationale.