# AIOps Platform

Enterprise AI Operations Platform — monitor infrastructure, manage incidents, and use AI for log analysis and remediation guidance.

## Current status

**Module 01 — Authentication & User Management** (complete)  
**Module 02 — Organization & Role Management** (complete)  
**Module 03 — Infrastructure Inventory** (complete)

See [docs/PRD.md](docs/PRD.md), [docs/MODULE_01_AUTH.md](docs/MODULE_01_AUTH.md), [docs/MODULE_02_ORG_ROLES.md](docs/MODULE_02_ORG_ROLES.md), and [docs/MODULE_03_INVENTORY.md](docs/MODULE_03_INVENTORY.md).

## Quick start (local)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # or use the provided SQLite .env for local dev
uvicorn main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Docker Compose (PostgreSQL + API)

```bash
cd deployment
docker compose up --build
```

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Project layout

```
backend/     FastAPI application (clean architecture)
frontend/    React + TypeScript (upcoming)
deployment/  Docker Compose / Nginx
docs/        PRD and module specs
scripts/     Utility scripts
tests/       Cross-cutting tests (optional)
```
