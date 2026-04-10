#!/bin/bash
# Nuri-GPT 개발 서버 시작/종료 스크립트

BACKEND_PORT=8001
FRONTEND_PORT=5173
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
    pkill -f "uvicorn.*main:app" 2>/dev/null
    pkill -f "node_modules/.bin/vite" 2>/dev/null
    echo "✓ Servers stopped"
    exit 0
}

trap cleanup INT TERM

echo "🚀 Starting Nuri-GPT development servers..."
echo "   Backend:  http://localhost:$BACKEND_PORT"
echo "   Frontend: http://localhost:$FRONTEND_PORT"
echo ""

(cd "$SCRIPT_DIR/nuri-gpt-backend" && ./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT") &
BACKEND_PID=$!

(cd "$SCRIPT_DIR/nuri-gpt-frontend/frontend" && npm run dev) &
FRONTEND_PID=$!

echo "✅ Servers started! Press Ctrl+C to stop both."

wait "$BACKEND_PID" "$FRONTEND_PID"
