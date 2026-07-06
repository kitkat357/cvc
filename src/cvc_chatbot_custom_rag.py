"""
CVC RAG Chatbot - Custom RAG Pipeline (Cost-Optimized)
Uses traditional OpenSearch + direct Bedrock API calls.
No Bedrock Knowledge Base required - 60-75% cost savings!
"""

import streamlit as st
import sys
sys.path.insert(0, 'src')

from custom_rag import CustomRAG


# Page config
st.set_page_config(
    page_title="CVC Course Search",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS for CVC branding
st.markdown("""
<style>
    .main-header {
        background-color: #003366;
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #FDB913;
        color: #003366;
        font-weight: bold;
    }
    .course-card {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #003366;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize RAG pipeline
@st.cache_resource
def get_rag_pipeline():
    """Initialize custom RAG pipeline."""
    try:
        return CustomRAG()
    except Exception as e:
        st.error(f"Error initializing RAG pipeline: {str(e)}")
        return None


# Header
st.markdown("""
<div class="main-header">
    <h1>🎓 California Virtual Campus - Course Search</h1>
    <p>Find community college courses that transfer to 4-year universities</p>
    <p style="font-size: 0.9em; opacity: 0.9;">✨ Custom RAG Pipeline • 💰 Cost-Optimized Architecture</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.markdown("### 💡 About This Chatbot")

    st.markdown("""
    **Custom RAG Pipeline Features:**
    - 🔍 Semantic search with vector embeddings
    - 🎯 Traditional OpenSearch (cost-optimized)
    - 🤖 Claude Haiku 4.5 for responses
    - 💰 60-75% cheaper than Serverless
    """)

    st.markdown("---")

    st.markdown("### 📚 Example Questions")
    example_queries = [
        "I need a math course that transfers to Cal Poly",
        "What English courses are available at Cerritos?",
        "Show me biology courses with lab components",
        "What courses satisfy GE Area 3 (Arts & Humanities)?",
        "Does MATH 104 from VVC transfer to Cal State Fullerton?"
    ]

    for query in example_queries:
        if st.button(query, key=query):
            st.session_state.messages.append({"role": "user", "content": query})
            st.rerun()

    st.markdown("---")

    st.markdown("### ⚙️ Search Settings")
    top_k = st.slider("Number of results", min_value=5, max_value=20, value=10)

    st.markdown("---")

    st.markdown("### 📖 Cal Poly GE Areas")
    st.markdown("""
    **Area 1**: English & Communication (9 units)
    **Area 2**: Math (3 units)
    **Area 3**: Arts & Humanities (6 units)
    - 3A: Arts
    - 3B: Humanities
    **Area 4**: Social Sciences (6 units)
    **Area 5**: Physical & Life Sciences (7 units)
    - 5A, 5B: Science courses
    - 5C: Lab component
    **Area 6**: Ethnic Studies (3 units)
    """)

    st.markdown("---")

    # Architecture info
    with st.expander("🏗️ Architecture"):
        st.markdown("""
        **Traditional OpenSearch Setup:**
        - t3.small.search instance
        - 1536-dimension vectors (Titan)
        - HNSW algorithm (Faiss)
        - Direct Bedrock API calls

        **Monthly Cost: ~$20-40**
        vs Serverless: ~$90-180/month

        **Savings: 60-75%!**
        """)

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about courses, transfers, or GE requirements..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching courses and generating response..."):
            rag = get_rag_pipeline()

            if rag:
                try:
                    # Build conversation history for context
                    conversation_history = []
                    for msg in st.session_state.messages[:-1]:  # Exclude current message
                        conversation_history.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })

                    # Query RAG pipeline
                    result = rag.query(
                        user_query=prompt,
                        top_k=top_k,
                        conversation_history=conversation_history
                    )

                    response = result['response']
                    sources = result['sources']

                    # Display response
                    st.markdown(response)

                    # Show sources in expander
                    if sources:
                        with st.expander(f"📚 View {len(sources)} Sources"):
                            for i, doc in enumerate(sources, 1):
                                metadata = doc['metadata']
                                score = doc['score']

                                st.markdown(f"**Source {i}** (Relevance: {score:.3f})")

                                if metadata.get('source_type') == 'catalog':
                                    st.markdown(f"""
                                    <div class="course-card">
                                        <strong>{metadata.get('course_code', 'N/A')}</strong>: {metadata.get('title', 'N/A')}<br>
                                        <em>{metadata.get('college', 'N/A')}</em> • {metadata.get('units', 'N/A')} units<br>
                                        <small>{doc['text'][:200]}...</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                                elif metadata.get('source_type') == 'transfer':
                                    st.markdown(f"""
                                    <div class="course-card">
                                        <strong>Transfer:</strong> {metadata.get('from_course', 'N/A')}
                                        ({metadata.get('from_college', 'N/A')}) →
                                        {metadata.get('to_college', 'N/A')}<br>
                                        <small>{doc['text'][:200]}...</small>
                                    </div>
                                    """, unsafe_allow_html=True)

                    # Add to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
            else:
                error_msg = "RAG pipeline initialization failed. Check the logs."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    <p>🎓 California Virtual Campus Course Search • Powered by Custom RAG Pipeline</p>
    <p>Traditional OpenSearch + Claude Haiku 4.5 • Cost-Optimized Architecture</p>
</div>
""", unsafe_allow_html=True)
