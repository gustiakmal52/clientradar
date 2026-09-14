#!/bin/bash
# ==============================================================================
# ClientRadar — Developer Prospecting & Web Audit Engine
# Author: Gustiakmal
# ==============================================================================

echo "⚡ Starting ClientRadar by Gustiakmal..."

# 1. Start Backend in background
echo "-> Starting Backend API (FastAPI) on http://localhost:8000..."
cd /home/utopia/redteam_next/Project2/server
../venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 2. Start Frontend
echo "-> Starting Frontend (Vite React) on http://localhost:5173..."
cd /home/utopia/redteam_next/Project2/client
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo "=========================================================="
echo "  ClientRadar is running successfully!"
echo "  Frontend UI:  http://localhost:5173"
echo "  Backend API:  http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Author:       Gustiakmal"
echo "=========================================================="
echo "Press Ctrl+C to stop all services."

# Trap SIGINT and SIGTERM to kill background processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

wait
