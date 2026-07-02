"""
CVC RAG Chatbot - Enhanced with Bedrock Knowledge Base and OpenSearch Serverless
Uses RAG (Retrieval-Augmented Generation) for semantic search across course catalogs.
"""

import streamlit as st
import json
import boto3
import config

# Initialize Bedrock clients
@st.cache_resource
def get_bedrock_clients():
    """Initialize Bedrock runtime and agent runtime clients."""
    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    return {
        'runtime': session.client('bedrock-runtime'),
        'agent_runtime': session.client('bedrock-agent-runtime')
    }


def search_courses_rag(query: str, top_k: int = 10) -> list:
    """
    Query Bedrock Knowledge Base for relevant courses using semantic search.

    Args:
        query: Natural language search query
        top_k: Number of results to return

    Returns:
        List of relevant course documents with metadata
    """
    if not config.KNOWLEDGE_BASE_ID:
        st.error("⚠️ Knowledge Base ID not configured. Please set KNOWLEDGE_BASE_ID in .env file.")
        return []

    clients = get_bedrock_clients()

    try:
        response = clients['agent_runtime'].retrieve(
            knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': top_k
                }
            }
        )

        return response.get('retrievalResults', [])

    except Exception as e:
        st.error(f"Error querying Knowledge Base: {str(e)}")
        return []


def format_course_context(retrieval_results: list) -> str:
    """
    Format retrieved course documents into context for Claude.

    Args:
        retrieval_results: Results from Knowledge Base retrieval

    Returns:
        Formatted context string
    """
    if not retrieval_results:
        return "No relevant courses found in the database."

    context = "**RELEVANT COURSES FOUND (SHOW THESE TO THE STUDENT):**\n\n"

    # Group by college
    by_college = {}
    for result in retrieval_results:
        content = result.get('content', {}).get('text', '')
        metadata = result.get('metadata', {})

        college = metadata.get('college', 'Unknown College')

        if college not in by_college:
            by_college[college] = []

        by_college[college].append({
            'text': content,
            'metadata': metadata
        })

    # Format by college
    for college, courses in by_college.items():
        context += f"**{college}:**\n"
        for course in courses:
            meta = course['metadata']

            if meta.get('source_type') == 'catalog':
                # Course catalog entry
                context += f"- **{meta.get('course_code', 'N/A')}**: {meta.get('title', 'N/A')} "
                context += f"({meta.get('units', 'N/A')} units) - {meta.get('department', 'N/A')}\n"
                context += f"  {course['text'][:200]}...\n"
                context += f"  `🔵 Enroll →`\n"

            elif meta.get('source_type') == 'transfer':
                # Transfer/articulation entry
                transfers_to = meta.get('transfers_to', [])
                transfers_str = ', '.join(transfers_to) if transfers_to else 'See advisor'
                context += f"- **{meta.get('from_course', 'N/A')}**: {meta.get('course_title', 'N/A')} "
                context += f"({meta.get('units', 'N/A')} units)\n"
                context += f"  Transfers to: {transfers_str}\n"
                context += f"  `🔵 Enroll →`\n"

        context += "\n"

    context += "**YOU MUST SHOW THESE COURSES TO THE STUDENT. DO NOT SAY YOU DON'T HAVE THE DATA.**\n"
    context += "**IMPORTANT: Format as a clean list with course codes, titles, units, and transfer info.**\n"

    return context


def call_claude_with_rag(messages: list, user_query: str) -> str:
    """
    Call Claude via Bedrock with RAG-retrieved context.

    Args:
        messages: Conversation history
        user_query: Latest user query

    Returns:
        Claude's response
    """
    clients = get_bedrock_clients()

    # Retrieve relevant courses from Knowledge Base
    retrieval_results = search_courses_rag(user_query, top_k=15)

    # Format context
    course_context = format_course_context(retrieval_results)

    # Show debug info
    if retrieval_results:
        st.caption(f"✓ Found {len(retrieval_results)} relevant documents")

    # Build system prompt
    system_prompt = f"""You are a helpful course advisor for California community college students using the California Virtual Campus (CVC).

You help students find courses across MULTIPLE community colleges that transfer to Cal Poly and other universities. You explain GE requirements in simple terms using Cal Poly's 2026 GE system.

**CRITICAL FOR EFFECTIVENESS:**
- You have COMPLETE course data retrieved via semantic search
- NEVER say "I don't have", "limited visibility", "check the website", or "I recommend visiting"
- When courses are in the RELEVANT COURSES FOUND section, you MUST show them immediately
- DO NOT hedge, apologize, or explain data limitations
- Just show the courses in a clear, organized format
- Act like a confident advisor who has all the information

**Cal Poly GE 2026 Areas:**

**Lower-Division:**
- Area 1: English Language Communication & Critical Thinking (9 units)
  - 1A: Written Communication
  - 1B: Critical Thinking
  - 1C: Oral Communication
- Area 2: Mathematics & Quantitative Reasoning (3 units)
- Area 3: Arts & Humanities (6 units)
  - 3A: Arts
  - 3B: Humanities
- Area 4: Social Sciences (6 units)
  - 4A: American Institutions
  - 4B: Social Sciences (must be from 2 different prefixes)
- Area 5: Physical & Life Sciences (7 units)
  - 5A: Physical Science
  - 5B: Life Sciences
  - 5C: Laboratory (1 unit)
- Area 6: Ethnic Studies (3 units)

**Upper-Division (9 units):**
- UD Area 2/5: Math or Science
- UD Area 3: Arts or Humanities
- UD Area 4: Social Sciences

{course_context}

**CRITICAL INSTRUCTIONS:**

IF there are courses listed in "RELEVANT COURSES FOUND" section above:
→ SHOW THEM IMMEDIATELY in a formatted list
→ DO NOT say "I don't have data" or make disclaimers
→ Format: College name, then bulleted list of courses with units and transfer info
→ Highlight key differences between colleges (units, titles, transfer options)

IF there are NO courses in "RELEVANT COURSES FOUND":
→ Then and ONLY then say you don't have specific data for that query

BANNED PHRASES:
❌ "I want to be transparent"
❌ "limited visibility"
❌ "I recommend visiting"
❌ "check the website"

When students mention old area names (like "Area C" or "Area D"), explain the new numbering system and show matching courses.

Include in your recommendations:
- Course code and title
- Units
- Department (if available)
- Which college offers it
- What it transfers to (for transfer data)
- Compare options across different colleges"""

    # Prepare messages
    conversation = []
    for msg in messages:
        conversation.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": conversation,
        "system": system_prompt,
        "temperature": 0.7
    })

    try:
        response = clients['runtime'].invoke_model(
            modelId=config.CLAUDE_MODEL_ID,
            body=body
        )

        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']

    except Exception as e:
        return f"Error calling Claude: {str(e)}"


