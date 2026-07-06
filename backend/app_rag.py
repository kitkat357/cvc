"""
FastAPI backend for CVC chatbot with REAL RAG pipeline.
Uses OpenSearch + Bedrock (Claude Haiku + Titan Embeddings).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
sys.path.insert(0, '../src')

from custom_rag import CustomRAG

app = FastAPI(title="CVC GE Chatbot API - RAG Version")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline
rag_pipeline = None

def get_rag_pipeline():
    """Get or initialize RAG pipeline."""
    global rag_pipeline
    if rag_pipeline is None:
        try:
            rag_pipeline = CustomRAG()
            print("✅ RAG pipeline initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing RAG pipeline: {e}")
            raise
    return rag_pipeline


# Request/Response models
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    context: Optional[Dict] = {}


class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    courses: Optional[List[Dict]] = None
    sources: Optional[List[Dict]] = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint using RAG pipeline.
    This uses real Bedrock API (Titan + Claude Haiku).
    """
    try:
        rag = get_rag_pipeline()

        user_message = request.messages[-1].content if request.messages else ""

        # Build conversation history (exclude current message)
        conversation_history = []
        for msg in request.messages[:-1]:
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })

        # Get language from context
        language = request.context.get('language', 'en') if request.context else 'en'

        # Query RAG pipeline (uses Bedrock!)
        result = rag.query(
            user_query=user_message,
            top_k=10,
            conversation_history=conversation_history,
            language=language
        )

        # Format courses from sources
        courses = []
        for source in result.get('sources', []):
            metadata = source.get('metadata', {})

            if metadata.get('source_type') == 'catalog':
                courses.append({
                    'course_code': metadata.get('course_code', 'N/A'),
                    'title': metadata.get('title', 'N/A'),
                    'college': metadata.get('college', 'N/A'),
                    'units': metadata.get('units', 'N/A'),
                    'description': source.get('text', '')[:200] + '...',
                    'ge_areas': [metadata.get('course_code', 'N/A')],  # Simplified
                    'score': source.get('score', 0)
                })

        # Generate suggestions based on context
        suggestions = [
            "Tell me more about another GE area",
            "What are the transfer requirements?",
            "Show me courses from a different college"
        ]

        return ChatResponse(
            response=result['response'],
            courses=courses if courses else None,
            sources=result.get('sources'),
            suggestions=suggestions
        )

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    try:
        rag = get_rag_pipeline()
        return {
            "status": "ok",
            "rag_initialized": rag is not None,
            "mode": "production_rag"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "mode": "production_rag"
        }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CVC GE Chatbot API - RAG Version",
        "version": "2.0.0 (Production RAG)",
        "features": [
            "Semantic search with OpenSearch",
            "Claude Haiku via Bedrock",
            "Titan Embeddings",
            "1,981 indexed documents"
        ],
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI with RAG pipeline...")
    print("⚠️  This uses AWS Bedrock (costs apply)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
