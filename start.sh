#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Boss Fight RL..."
echo ""

echo "[1/2] Starting backend on port 3000..."
cd "$SCRIPT_DIR/backend" && npm install && node src/index.js &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 2

echo "[2/2] Starting frontend on port 4200..."
cd "$SCRIPT_DIR/frontend" && npm install && npx ng serve

# On exit, kill backend
trap "kill $BACKEND_PID 2>/dev/null" EXIT