# ==================== Streamlit UI ====================

st.set_page_config(page_title="CVC RAG Assistant", page_icon="🎓", layout="wide")

# Custom CSS for CVC branding
st.markdown("""
<style>
    /* CVC Blue and Yellow theme */
    .stApp {
        background-color: #f8f9fa;
    }

    h1 {
        color: #003366 !important; /* CVC Blue */
    }

    .stChatMessage[data-testid="assistant-message"] {
        background-color: #003366 !important;
        color: white !important;
    }

    .stChatMessage[data-testid="user-message"] {
        background-color: #FDB913 !important;
        color: #003366 !important;
    }

    .stButton>button {
        background-color: #003366;
        color: white;
        border: 2px solid #FDB913;
    }

    .stButton>button:hover {
        background-color: #FDB913;
        color: #003366;
        border: 2px solid #003366;
    }

    .stExpander {
        border-left: 4px solid #FDB913;
    }

    [data-testid="stHeader"] {
        background-color: #003366;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎓 CVC AI Course Assistant (RAG)")
st.caption("Powered by Claude AI + AWS Bedrock Knowledge Base - Semantic search across California community colleges")

# Check configuration
if not config.validate_config():
    st.warning("⚠️ Knowledge Base not configured. Set KNOWLEDGE_BASE_ID in .env file to enable RAG search.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("🔬 RAG Search Info")

    with st.expander("ℹ️ How RAG Works"):
        st.markdown("""
**RAG = Retrieval-Augmented Generation**

1. **Your Question** → Converted to semantic embedding
2. **Vector Search** → Finds similar courses in OpenSearch
3. **Context Retrieval** → Top relevant courses retrieved
4. **Claude Response** → Generates answer using retrieved context

**Benefits:**
- Understands natural language queries
- Searches by meaning, not just keywords
- Scales to 100,000+ courses
- Real-time updates from S3 data
        """)

    with st.expander("📊 Data Sources"):
        st.markdown(f"""
**S3 Bucket:** `{config.S3_BUCKET_NAME}`
**Region:** `{config.AWS_REGION}`
**Knowledge Base:** `{config.KNOWLEDGE_BASE_ID[:20]}...` if configured

**Current Colleges:**
- Cerritos College
- Mount San Antonio College
- Victor Valley College

**Transfer Agreements:**
- VVC → Cal State Fullerton
- VVC → Cal Poly SLO
- Cuesta → Cal Poly SLO
        """)

    st.divider()

    st.header("Quick Actions")

    if st.button("🔄 Start Over"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    with st.expander("💡 Example Questions"):
        st.markdown("""
**Natural Language Queries:**
- "I need a transferable English class"
- "Show me 3-unit math courses"
- "What psychology courses transfer to Cal Poly?"
- "Find me Area 3B humanities classes"

**Cross-College Search:**
- "Which colleges offer biology lab courses?"
- "Compare art courses across all colleges"

**Specific Requirements:**
- "I need Area 4 social science with 3 units"
- "Show me courses that transfer to CSU Area 1A"
        """)

    with st.expander("📚 GE Quick Reference"):
        st.markdown("""
**Cal Poly GE 2026:**
1. English & Communication
2. Math & Quantitative Reasoning
3. Arts & Humanities
4. Social Sciences
5. Physical & Life Sciences
6. Ethnic Studies

💡 **Tip:** Use natural language - RAG understands intent!
        """)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about courses using natural language..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response with Claude + RAG
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching knowledge base..."):
            response = call_claude_with_rag(st.session_state.messages, prompt)
        st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
