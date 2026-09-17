#!/usr/bin/env bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=================================================================="
echo "    🚀 Launching Cymbal AI Leadership Simulator Local Stack      "
echo "=================================================================="

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down backend and frontend services..."
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo "Done."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 1. Install frontend node dependencies if needed
echo "📦 Installing frontend dependencies..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install --silent
fi

# 2. Check if ports 8000 or 3002 are occupied and free them if necessary
for PORT in 8000 3002; do
    PID=$(lsof -ti:$PORT 2>/dev/null || true)
    if [ -n "$PID" ]; then
        echo "⚠️ Port $PORT is in use by process $PID. Freeing port..."
        kill -9 $PID 2>/dev/null || true
    fi
done

# 3. Launch Backend (FastAPI on Port 8000)
echo "🐍 Starting FastAPI Backend on http://localhost:8000..."
cd "$SCRIPT_DIR/backend"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait briefly for backend startup
sleep 2

# 4. Launch Frontend (Express on Port 3002)
echo "🌐 Starting Frontend Workspace Dashboard on http://localhost:3002..."
cd "$SCRIPT_DIR/frontend"
PORT=3002 node server.js &
FRONTEND_PID=$!

# Wait briefly for frontend startup
sleep 1

echo "=================================================================="
echo "  ✅ Cymbal Leadership Simulator is UP and RUNNING!               "
echo "  --------------------------------------------------------------  "
echo "  📌 Workspace UI:   http://localhost:3002                        "
echo "  📌 Backend API:    http://localhost:8000                        "
echo "  📌 OpenAPI Docs:   http://localhost:8000/docs                   "
echo "=================================================================="
echo "Press CTRL+C to stop all servers."

# Keep launcher process alive
wait
