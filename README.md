# AIOps Platform

Enterprise AI Operations Platform — monitor infrastructure, manage incidents, and use AI for log analysis and remediation guidance.

## Current status

All roadmap modules (01–10) are implemented:

| Module | Scope |
|--------|--------|
| 01 | Authentication & user management |
| 02 | Organization, teams, projects, RBAC |
| 03 | Infrastructure inventory |
| 04 | Monitoring & metrics |
| 05 | Alerting & notifications |
| 06 | Incidents (comments + attachments) |
| 07 | AI assistant & knowledge base |
| 08 | Dashboard & CSV reports |
| 09 | Audit log read/export |
| 10 | Docker Compose, Nginx, GitHub Actions CI |

See [docs/PRD.md](docs/PRD.md) and module specs in [docs/](docs/).

## Quick start (local)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- UI: http://localhost:5173 (proxies `/api` to the backend)

## Docker Compose (PostgreSQL + API + Nginx UI)

```bash
cd deployment
docker compose up --build
```

- UI + API proxy: http://localhost
- API direct: http://localhost:8000

## Tests

```bash
cd backend
pytest -q
```

## Project layout

```
backend/     FastAPI application (clean architecture)
frontend/    React + TypeScript + MUI dashboard
deployment/  Docker Compose, Nginx
docs/        PRD and module specs
.github/     CI workflows
```
