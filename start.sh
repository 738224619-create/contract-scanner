#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "🔧 启动 AI 合同风险扫描..."
echo ""

# 后端
echo "→ 启动后端 (端口 8000)..."
cd backend
source venv/bin/activate 2>/dev/null || true
../venv/bin/python -m uvicorn main:app --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
cd ..

sleep 3

# 前端
echo "→ 启动前端 (端口 5173)..."
cd frontend
npx vite --host 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ 后端: http://localhost:8000"
echo "✅ 前端: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
