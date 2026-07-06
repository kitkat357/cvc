#!/bin/bash

# Script to run React + FastAPI with REAL RAG pipeline
# Uses OpenSearch + Bedrock (Claude Haiku + Titan)
# ⚠️ COSTS: ~$20-40/month when active

echo "🚀 Starting React Chatbot with RAG Pipeline..."
echo ""
echo "⚠️  WARNING: This uses AWS Bedrock API (costs apply)"
echo "   - Titan Embeddings for query vectors"
echo "   - Claude Haiku for responses"
echo "   - OpenSearch for vector search"
echo ""
echo "💰 Estimated cost: ~$20-40/month when active"
echo ""

# Check if OpenSearch is ready
echo "📊 Checking OpenSearch status..."
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate

OPENSEARCH_STATUS=$(aws opensearch describe-domain --domain-name cvc-courses --profile cvc-project --region us-west-2 --query 'DomainStatus.Processing' --output text 2>&1)

if [ "$OPENSEARCH_STATUS" != "False" ]; then
    echo "❌ OpenSearch domain is not ready yet"
    echo "   Run: python src/setup_opensearch_traditional.py"
    exit 1
fi

echo "✅ OpenSearch is ready"
echo ""

# Start backend with RAG
echo "📦 Starting FastAPI backend with RAG on port 8000..."
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate
cd backend
python app_rag.py > /tmp/backend_rag.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
sleep 3

# Check backend health
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "   ✅ Backend is running with RAG"
    echo ""
    echo "   Backend features:"
    curl -s http://localhost:8000/ | python -m json.tool 2>/dev/null | grep -A 10 "features" || echo "   - RAG pipeline active"
else
    echo "   ❌ Backend failed to start"
    cat /tmp/backend_rag.log
    exit 1
fi

echo ""
echo "⚛️  Starting React frontend on port 5173..."
cd /Users/rishikajain/claude/cvc-rag-chatbot/frontend
npm run dev

# This will block here. When you Ctrl+C, kill backend too
kill $BACKEND_PID
