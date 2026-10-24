#!/usr/bin/env bash
#
# Start Finka locally: Postgres, API and frontend (all docker), run migrations,
# seed the local user. Stop with `docker compose down`. Requires Colima
# (`brew install colima docker docker-compose`).
#
set -euo pipefail
cd "$(dirname "$0")"

# --demo: a throwaway copy with fictional data, in its own Docker project (own
# database volume), so it can never touch your real data. Stop your real stack
# first: both use the same ports.
DEMO=0
if [ "${1:-}" = "--demo" ]; then
  DEMO=1
  export COMPOSE_PROJECT_NAME=finka-demo
  echo "▸ Demo mode: fictional data, separate database (project: finka-demo)"
fi

# Colima doesn't auto-start like Docker Desktop does, so bring the VM up first.
# Memory capped at 4g to match the containers' own mem_limits in compose.yml.
if command -v colima >/dev/null 2>&1 && ! colima status >/dev/null 2>&1; then
  echo "▸ Starting Colima…"
  colima start --cpu 4 --memory 4 --disk 60
fi

echo "▸ Starting Postgres + API (docker)…"
docker compose up -d --build

echo "▸ Waiting for the API on :8000…"
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do sleep 1; done

echo "▸ Applying database migrations…"
docker compose exec -T api alembic upgrade head

# Auth is stubbed (single local user), so every API call 500s until this user
# exists. Idempotent: safe to run on every start.
if [ "$DEMO" = 1 ]; then
  echo "▸ Seeding demo data…"
  docker compose exec -T api python -m scripts.seed_demo
else
  echo "▸ Seeding the local user and sample accounts…"
  docker compose exec -T api python -m scripts.seed
fi

echo "▸ Waiting for the frontend on :3000…"
until curl -sf http://localhost:3000 >/dev/null 2>&1; do sleep 2; done

echo "✓ Finka is running at http://localhost:3000 (stop with: docker compose down)"
if [ "$DEMO" = 1 ]; then echo "  Remove the demo data with: COMPOSE_PROJECT_NAME=finka-demo docker compose down -v"; fi
