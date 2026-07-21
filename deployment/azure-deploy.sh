#!/usr/bin/env bash
# Deploy on Azure VM (or any Linux host). Run from repo root or deployment/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/deployment"

if [[ ! -f .env ]]; then
  echo "Missing deployment/.env — copy .env.example and set FRONTEND_URL + BOOTSTRAP_* for your VM IP."
  exit 1
fi

echo "==> Pulling latest main..."
git -C "$ROOT" pull origin main

echo "==> Building and starting containers (web build may take 5–15 min on small VMs)..."
docker compose up --build -d

echo "==> Waiting for API health..."
for i in $(seq 1 36); do
  if curl -sf http://127.0.0.1/health >/dev/null 2>&1; then
    echo "API is healthy."
    break
  fi
  if [[ "$i" -eq 36 ]]; then
    echo "Health check timed out. Run: docker compose logs api --tail 80"
    exit 1
  fi
  sleep 5
done

docker compose ps
echo ""
echo "Open: $(grep -E '^FRONTEND_URL=' .env | cut -d= -f2- || echo 'http://YOUR_VM_IP')"
echo "If login fails on a fresh DB, register a new account or set BOOTSTRAP_ADMIN_EMAIL in .env and redeploy."
