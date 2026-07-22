#!/usr/bin/env bash
#
# Start Finka locally: Postgres + API (docker), run migrations, then the frontend.
# Ctrl-C stops the frontend; the containers keep running (stop them with
# `docker compose down`). Requires Docker and Node.
#
set -euo pipefail
cd "$(dirname "$0")"

echo "▸ Starting Postgres + API (docker)…"
docker compose up -d

echo "▸ Waiting for the API on :8000…"
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do sleep 1; done

echo "▸ Applying database migrations…"
docker compose exec -T api alembic upgrade head

echo "▸ Starting the frontend on http://localhost:3000 …"
cd frontend
[ -d node_modules ] || npm install
npm run dev
