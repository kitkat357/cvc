"""
FastAPI backend for CVC GE chatbot (mock version)
Simple conversational flow without RAG pipeline
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json

app = FastAPI(title="CVC GE Chatbot API")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GE Information
GE_INFO = {
    "igetc": {
        "name": "IGETC (Intersegmental General Education Transfer Curriculum)",
        "description": "IGETC is a GE pattern for California Community College students transferring to UC or CSU. Completing IGETC can satisfy most lower-division general education requirements before transfer.",
        "note": "Students who started at a California Community College before Fall 2025 may still be eligible to use IGETC.",
        "areas": {
            "1A": "English Composition (1 course, 3 units)",
            "1B": "Critical Thinking & Composition (1 course, 3 units)",
            "1C": "Oral Communication (1 course, 3 units)",
            "2": "Mathematical Concepts (1 course, 3-4 units)",
            "3A": "Arts (3 courses, 9 units from at least 2 disciplines)",
            "3B": "Humanities (3 courses, 9 units from at least 2 disciplines)",
            "4": "Social & Behavioral Sciences (3 courses, 9 units from at least 2 disciplines)",
            "5A": "Physical Sciences (2 courses, 7-9 units, at least 1 lab)",
            "5B": "Biological Sciences (2 courses, 7-9 units, at least 1 lab)",
            "5C": "Science Laboratory (included in 5A/5B)",
            "6": "Language Other Than English (proficiency requirement)"
        }
    },
    "cal-getc": {
        "name": "Cal-GETC (California General Education Transfer Curriculum)",
        "description": "Starting Fall 2025, Cal-GETC became the single lower-division GE transfer pattern for California Community College students transferring to UC or CSU. It was created to simplify transfer by replacing multiple GE pathways with one shared pattern.",
        "note": "Students should still check major requirements on ASSIST.org because GE completion does not replace major preparation.",
        "areas": {
            "1A": "English Composition (1 course, 3 units)",
            "1B": "Critical Thinking & Composition (1 course, 3 units)",
            "1C": "Oral Communication (1 course, 3 units)",
            "2": "Mathematical Concepts (1 course, 3-4 units)",
            "3": "Arts & Humanities (3 courses, 9 units from at least 2 disciplines)",
            "4": "Social & Behavioral Sciences (3 courses, 9 units from at least 2 disciplines)",
            "5": "Physical & Biological Sciences (2 courses with labs, 7-9 units)",
            "6": "Ethnic Studies (1 course, 3 units)",
            "7": "Language Other Than English (proficiency requirement)"
        }
    },
    "cal-breadth": {
        "name": "Cal-Breadth / UC Campus Breadth",
        "description": "General education or breadth requirements specific to a UC campus or college. Instead of completing IGETC or Cal-GETC, some students may follow the GE/breadth pattern of the UC campus they plan to attend.",
        "note": "This option can be better for students in selective or unit-heavy majors where completing every IGETC/Cal-GETC area is not the best use of time. Breadth requirements vary by UC campus, college, and major."
    }
}

# Mock course data (simplified for demo)
MOCK_COURSES = [
    {
        "course_code": "ENGL 101",
        "title": "English Composition",
        "college": "Cerritos College",
        "units": "3",
        "ge_areas": ["IGETC 1A", "Cal-GETC 1A"],
        "description": "Introduction to college-level writing and critical reading."
    },
    {
        "course_code": "COMM 100",
        "title": "Public Speaking",
        "college": "Victor Valley College",
        "units": "3",
        "ge_areas": ["IGETC 1C", "Cal-GETC 1C"],
        "description": "Fundamentals of public speaking and oral communication."
    },
    {
        "course_code": "MATH 104",
        "title": "Calculus I",
        "college": "Victor Valley College",
        "units": "5",
        "ge_areas": ["IGETC 2", "Cal-GETC 2"],
        "description": "Introduction to differential and integral calculus."
    },
    {
        "course_code": "ART 101",
        "title": "Art History",
        "college": "Mount San Antonio College",
        "units": "3",
        "ge_areas": ["IGETC 3A", "Cal-GETC 3"],
        "description": "Survey of Western art from prehistoric to modern times."
    },
    {
        "course_code": "MUS 104B",
        "title": "History of Rock Music",
        "college": "Cerritos College",
        "units": "3",
        "ge_areas": ["IGETC 3A", "Cal-GETC 3"],
        "description": "Historical and cultural study of rock music."
    },
    {
        "course_code": "SOC 101",
        "title": "Intro to Sociology",
        "college": "Cerritos College",
        "units": "3",
        "ge_areas": ["IGETC 4", "Cal-GETC 4"],
        "description": "Introduction to sociological principles and concepts."
    },
    {
        "course_code": "PSYCH 101",
        "title": "General Psychology",
        "college": "Victor Valley College",
        "units": "3",
        "ge_areas": ["IGETC 4", "Cal-GETC 4"],
        "description": "Introduction to the science of human behavior."
    },
    {
        "course_code": "BIO 101",
        "title": "General Biology",
        "college": "Cerritos College",
        "units": "4",
        "ge_areas": ["IGETC 5B", "Cal-GETC 5"],
        "description": "Introduction to biological principles with lab component."
    },
    {
        "course_code": "CHEM 101",
        "title": "General Chemistry",
        "college": "Mount San Antonio College",
        "units": "5",
        "ge_areas": ["IGETC 5A", "Cal-GETC 5"],
        "description": "Introduction to chemical principles with lab."
    },
    {
        "course_code": "ES 101",
        "title": "Introduction to Ethnic Studies",
        "college": "Victor Valley College",
        "units": "3",
        "ge_areas": ["Cal-GETC 6"],
        "description": "Interdisciplinary study of race, ethnicity, and culture in America."
    }
]


# Request/Response models
class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    context: Optional[Dict] = {}


class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    courses: Optional[List[Dict]] = None
    enrollable_course_codes: Optional[List[str]] = None


def get_bot_response(messages: List[Message], context: Dict) -> ChatResponse:
    """Generate bot response based on conversation history and context."""

    user_message = messages[-1].content.lower() if messages else ""

    # Check if user is asking about GE systems
    if any(term in user_message for term in ["what is", "explain", "tell me about"]):
        if "igetc" in user_message:
            info = GE_INFO["igetc"]
            response = f"**{info['name']}**\n\n{info['description']}\n\n**Note**: {info['note']}\n\n"
            response += "**IGETC Areas:**\n"
            for area, desc in info['areas'].items():
                response += f"- **Area {area}**: {desc}\n"

            return ChatResponse(
                response=response,
                suggestions=["I need help with Area 1A", "Show me Area 4 courses", "What about Cal-GETC?"]
            )

        elif "cal-getc" in user_message or "calgetc" in user_message:
            info = GE_INFO["cal-getc"]
            response = f"**{info['name']}**\n\n{info['description']}\n\n**Note**: {info['note']}\n\n"
            response += "**Cal-GETC Areas:**\n"
            for area, desc in info['areas'].items():
                response += f"- **Area {area}**: {desc}\n"

            return ChatResponse(
                response=response,
                suggestions=["I need Area 3 courses", "What about Area 6?", "Show me science courses"]
            )

        elif "breadth" in user_message or "cal-breadth" in user_message:
            info = GE_INFO["cal-breadth"]
            response = f"**{info['name']}**\n\n{info['description']}\n\n**Note**: {info['note']}"

            return ChatResponse(
                response=response,
                suggestions=["I'll use IGETC instead", "Tell me about Cal-GETC"]
            )

    # Check if user is asking about specific GE areas
    ge_area_match = None
    for pattern in ["area 1a", "area 1b", "area 1c", "area 2", "area 3", "area 4", "area 5", "area 6", "area 7",
                    "1a", "1b", "1c", "ge 2", "ge 3", "ge 4", "ge 5", "ge 6"]:
        if pattern in user_message:
            ge_area_match = pattern.replace("area ", "").replace("ge ", "").upper()
            break

    if ge_area_match:
        # Find courses for this GE area
        matching_courses = [
            course for course in MOCK_COURSES
            if any(ge_area_match in ge for ge in course["ge_areas"])
        ]

        if matching_courses:
            response = f"Great! Here are some courses that satisfy **Area {ge_area_match}**:\n\n"

            return ChatResponse(
                response=response,
                courses=matching_courses,
                suggestions=["I want to enroll in one of these", "I need a different area", "Show me all areas"]
            )
        else:
            return ChatResponse(
                response=f"I don't have specific courses for Area {ge_area_match} in my current database. Would you like to explore other areas?",
                suggestions=["Show me Area 1A", "What about Area 4?", "See all available areas"]
            )

    # Check for specific subjects
    if any(term in user_message for term in ["math", "calculus", "mathematics"]):
        math_courses = [c for c in MOCK_COURSES if "MATH" in c["course_code"]]
        return ChatResponse(
            response="Here are the math courses I found:",
            courses=math_courses,
            suggestions=["I want to enroll in MATH 104", "Show me other areas", "I need science courses"]
        )

    if any(term in user_message for term in ["english", "writing", "composition"]):
        english_courses = [c for c in MOCK_COURSES if "ENGL" in c["course_code"]]
        return ChatResponse(
            response="Here are the English courses I found:",
            courses=english_courses,
            suggestions=["I want to enroll in ENGL 101", "Show me communication courses", "I need humanities"]
        )

    if any(term in user_message for term in ["social", "sociology", "psychology"]):
        social_courses = [c for c in MOCK_COURSES if any(code in c["course_code"] for code in ["SOC", "PSYCH"])]
        return ChatResponse(
            response="Here are social science courses I found:",
            courses=social_courses,
            suggestions=["I want to enroll", "Show me arts courses", "I need science courses"]
        )

    if any(term in user_message for term in ["science", "biology", "chemistry", "lab"]):
        science_courses = [c for c in MOCK_COURSES if any(code in c["course_code"] for code in ["BIO", "CHEM"])]
        return ChatResponse(
            response="Here are science courses with lab components:",
            courses=science_courses,
            suggestions=["I want to enroll", "Show me humanities", "I need math courses"]
        )

    # Check if user expresses interest in enrolling
    # Only trigger if they're NOT asking for help initially
    enrollment_keywords = ["enroll", "sign up", "register", "take this", "sounds good", "that works",
                           "perfect", "i'll take", "looks good", "interested in enrolling",
                           "want to take", "want that", "i'd like", "that one"]

    # Exclude phrases that indicate they're asking for help, not enrolling
    help_phrases = ["i want some help", "i want help", "want some help", "can you help"]
    is_asking_for_help = any(phrase in user_message for phrase in help_phrases)

    if len(messages) > 2 and any(keyword in user_message for keyword in enrollment_keywords) and not is_asking_for_help:
        enrollable_codes = []

        # Try to identify specific course mentioned in user message
        for course in MOCK_COURSES:
            course_code_clean = course["course_code"].replace(" ", "").lower()
            course_code_spaced = course["course_code"].lower()
            course_title_lower = course["title"].lower()

            if (course_code_clean in user_message.replace(" ", "") or
                course_code_spaced in user_message or
                course_title_lower in user_message):
                enrollable_codes.append(course["course_code"])

        # If specific course identified, enable enrollment for that course
        if enrollable_codes:
            return ChatResponse(
                response=f"Great! I've enabled the enrollment button for **{', '.join(enrollable_codes)}**. "
                        f"Click the **📝 Enroll** button next to the course to proceed.",
                enrollable_course_codes=enrollable_codes,
                suggestions=["Show me more courses", "What other GE areas do I need?", "Tell me about transfer requirements"]
            )
        # If no specific course mentioned, enable all recently shown courses
        else:
            # Find all courses that were shown in the last few messages
            # We'll enable enrollment for all courses currently visible
            all_enrollable = [c["course_code"] for c in MOCK_COURSES]

            return ChatResponse(
                response=f"Great! I've enabled the enrollment buttons for all the courses shown above. "
                        f"Click the **📝 Enroll** button next to any course you'd like to take.",
                enrollable_course_codes=all_enrollable,
                suggestions=["Show me more courses", "What other areas do I need?", "Tell me about prerequisites"]
            )

    # Check if user mentions they attend Cal Poly
    if "cal poly" in user_message and len(messages) == 1:
        return ChatResponse(
            response="Great! I can help you find community college courses that satisfy Cal Poly's GE requirements. "
                    "Starting Fall 2025, students use **Cal-GETC** (California General Education Transfer Curriculum) "
                    "to complete their lower-division GE requirements.\n\n"
                    "Which GE area do you need help with? Or would you like me to explain the different GE systems first?",
            suggestions=[
                "Explain Cal-GETC to me",
                "What's the difference between IGETC and Cal-GETC?",
                "I need help with Area 4 (Social Sciences)",
                "Show me all GE areas"
            ]
        )

    # Default greeting/help
    if len(messages) <= 1 or any(term in user_message for term in ["help", "start", "hi", "hello"]):
        return ChatResponse(
            response="Hi! I'm here to help you find community college courses that satisfy your Cal Poly GE requirements. "
                    "I can:\n\n"
                    "✅ Explain different GE systems (IGETC, Cal-GETC, Cal-Breadth)\n"
                    "✅ Help you understand GE areas (like Area 1A, Area 4, etc.)\n"
                    "✅ Find courses that satisfy specific GE requirements\n\n"
                    "What would you like to know?",
            suggestions=[
                "What is Cal-GETC?",
                "I need courses for Area 3 (Arts & Humanities)",
                "Explain the difference between IGETC and Cal-GETC",
                "Show me all available courses"
            ]
        )

    # Fallback
    return ChatResponse(
        response="I'm not sure I understood that. Could you clarify what GE area you need help with, "
                "or would you like me to explain the GE systems?",
        suggestions=[
            "Explain Cal-GETC",
            "I need Area 1A courses",
            "Show me all areas",
            "What courses are available?"
        ]
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint."""
    try:
        return get_bot_response(request.messages, request.context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CVC GE Chatbot API",
        "version": "1.0.0 (Mock)",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/api/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
