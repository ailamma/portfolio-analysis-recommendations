#!/bin/bash
# init.sh - Start dev environment and run smoke test
set -e

echo "=== Portfolio Advisor Dev Environment ==="

# Install backend deps
cd "$(dirname "$0")"
poetry install --no-root

# Install frontend deps
cd frontend && npm install && cd ..

# Start backend in background
poetry run uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Start frontend dev server in background
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Smoke test: checking /health endpoint..."
sleep 3
curl -s http://localhost:8000/health && echo " ✓ Backend healthy"

echo ""
echo "PIDs: backend=$BACKEND_PID frontend=$FRONTEND_PID"
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"
