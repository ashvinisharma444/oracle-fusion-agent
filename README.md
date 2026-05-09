# Oracle Fusion AI Autonomous Diagnostic Agent
## Phase 1 — Read-Only Enterprise Platform

AI-powered diagnostic platform for Oracle Fusion Cloud using Gemini 2.5 Pro, Playwright browser automation, and ChromaDB vector knowledge retrieval.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js 14 Frontend (Port 3000)              │
│  Login · Dashboard · RCA Viewer · Sessions · Knowledge Search  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ JWT-authenticated REST
┌──────────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend (Port 8000)                   │
│  Auth · Analyze · Sessions · Knowledge · Health                │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ DiagnosticService│  │ PlaywrightAdapter │  │GeminiAdapter │  │
│  │ (Orchestrator)  │  │ (Browser Pool)   │  │(AI Provider) │  │
│  └────────┬────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                    │                    │          │
│  ┌────────▼────────────────────▼────────────────────▼───────┐  │
│  │           Infrastructure Layer                           │  │
│  │  PostgreSQL  │  Redis  │  ChromaDB  │  Playwright       │  │
│  └──────────────┴─────────┴────────────┴───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │ Browser Automation (READ-ONLY)
┌──────────────────────────▼──────────────────────────────────────┐
│                   Oracle Fusion Cloud                           │
│  Subscription Mgmt · Order Mgmt · DOO · Billing · Pricing     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker + Docker Compose
- Google AI Studio API key (Gemini 2.5 Pro)
- Oracle Fusion service account credentials

---

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env — fill in GEMINI_API_KEY, ORACLE_FUSION_*, JWT_SECRET_KEY, DB passwords
```

### 2. Start with Docker Compose (recommended)

```bash
make docker-up
```

This starts: PostgreSQL, Redis, ChromaDB, FastAPI backend, Next.js frontend, Nginx.

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

### 3. Seed knowledge base

```bash
make ingest-knowledge
```

### 4. Create first admin user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@company.com", "password": "SecurePassword123!", "role": "admin"}'
```

### 5. Log in and run a diagnostic

Login at http://localhost:3000, navigate to **Run Diagnostic**, enter an Oracle Fusion subscription or order number.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/login` | POST | Authenticate → JWT tokens |
| `/api/v1/analyze/subscription` | POST | RCA for subscription record |
| `/api/v1/analyze/order` | POST | RCA for order record |
| `/api/v1/analyze/orchestration` | POST | RCA for DOO process |
| `/api/v1/sessions` | GET/POST | Manage browser sessions |
| `/api/v1/knowledge/search` | POST | Semantic knowledge search |
| `/api/v1/knowledge/ingest` | POST | Ingest documents |
| `/health` | GET | System health check |

---

## Phase 1 Constraints (READ-ONLY)

The agent will **never**:
- Create, update, or delete any Oracle Fusion records
- Submit forms or trigger transactions
- Modify configuration

All Playwright page objects expose only navigation and extraction methods.

---

## Security

- JWT HS256 tokens (60 min access, 7 day refresh)
- RBAC: ADMIN · ANALYST · VIEWER roles
- All secrets via environment variables only
- Structured audit logging with correlation IDs
- Rate limiting on all API endpoints

---

## Adding Oracle Knowledge

```python
# Via API
curl -X POST http://localhost:8000/api/v1/knowledge/ingest \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": ["Your Oracle doc content here..."],
    "collection": "oracle_docs",
    "module": "subscription",
    "source": "Oracle Help Center"
  }'
```

---

## AI Provider Swapping (Gemini → Claude)

The `AIProvider` interface in `backend/app/domain/interfaces/ai_port.py` is provider-agnostic.
To switch to Claude:
1. Implement `ClaudeAdapter(AIProvider)` in `backend/app/infrastructure/ai/`
2. Update `get_ai_provider()` factory in `gemini_adapter.py`
3. No other code changes required

---

## Phase 2 Roadmap

- MCP server integration for autonomous multi-step workflows
- Multi-agent orchestration (Subscription Agent + Order Agent + Billing Agent)
- Scheduled diagnostic runs with alerting
- Write operations (admin-approved, audit-logged)
- Slack/Teams/ServiceNow integration for auto-ticket creation
- Oracle REST API integration alongside browser automation
