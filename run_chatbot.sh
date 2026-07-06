#!/bin/bash

# Script to run React + FastAPI chatbot

echo "🚀 Starting CVC React Chatbot..."
echo ""

# Activate virtual environment and start backend
echo "📦 Starting FastAPI backend on port 8000..."
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate
cd backend
python app.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
sleep 2

# Check backend health
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "   ✅ Backend is running"
else
    echo "   ❌ Backend failed to start"
    cat /tmp/backend.log
    exit 1
fi

echo ""
echo "⚛️  Starting React frontend on port 5173..."
cd /Users/rishikajain/claude/cvc-rag-chatbot/frontend
npm run dev

# This will block here. When you Ctrl+C, kill backend too
kill $BACKEND_PID
