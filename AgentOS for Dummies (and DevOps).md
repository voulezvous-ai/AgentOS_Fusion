# AgentOS Fusion – Operations & Development Manual

This manual distills the key operational, architectural, and deployment practices from the consolidated `6_AgentOS.pdf` used during the finalization of AgentOS Fusion.

---

## ⚙️ Core Concepts

- **Prompt-Driven Backend** using FastAPI
- **Agent Memory**:
  - Redis for short-term
  - MongoDB Atlas Vector Search for long-term
- **Command Execution**:
  - Tools (search, order status, customer lookup, etc.)
  - Handoff support (SalesAgent, SupportAgent...)
- **Real WebSocket** secured by JWT
- **Admin Panel** for monitoring sessions, logs, chat states

---

## 📋 API Highlights

- `POST /auth/login` — Bearer JWT issuance
- `GET /auth/me` — Authenticated profile fetch
- `GET /admin/status` — Websocket + log + chat info
- `WS /ws/updates` — Secured updates with token

---

## 🛡️ Security Practices

- All access via JWT (`Authorization: Bearer`)
- Role enforcement via `require_role()`
- Rate limiting via `slowapi` (`10/min` for login, etc.)
- Full `trace_id` injection for log tracing
- S2S stub token placeholder (`verify_s2s_token()`)

---

## 🧠 Memory System

- `get_short_term_memory(chat_id)` from Redis
- `add_to_short_term_memory(...)`
- `generate_embedding()` and `$vectorSearch` for docs/messages
- Simple PII masking filter included (`simple_pii_filter()`)

---

## 🧪 Testing & Observability

- Run all tests: `./scripts/run_tests.sh`
- Logging by `loguru`
- `trace_id` bound to each request
- Celery workers log `task_id` and errors

---

## 🔁 CI/CD and Deploy

- Use `.github/workflows/railway_ci_backend.yml`
- Push to `main` triggers:
  - Install
  - Test
  - (Railway auto-deploy)

> Railway uses `.railway/project.json` to resolve folders and services.

---

## 🔧 Dev Scripts

- `create_admin.py` — Initialize admin user
- `test_command_cli.py` — Local prompt tool test
- `db_stats.py` — Prints DB counts and indexes
- `run_tests.sh` — Full test runner

---

## 🧭 Troubleshooting

| Problem                 | Try This                             |
|------------------------|--------------------------------------|
| Redis not connecting   | Check `REDIS_URL` in `.env`          |
| Mongo vector search    | Confirm `$vectorSearch` index exists |
| Celery not running     | `docker-compose logs worker`         |
| WS not responding      | Ensure token is passed in URL        |

---

## 📝 Contributors Note

This project was built incrementally with production-level validation, architectural iteration, and DevOps refinement across several phases.

For a full architectural walk-through, refer to `6_AgentOS.pdf`.