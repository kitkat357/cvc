# 🚀 Quick Start Guide

## What You Have

✅ **React + FastAPI Chatbot** - Simple mock version for demos  
✅ **Custom RAG Pipeline** - Full production version (currently paused)  
✅ **All AWS services paused** - Costing ~$0.01/month  

---

## Run the Mock Chatbot (React + FastAPI)

Perfect for demos - **NO AWS REQUIRED!**

### Option 1: Simple Script

```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
./run_chatbot.sh
```

Then open **http://localhost:5173** in your browser!

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot/frontend
npm run dev
```

Then open **http://localhost:5173**

---

## Try These Queries

1. **"I'm a student attending Cal Poly and I want some help getting some GEs over the summer"**
   - Bot will interview you about GE areas

2. **"What is Cal-GETC?"**
   - Explains the new GE system

3. **"I need courses for Area 4"**
   - Shows social science courses

4. **"Show me math courses"**
   - Displays available math classes

---

## Resume Full RAG Pipeline (Production Version)

When you need real semantic search with 1,981 courses:

```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate

# Step 1: Create OpenSearch domain (~15 min)
python src/setup_opensearch_traditional.py

# Step 2: Create vector index (~1 min)
python src/create_opensearch_index_traditional.py

# Step 3: Upload data with embeddings (~10 min)
python src/upload_to_opensearch.py

# Step 4: Start custom RAG chatbot
streamlit run src/cvc_chatbot_custom_rag.py --server.port 8502
```

**Cost when active**: ~$20-40/month (60-75% cheaper than Serverless!)

---

## Stop/Pause Services

### Mock Chatbot
Just press Ctrl+C in the terminal

### Full RAG Pipeline
```bash
# Pause OpenSearch domain
aws opensearch delete-domain \
  --domain-name cvc-courses \
  --profile cvc-project \
  --region us-west-2

# Stop Streamlit
pkill -f "streamlit run"
```

**Cost when paused**: ~$0.01/month

---

## Documentation

- **REACT_CHATBOT_README.md** - Mock chatbot details
- **CUSTOM_RAG_SUMMARY.md** - Full RAG pipeline info
- **PAUSE_RESUME.md** - How to pause/resume AWS services
- **CLAUDE.md** - Complete project documentation

---

## Architecture Comparison

### Mock Chatbot (Current - Running)
```
React (5173) → FastAPI (8000) → Hardcoded Data
```
- **Cost**: $0
- **Setup**: 5 minutes
- **Use**: Demos, prototypes

### Full RAG Pipeline (Available - Paused)
```
Streamlit (8502) → Custom RAG → OpenSearch + Bedrock
```
- **Cost**: $20-40/month (when active)
- **Setup**: 30-40 minutes
- **Use**: Production, real users

---

## Quick Reference

| Task | Command |
|------|---------|
| **Start mock chatbot** | `./run_chatbot.sh` |
| **Check backend** | `curl http://localhost:8000/api/health` |
| **View frontend** | Open http://localhost:5173 |
| **Resume RAG pipeline** | See CUSTOM_RAG_SUMMARY.md |
| **Check AWS status** | `python src/check_status.py` |

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Activate virtual environment
source .venv/bin/activate
```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### "Can't connect to server"
Make sure backend is running on port 8000 first!

---

**Current Status**: Mock chatbot ready to run, AWS services paused  
**Monthly Cost**: ~$0.01 (just S3 storage)  
**Ready to Demo**: Yes! Just run `./run_chatbot.sh` 🎉
