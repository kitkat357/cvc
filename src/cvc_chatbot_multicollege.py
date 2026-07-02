import streamlit as st
import json
import boto3

# Load ALL course data
@st.cache_data
def load_all_data():
    colleges = {}

    # Load Victor Valley → Cal Poly
    with open("simple_transfers (1).json", "r") as f:
        vvc_data = json.load(f)
        colleges["Victor Valley College"] = vvc_data

    # Load Cuesta → Cal Poly
    with open("simple_transfers (2).json", "r") as f:
        cuesta_data = json.load(f)
        colleges["Cuesta College"] = cuesta_data

    return colleges

# Initialize Bedrock client
@st.cache_resource
def get_bedrock_client():
    session = boto3.Session(profile_name='cvc-project')
    return session.client('bedrock-runtime', region_name='us-west-2')

def search_for_context(user_query, all_colleges_data):
    """Search all colleges for relevant courses based on user query"""
    # Extract keywords for common GE areas
    area_keywords = {
        '1': ['english', 'writing', 'communication', 'speech', 'composition'],
        '2': ['math', 'mathematics', 'statistics', 'calculus', 'algebra'],
        '3': ['art', 'music', 'humanities', 'philosophy', 'literature', 'history', 'language'],
        '4': ['psychology', 'sociology', 'political', 'economics', 'anthropology'],
        '5': ['biology', 'chemistry', 'physics', 'science', 'geology'],
        '6': ['ethnic', 'chicano', 'african american', 'asian american']
    }

    query_lower = user_query.lower()
    results = {}

    # Determine which area is being asked about
    keywords = []
    if '3b' in query_lower or 'humanities' in query_lower:
        keywords = ['english', 'history', 'philosophy', 'literature', 'language', 'cultural', 'religion', 'humanities']
    elif '3a' in query_lower or 'arts' in query_lower:
        keywords = ['art', 'music', 'theater', 'theatre', 'dance', 'visual']
    elif 'area 3' in query_lower:
        keywords = ['english', 'history', 'philosophy', 'literature', 'art', 'music', 'humanities']
    elif 'area 4' in query_lower or 'social science' in query_lower:
        keywords = area_keywords['4']
    elif 'area 2' in query_lower or 'math' in query_lower:
        keywords = area_keywords['2']
    elif 'area 5' in query_lower or 'science' in query_lower:
        keywords = area_keywords['5']

    if keywords:
        for college_name, data in all_colleges_data.items():
            matches = []
            for course in data['transfers']:
                dept_lower = course['department'].lower()
                title_lower = course['course_title'].lower()

                if any(kw in dept_lower or kw in title_lower for kw in keywords):
                    matches.append(course)

            if matches:
                results[college_name] = matches[:10]  # Top 10 per college

    return results

def call_claude(messages, all_colleges_data):
    """Call Claude via Bedrock with ALL college course context"""
    client = get_bedrock_client()

    # Get the last user message to search for relevant courses
    last_user_msg = messages[-1]["content"] if messages and messages[-1]["role"] == "user" else ""

    # Search for relevant courses
    search_results = search_for_context(last_user_msg, all_colleges_data)

    # Build course context from search results
    course_context = ""
    if search_results:
        course_context = "\n\n**RELEVANT COURSES FOUND (SHOW THESE TO THE STUDENT):**\n"
        for college_name, courses in search_results.items():
            course_context += f"\n**{college_name}:**\n"
            for course in courses:
                transfers = ', '.join(course['transfers_to']) if course['transfers_to'] else 'See advisor'
                course_context += f"- {course['from_course']}: {course['course_title']} ({course['units']} units) - {course['department']}\n  Transfers to: {transfers}\n  ADD ENROLL BUTTON: After this course, add a mock enroll badge like: `🔵 Enroll →`\n"
        course_context += f"\n**YOU MUST SHOW THESE COURSES TO THE STUDENT. DO NOT SAY YOU DON'T HAVE THE DATA.**\n"
        course_context += f"\n**IMPORTANT: Add a mock enroll button/badge after EACH course using this format: `🔵 Enroll →` or make it look like a clickable button**\n"
    else:
        course_context = "\n\n**NO COURSES FOUND IN SEARCH - but this might be a search error, not missing data**\n"

    # Build comprehensive system prompt
    colleges_summary = "\n".join([
        f"- **{name}**: {len(data['transfers'])} courses transferring to {data['to_college']}"
        for name, data in all_colleges_data.items()
    ])

    system_prompt = f"""You are a helpful course advisor for California community college students using the California Virtual Campus (CVC).

You help students find courses across MULTIPLE community colleges that transfer to Cal Poly and other universities. You explain GE requirements in simple terms using Cal Poly's 2026 GE system.

**CRITICAL FOR DEMO:**
- You have COMPLETE course data. NEVER say "I don't have", "limited visibility", "let me be transparent", "check the website", or "I recommend visiting"
- When courses are in the RELEVANT COURSES FOUND section, you MUST show them immediately
- DO NOT hedge, apologize, or explain data limitations
- Just show the damn courses in a nice table format
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

**Available Colleges & Courses:**
{colleges_summary}

{course_context}

**CRITICAL INSTRUCTIONS - READ THIS CAREFULLY:**

IF there are courses listed in "RELEVANT COURSES FOUND" section above:
→ SHOW THEM IMMEDIATELY in a formatted list
→ DO NOT say "I don't have data", "limited visibility", "be transparent", "recommend checking"
→ These English, History, Philosophy courses ALL count as Area 3B
→ Format: College name, then bulleted list of courses with units

IF there are NO courses in "RELEVANT COURSES FOUND":
→ Then and ONLY then say you don't have specific data

BANNED PHRASES:
❌ "I want to be transparent"
❌ "limited visibility"
❌ "I recommend visiting"
❌ "check the website"
❌ "let me pull up"

Just show the courses confidently like a normal advisor would.
1. Search across ALL available colleges
2. Group results by college
3. Show which colleges offer courses for that requirement
4. Highlight differences (units, course titles, etc.)

When students mention old area names (like "Area C" or "Area D"), explain the new numbering system and then search for relevant courses.

You have access to the full course catalog from these colleges. When recommending courses, include:
- Course code and title
- Units
- Department
- Which college offers it
- What it transfers to at Cal Poly"""

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
        response = client.invoke_model(
            modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
            body=body
        )

        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']

    except Exception as e:
        return f"Error calling Claude: {str(e)}"

