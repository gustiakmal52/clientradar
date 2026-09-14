#!/bin/bash
# ==============================================================================
# ClientRadar — Developer Prospecting & Web Audit Engine
# Author: Gustiakmal
# ==============================================================================

set -e

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_HOST="${CLIENTRADAR_HOST:-127.0.0.1}"

echo "⚡ Starting ClientRadar by Gustiakmal..."

# Clean up both children even when either process fails during startup.
trap 'kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true' EXIT INT TERM

# 1. Start Backend in background
echo "-> Starting Backend API (FastAPI) on http://localhost:8000..."
(cd "$PROJECT_DIR/server" && "$PROJECT_DIR/venv/bin/python3" -m uvicorn app.main:app --host "$APP_HOST" --port 8000) &
BACKEND_PID=$!

# 2. Start Frontend
echo "-> Starting Frontend (Vite React) on http://localhost:5173..."
(cd "$PROJECT_DIR/client" && npm run dev -- --host "$APP_HOST" --strictPort) &
FRONTEND_PID=$!

sleep 1
if ! kill -0 "$BACKEND_PID" 2>/dev/null || ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "Gagal menjalankan backend atau frontend. Periksa dependency dan port 8000/5173." >&2
  exit 1
fi

echo ""
echo "=========================================================="
echo "  ClientRadar is running successfully!"
echo "  Frontend UI:  http://localhost:5173"
echo "  Backend API:  http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Author:       Gustiakmal"
echo "=========================================================="
echo "Press Ctrl+C to stop all services."

wait
