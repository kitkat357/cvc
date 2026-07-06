# React + FastAPI Chatbot (Mock Version)

Simple conversational GE chatbot for Cal Poly students - no RAG pipeline needed for demos.

## Architecture

```
React Frontend (Port 5173)
    ↓ HTTP REST API
FastAPI Backend (Port 8000)
    ↓
Hardcoded course data + conversation logic
```

## Features

✅ Conversational interviewing about GE requirements  
✅ Explains GE systems (IGETC, Cal-GETC, Cal-Breadth)  
✅ Shows courses that satisfy specific GE areas  
✅ Clickable suggestions for easy navigation  
✅ Clean, modern UI with CVC branding  
✅ No AWS/OpenSearch required - perfect for demos!

## Setup Instructions

### Backend (FastAPI)

```bash
# Navigate to backend
cd /Users/rishikajain/claude/cvc-rag-chatbot/backend

# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python app.py
# Or: uvicorn app:app --reload
```

Backend will run on **http://localhost:8000**

### Frontend (React)

```bash
# Navigate to frontend
cd /Users/rishikajain/claude/cvc-rag-chatbot/frontend

# Install dependencies (if not already done)
npm install

# Run dev server
npm run dev
```

Frontend will run on **http://localhost:5173**

## Usage

1. Start the backend: `python backend/app.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Open **http://localhost:5173** in your browser
4. Chat with the bot!

### Example Conversations

**Example 1: Learning about GE systems**
- User: "What is Cal-GETC?"
- Bot: Explains Cal-GETC and shows all areas
- Suggestions: "I need Area 3 courses", "What about IGETC?"

**Example 2: Finding courses**
- User: "I need courses for Area 4"
- Bot: Shows social science courses (Sociology, Psychology)
- Displays course cards with GE area badges

**Example 3: Subject search**
- User: "Show me math courses"
- Bot: Displays MATH 104 (Calculus)
- Shows what GE areas it satisfies

## Mock Data

The backend includes hardcoded mock data for:
- 10 sample courses across multiple colleges
- IGETC area definitions
- Cal-GETC area definitions
- Cal-Breadth information

### Colleges Included
- Cerritos College
- Victor Valley College
- Mount San Antonio College

### Sample Courses
- ENGL 101 - English Composition (Area 1A)
- MATH 104 - Calculus I (Area 2)
- SOC 101 - Intro to Sociology (Area 4)
- BIO 101 - General Biology (Area 5B)
- ES 101 - Introduction to Ethnic Studies (Cal-GETC Area 6)

## API Endpoints

### POST /api/chat
Send a message and get bot response.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "What is Cal-GETC?"}
  ],
  "context": {}
}
```

**Response:**
```json
{
  "response": "Cal-GETC explanation...",
  "suggestions": [
    "I need Area 3 courses",
    "What about IGETC?"
  ],
  "courses": null
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Customization

### Adding More Courses

Edit `backend/app.py` and add to the `MOCK_COURSES` list:

```python
{
    "course_code": "HIST 101",
    "title": "US History",
    "college": "Your College",
    "units": "3",
    "ge_areas": ["IGETC 4", "Cal-GETC 4"],
    "description": "Survey of US history."
}
```

### Changing Colors/Branding

Edit `frontend/src/components/Chatbot.css`:

```css
.chatbot-header {
  background: linear-gradient(135deg, #003366 0%, #004d99 100%); /* CVC Blue */
}

.ge-badge {
  background: #FDB913; /* CVC Gold */
  color: #003366;
}
```

### Adding New Conversation Patterns

Edit `backend/app.py` in the `get_bot_response()` function:

```python
if "your keyword" in user_message:
    return ChatResponse(
        response="Your custom response",
        suggestions=["Option 1", "Option 2"]
    )
```

## Project Structure

```
cvc-rag-chatbot/
├── backend/
│   ├── app.py              # FastAPI server with conversation logic
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chatbot.jsx    # Main chatbot component
│   │   │   └── Chatbot.css    # Chatbot styling
│   │   ├── App.jsx            # Root component
│   │   └── App.css            # Global styles
│   ├── package.json           # Node dependencies
│   └── vite.config.js         # Vite configuration
└── REACT_CHATBOT_README.md   # This file
```

## Differences from Full RAG Version

| Feature | Mock Version | Full RAG Version |
|---------|-------------|------------------|
| **Data Source** | Hardcoded in Python | OpenSearch with embeddings |
| **Search** | Keyword matching | Semantic vector search |
| **LLM** | None (predefined responses) | Claude Haiku via Bedrock |
| **Cost** | $0 | ~$20-40/month |
| **Setup Time** | 5 minutes | 30-40 minutes |
| **Use Case** | Demos, prototypes | Production, real users |

## Advantages of Mock Version

✅ **Zero Cost** - No AWS services needed  
✅ **Fast Setup** - Ready in minutes  
✅ **Predictable** - Hardcoded responses for demos  
✅ **Offline** - Works without internet (after npm install)  
✅ **Easy to Customize** - Just edit Python dicts  

## When to Use Each Version

**Use Mock Version when:**
- Demoing to stakeholders
- Testing UI/UX flows
- Presenting to class/team
- Limited budget
- Prototyping new features

**Use Full RAG Version when:**
- Deploying to real users
- Need semantic search quality
- Have 1000s of courses
- Need real-time data updates
- Production deployment

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

### Frontend can't connect to backend
1. Check backend is running on port 8000
2. Check console for CORS errors
3. Verify API_URL in `frontend/src/components/Chatbot.jsx`

### Styling issues
```bash
# Clear npm cache
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

### Add Features
- [ ] Save conversation history
- [ ] Export course list as PDF
- [ ] Add course comparison
- [ ] Filter by college/units
- [ ] Add course prerequisites

### Upgrade to Full RAG
When ready, switch to the full RAG pipeline:
1. Run `python src/setup_opensearch_traditional.py`
2. Run `python src/upload_to_opensearch.py`
3. Update frontend to call RAG endpoints
4. Much better search quality!

## Support

For questions about:
- **Mock version**: Check this README
- **Full RAG version**: See `CUSTOM_RAG_SUMMARY.md`
- **General project**: See `CLAUDE.md`

---

**Built**: 2026-07-06  
**Purpose**: Mock chatbot for demos (no AWS required)  
**Cost**: $0 🎉