def search_courses_multi_college(all_colleges_data, keywords, area_filter=None):
    """Search courses across all colleges"""
    results_by_college = {}

    for college_name, data in all_colleges_data.items():
        matches = []
        for course in data['transfers']:
            dept_lower = course['department'].lower()
            title_lower = course['course_title'].lower()

            if any(kw.lower() in dept_lower or kw.lower() in title_lower for kw in keywords):
                matches.append(course)

        if matches:
            results_by_college[college_name] = matches[:10]

    return results_by_college

# Streamlit UI
st.set_page_config(page_title="CVC Multi-College Assistant", page_icon="🎓", layout="wide")

# Disable Command+C cache clearing shortcut
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    // Disable 'c' key for clearing cache (Streamlit default)
    if (e.key === 'c' && !e.target.matches('input, textarea')) {
        e.stopPropagation();
    }
});
</script>
<style>
    /* CVC Blue and Yellow theme */
    .stApp {
        background-color: #f8f9fa;
    }

    h1 {
        color: #003366 !important; /* CVC Blue */
    }

    .stChatMessage[data-testid="assistant-message"] {
        background-color: #003366 !important; /* CVC Blue */
        color: white !important;
    }

    .stChatMessage[data-testid="user-message"] {
        background-color: #FDB913 !important; /* CVC Yellow */
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

st.title("🎓 CVC AI Course Assistant")
st.caption("Powered by Claude AI - Search courses across multiple California community colleges")

# Load all college data
all_colleges = load_all_data()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar with college info
with st.sidebar:
    st.header("Available Colleges")

    for college_name, data in all_colleges.items():
        with st.expander(f"📚 {college_name}"):
            st.metric("Courses", len(data['transfers']))
            st.caption(f"Transfers to: {data['to_college']}")

    st.divider()

    st.header("Quick Actions")

    if st.button("🔄 Start Over"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    with st.expander("💡 Example Questions"):
        st.markdown("""
**Multi-College Search:**
- "Which community colleges can I take Area 3B at?"
- "I need Area 4 courses - show me all options"
- "Compare psychology courses across colleges"

**Specific College:**
- "What courses does Cuesta offer for Area 2?"
- "Show me Victor Valley science classes"

**Transfer Planning:**
- "I'm at Victor Valley, what transfers to Cal Poly for GE Area 1A?"
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

---

**Transfer Curriculum Options:**

**CSU GE Breadth (Cal Poly)**
- General Education pattern accepted by all 23 CSU campuses
- Cal Poly uses this framework with numbered areas (1-6)
- Complete at community college, finish at CSU

**IGETC (Intersegmental General Education Transfer Curriculum)**
- Accepted by both CSU and UC systems
- One pattern satisfies lower-division GE for both
- Makes transferring between systems easier
- Similar areas to CSU Breadth but slightly different requirements

**GETC (General Education Transfer Curriculum)**
- Less common, used by some specific colleges
- Covers basic GE requirements
- Check with your target institution for acceptance

💡 **Tip:** Most community college students use either CSU GE Breadth (for CSU schools like Cal Poly) or IGETC (if considering UCs too).
        """)

# Display chat history in main area
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input at the bottom
if prompt := st.chat_input("Ask me about courses across colleges..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response with Claude
    with st.chat_message("assistant"):
        with st.spinner("Searching across all colleges..."):
            # Debug: show what's being searched
            search_results = search_for_context(prompt, all_colleges)
            if search_results:
                st.caption(f"🔍 Found {sum(len(courses) for courses in search_results.values())} courses across {len(search_results)} colleges")

            response = call_claude(st.session_state.messages, all_colleges)
            st.markdown(response)

            # Add interactive enroll buttons if courses were found
            if search_results:
                st.divider()
                st.caption("💡 Quick Actions:")
                for college_name, courses in search_results.items():
                    with st.expander(f"📚 Enroll in {college_name} courses"):
                        for course in courses[:5]:  # Show top 5
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**{course['from_course']}**: {course['course_title']} ({course['units']} units)")
                            with col2:
                                if st.button("Enroll →", key=f"enroll_{college_name}_{course['from_course']}", type="primary"):
                                    st.success(f"✅ Enrolled in {course['from_course']}!")

            st.session_state.messages.append({"role": "assistant", "content": response})
