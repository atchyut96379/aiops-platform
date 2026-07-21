#!/bin/sh
set -e
alembic upgrade head
python scripts/bootstrap_admin.py
exec uvicorn main:app --host 0.0.0.0 --port 8000
