# CLAUDE.md - CVC RAG Chatbot Project

## Project Overview

**Name**: CVC LLM Search Enhancement - RAG Chatbot
**Purpose**: Enhance California Virtual Campus (CVC) course search with natural language processing and semantic search
**Primary Users**: California community college students seeking transferable courses
**Scale**: Currently 3 colleges (mock data), target 116 colleges with 100,000+ courses serving 2.2M students

**Last Updated**: 2026-07-06
**Current Status**: 
- ✅ Mock Chatbot (React + FastAPI) - Ready for demos
- ✅ Custom RAG Pipeline - Built and tested, currently paused
- ⏸️ AWS Services - All paused to save costs (~$0.01/month)

## Two Implementation Approaches

### 1. Mock Chatbot (React + FastAPI) - **RECOMMENDED FOR DEMOS**

**Architecture:**
```
React Frontend (Port 5173)
    ↓ HTTP REST API
FastAPI Backend (Port 8000)
    ↓
Hardcoded course data + conversation logic
```

**Technology Stack:**
- **Frontend**: React 18 with Vite
- **Backend**: FastAPI (Python)
- **Data**: Hardcoded mock courses (10 samples)
- **Cost**: $0 (no AWS required)
- **Setup Time**: 5 minutes

**Use Cases:**
- Demos to stakeholders
- UI/UX prototyping
- Class presentations
- Testing conversation flows

**Files:**
- `backend/app.py` - FastAPI server with GE conversation logic
- `frontend/src/components/Chatbot.jsx` - React chatbot UI
- `run_chatbot.sh` - Easy startup script
- `REACT_CHATBOT_README.md` - Full documentation

### 2. Custom RAG Pipeline (OpenSearch + Bedrock) - **FOR PRODUCTION**

**Architecture:**
```
Streamlit UI (Port 8502)
    ↓
Custom RAG Implementation (src/custom_rag.py)
    ↓
Traditional OpenSearch (t3.small.search)
    ↓
AWS Bedrock (Titan Embeddings + Claude Haiku)
```

**Technology Stack:**
- **Frontend**: Streamlit (Python web framework for ML/AI apps)
- **RAG Implementation**: Custom Python pipeline (no Bedrock Knowledge Base)
- **LLM**: Claude Haiku 4.5 via AWS Bedrock (`us.anthropic.claude-haiku-4-5-20251001-v1:0`)
- **Embeddings**: AWS Bedrock Titan Embeddings G1 (1536-dimension vectors)
- **Vector Database**: Traditional OpenSearch (t3.small.search instance)
- **Storage**: AWS S3 (`cvc-rag-course-data` bucket)
- **Region**: us-west-2 (Oregon)
- **AWS Profile**: `cvc-project`
- **Cost**: ~$20-40/month when active (60-75% cheaper than Serverless!)
- **Setup Time**: 30-40 minutes

**Use Cases:**
- Production deployment
- Real semantic search across 1,981 documents
- Scalable to 100,000+ courses
- Real user queries

### Custom RAG Pipeline (Production Version)

1. **User Query** → Streamlit chat input
2. **Semantic Embedding** → Direct Bedrock Titan API call (1536-dim vector)
3. **Vector Search** → OpenSearch KNN search (custom implementation)
4. **Context Retrieval** → Top-k relevant courses retrieved (default k=10)
5. **LLM Generation** → Direct Claude Haiku API call with retrieved context
6. **Response Display** → Formatted in Streamlit chat interface

**Key Advantage**: Full control over every step, no black-box Knowledge Base

### Data Flow

**Custom RAG Pipeline (Current Implementation):**
```
S3 Bucket (cvc-rag-course-data)
├── 1,981 documents preserved
└── courses + transfers
        ↓
Local Processing (src/upload_to_opensearch.py)
        ↓
Bedrock Titan Embeddings (API call)
        ↓
Traditional OpenSearch t3.small.search
        ↓
Custom RAG retrieval (src/custom_rag.py)
        ↓
Claude Haiku (direct API call)
```

**Mock Chatbot (For Demos):**
```
React UI
    ↓
FastAPI Backend
    ↓
Hardcoded conversation logic
    ↓
Mock course data (10 samples)
```

## Project Structure

### Mock Chatbot Modules (React + FastAPI)

#### `backend/app.py`
- FastAPI server with CORS enabled for React frontend
- Conversational logic for GE education and course recommendations
- **Key Functions**:
  - `get_bot_response()`: Main conversation handler with pattern matching
  - `chat()`: POST /api/chat endpoint for message handling
  - `health()`: GET /api/health for status checks
- **Data**: 
  - `GE_INFO`: IGETC, Cal-GETC, and Cal-Breadth definitions
  - `MOCK_COURSES`: 10 sample courses across 3 colleges
- **Features**: Explains GE systems, interviews about areas, shows relevant courses

#### `frontend/src/components/Chatbot.jsx`
- React component for chat interface
- **Key Features**:
  - Message history with user/assistant distinction
  - Course cards with GE area badges
  - Clickable suggestion buttons
  - Typing indicator animation
  - Auto-scroll to latest message
- **API Integration**: Axios for HTTP requests to FastAPI backend
- **State Management**: useState hooks for messages, input, loading, suggestions

#### `frontend/src/components/Chatbot.css`
- CVC-branded styling (blue #003366, gold #FDB913)
- Responsive course cards
- Smooth animations and transitions
- Mobile-friendly design

#### `run_chatbot.sh`
- Convenience script to start both backend and frontend
- Activates virtual environment
- Checks backend health before starting frontend
- Handles graceful shutdown

### Custom RAG Pipeline Modules (Production)

#### `src/custom_rag.py`
- Custom RAG implementation without Bedrock Knowledge Base
- **Class**: `CustomRAG`
- **Key Methods**:
  - `embed_text()`: Call Bedrock Titan for embeddings
  - `search_similar()`: OpenSearch KNN vector search
  - `generate_response()`: Call Claude Haiku with context
  - `query()`: Complete RAG pipeline (retrieve + generate)
- **Advantages**: Full control, 60-75% cost savings, debuggable

#### `src/upload_to_opensearch.py`
- Process and upload course data with embeddings to OpenSearch
- **Class**: `DataUploader`
- **Key Methods**:
  - `process_course_catalog()`: Parse course JSON files
  - `process_transfer_data()`: Parse transfer agreement files
  - `upload_documents()`: Bulk upload with embeddings (50 docs/batch)
- **Result**: 1,981 documents indexed with 1536-dim vectors

#### `src/cvc_chatbot_custom_rag.py`
- Streamlit UI for custom RAG pipeline
- Uses `CustomRAG` class instead of Bedrock Knowledge Base API
- Shows source documents with relevance scores
- CVC branding consistent with mock version

#### `src/setup_opensearch_traditional.py`
- Creates traditional OpenSearch domain (t3.small.search)
- Configures access policies for Bedrock and local access
- ~15 minute provisioning time
- Cost: ~$26/month (vs $90-180 for Serverless)

#### `src/create_opensearch_index_traditional.py`
- Creates vector index with HNSW algorithm
- 1536-dimension vectors (matches Titan embeddings)
- Faiss engine for efficient KNN search

### Legacy/Reference Modules

#### `src/config.py`
- Centralized configuration management
- Loads environment variables from `.env` file
- Defines AWS resource names, data paths, file mappings
- **Key Variables**: `AWS_PROFILE`, `AWS_REGION`, `S3_BUCKET_NAME`, `KNOWLEDGE_BASE_ID`

#### `src/cvc_chatbot_rag.py` (Main Application)
- Streamlit-based chat interface with CVC branding (blue #003366, yellow #FDB913)
- **Key Functions**:
  - `get_bedrock_clients()`: Initialize Bedrock runtime and agent runtime clients
  - `search_courses_rag(query, top_k)`: Query Knowledge Base for semantic search
  - `format_course_context(results)`: Format retrieved documents for Claude context
  - `call_claude_with_rag(messages, user_query)`: RAG pipeline - retrieve + generate
- **UI Components**: Chat history, sidebar with RAG info, example queries, GE reference
- **Session State**: `st.session_state.messages` stores conversation history

#### `src/upload_to_s3.py`
- Upload course and transfer data to S3 bucket
- **Functions**:
  - `create_s3_bucket()`: Create bucket with versioning enabled
  - `upload_course_data()`: Upload 3 course catalogs to structured S3 paths
  - `upload_transfer_data()`: Upload 3 transfer agreement files
  - `verify_uploads()`: List all files in bucket for validation
- **Run**: `python src/upload_to_s3.py`

#### `src/data_processor.py`
- Transform JSON files to Bedrock Knowledge Base format (JSON Lines with metadata)
- **Functions**:
  - `process_course_catalog()`: Convert course JSON to KB document format
  - `process_transfer_data()`: Convert transfer JSON to KB document format
  - `export_for_knowledge_base()`: Write JSONL file for S3 upload
- **Output**: `data/processed/all_documents.jsonl`
- **Run**: `python src/data_processor.py`

#### `src/cvc_chatbot_multicollege.py` (Legacy - Comparison)
- Original in-context learning version (loads JSON directly)
- Uses hardcoded keyword matching for GE areas
- Good for comparison: old approach vs. RAG

### Data Structure

#### Course Catalog Document Schema
```python
{
    "document_id": "cerritos_engl_101",
    "text": "English Composition - English Department: College-level composition...",
    "metadata": {
        "college": "Cerritos College",
        "department_code": "ENGL",
        "course_number": "101",
        "course_code": "ENGL 101",
        "title": "English Composition",
        "department": "English",
        "units": "3.0",
        "academic_year": "2019-2025",
        "source_type": "catalog"
    }
}
```

#### Transfer Document Schema
```python
{
    "document_id": "transfer_victor-valley_math-104_cal-poly-slo",
    "text": "MATH 104 (Calculus I) from Victor Valley College transfers to: MATH 141...",
    "metadata": {
        "from_college": "Victor Valley College",
        "to_college": "Cal Poly SLO",
        "from_course": "MATH 104",
        "course_title": "Calculus I",
        "units": "5.0",
        "department": "Mathematics",
        "transfers_to": ["MATH 141: Calculus I"],
        "academic_year": "2024-2025",
        "source_type": "transfer"
    }
}
```

### Mock Data Files (data/)

- `cerritos_output_final.json`: Cerritos College courses (37 courses)
- `output.json`: Mount San Antonio College courses (15 courses)
- `VVC_output.json`: Victor Valley College courses (39 courses)
- `simple_transfers.json`: VVC → Cal State Fullerton (474 transfers)
- `simple_transfers (1).json`: VVC → Cal Poly SLO (709 transfers)
- `simple_transfers (2).json`: Cuesta → Cal Poly SLO (709 transfers)

**Total**: 91 courses, 1,892 transfer mappings

---

## Quick Start

### For Demos (Mock Chatbot)

**Fastest way to demo the chatbot (NO AWS required):**

```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
./run_chatbot.sh
```

Then open **http://localhost:5173** and try:
> "I'm a student attending Cal Poly and I want some help getting some GEs over the summer"

**Manual start:**
```bash
# Terminal 1 - Backend
source .venv/bin/activate
cd backend && python app.py

# Terminal 2 - Frontend  
cd frontend && npm run dev
```

### For Production (Custom RAG Pipeline)

**Resume the full RAG pipeline with 1,981 courses:**

```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate

# 1. Create OpenSearch domain (~15 min)
python src/setup_opensearch_traditional.py

# 2. Create vector index (~1 min)
python src/create_opensearch_index_traditional.py

# 3. Upload data with embeddings (~10 min)
python src/upload_to_opensearch.py

# 4. Start chatbot
streamlit run src/cvc_chatbot_custom_rag.py --server.port 8502
```

**Cost**: ~$20-40/month when active

---

## Development Workflow

### Setup New Environment

```bash
# Navigate to project
cd /Users/rishikajain/claude/cvc-rag-chatbot

# Activate virtual environment
source .venv/bin/activate

# Verify Python version
python --version  # Should be 3.11+

# Install/update dependencies
pip install -r requirements.txt
```

### Running the Applications

**Mock Chatbot (React + FastAPI):**
```bash
# Quick start
./run_chatbot.sh

# Or manually:
# Terminal 1 - Backend
source .venv/bin/activate
cd backend && python app.py

# Terminal 2 - Frontend
cd frontend && npm run dev
```

**Custom RAG Chatbot (Streamlit + OpenSearch):**
```bash
# Activate venv
source .venv/bin/activate

# Run custom RAG chatbot (recommended)
streamlit run src/cvc_chatbot_custom_rag.py --server.port 8502

# Or legacy Bedrock KB version (if available)
streamlit run src/cvc_chatbot_rag.py --server.port 8503
```

### AWS Operations

```bash
# Upload data to S3
python src/upload_to_s3.py

# Process data to Knowledge Base format
python src/data_processor.py

# List S3 contents
aws s3 ls s3://cvc-rag-course-data --recursive --profile cvc-project

# Test Bedrock connection
aws bedrock-runtime invoke-model \
  --model-id us.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' \
  --profile cvc-project \
  --region us-west-2 \
  output.json
```

### Git Workflow

```bash
# Check status
git status

# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add semantic search for biology courses"

# View history
git log --oneline
```

## Key Concepts

### RAG (Retrieval-Augmented Generation)

**Problem**: LLMs have knowledge cutoffs and can't know real-time data (e.g., current course catalogs)
**Solution**: Retrieve relevant documents from a knowledge base, then generate responses using that context

**Benefits**:
- Always up-to-date (synced from S3)
- Cites specific courses with metadata
- Scales to 100,000+ courses without context window limits
- Semantic search (understands intent, not just keywords)

### Cal Poly GE 2026 System

Students must complete General Education (GE) requirements, organized into areas:
- **Area 1**: English & Communication (9 units)
- **Area 2**: Math (3 units)
- **Area 3**: Arts & Humanities (6 units) - 3A (Arts), 3B (Humanities)
- **Area 4**: Social Sciences (6 units)
- **Area 5**: Physical & Life Sciences (7 units) - 5A, 5B, 5C (lab)
- **Area 6**: Ethnic Studies (3 units)

Students at community colleges need courses that "transfer" (count toward these requirements at 4-year universities like Cal Poly).

### Transfer Agreements (Articulation)

**ASSIST.org**: Official database showing how community college courses transfer to CSU/UC
**Crosswalk**: Mapping of equivalent courses (e.g., "VVC MATH 104 = Cal Poly MATH 141")
**C-ID**: Course Identification system - standardized course codes across CA colleges

## Important Patterns

### Bedrock API Calls

**Claude Invocation (Runtime)**:
```python
import boto3, json

client = boto3.Session(profile_name='cvc-project').client('bedrock-runtime', region_name='us-west-2')

body = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 2000,
    "messages": [{"role": "user", "content": "Hello"}],
    "system": "You are a helpful assistant.",
    "temperature": 0.7
})

response = client.invoke_model(
    modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    body=body
)

result = json.loads(response['body'].read())
text = result['content'][0]['text']
```

**Knowledge Base Retrieval (Agent Runtime)**:
```python
client = boto3.Session(profile_name='cvc-project').client('bedrock-agent-runtime', region_name='us-west-2')

response = client.retrieve(
    knowledgeBaseId='YOUR_KB_ID',
    retrievalQuery={'text': 'I need a math course'},
    retrievalConfiguration={
        'vectorSearchConfiguration': {'numberOfResults': 10}
    }
)

results = response['retrievalResults']
for result in results:
    content = result['content']['text']
    metadata = result['metadata']
```

### Streamlit Caching

**Cache Data** (for expensive data loading):
```python
@st.cache_data
def load_data():
    return expensive_operation()
```

**Cache Resources** (for clients/connections):
```python
@st.cache_resource
def get_bedrock_client():
    return boto3.Session(...).client('bedrock-runtime')
```

### Session State (Chat History)

```python
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add message
st.session_state.messages.append({"role": "user", "content": "Hello"})

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
```

## Known Issues & Limitations

### Current Limitations

1. **Small Dataset**: Only 3 colleges, 91 courses (mock data)
2. **No Authentication**: No user accounts or saved preferences
3. **Local Only**: Runs on localhost, not deployed
4. **Manual Setup**: AWS infrastructure requires manual console configuration
5. **No Analytics**: No usage tracking or metrics

### Dependencies on Manual AWS Setup

The following must be configured manually in AWS Console:

1. **OpenSearch Serverless Collection**:
   - Name: `cvc-courses`
   - Type: Vector search
   - Index mapping: 1536-dimension vectors
   - Network access policy
   - Data access policy for Bedrock

2. **Bedrock Knowledge Base**:
   - Name: `cvc-course-catalog`
   - S3 data source: `s3://cvc-rag-course-data/`
   - Embedding model: Titan Embeddings G1
   - Vector store: OpenSearch Serverless collection
   - Sync schedule: Manual or on-demand

3. **IAM Roles & Policies**:
   - Bedrock → S3 read access
   - Bedrock → OpenSearch write access
   - Local profile `cvc-project` → Bedrock invoke permissions

### Future Infrastructure (Out of Scope)

- Lambda functions for API endpoints
- API Gateway for external integrations
- CloudWatch for logging and monitoring
- DynamoDB for user state
- Cognito for authentication
- CloudFormation/Terraform for IaC

## Cost Management (2026-07-06 Update)

### Current Monthly Costs

| Component | Status | Monthly Cost |
|-----------|--------|--------------|
| **Mock Chatbot (React + FastAPI)** | ✅ Ready | $0 |
| **S3 Storage (1,000 files)** | ✅ Active | ~$0.01 |
| **Traditional OpenSearch** | ⏸️ Paused | $0 |
| **Bedrock APIs** | ⏸️ Not in use | $0 |
| **Total Current** | | **~$0.01/month** |

### Cost When Active (Custom RAG)

| Component | Monthly Cost |
|-----------|--------------|
| OpenSearch t3.small.search | ~$26 |
| 10GB gp3 storage | ~$1 |
| Bedrock Titan Embeddings | ~$0.10 (pay-per-use) |
| Claude Haiku queries | ~$0.25 (pay-per-use) |
| S3 storage | <$0.01 |
| **Total Active** | **~$20-40/month** |

**Comparison**: 60-75% cheaper than OpenSearch Serverless ($90-180/month)

### Cost Optimization Decisions Made

1. ✅ **Switched from Serverless to Traditional OpenSearch**
   - Savings: ~$50-140/month
   - Trade-off: 15-minute setup time vs instant scaling

2. ✅ **Built Custom RAG Pipeline (no Bedrock Knowledge Base)**
   - Savings: No KB charges
   - Benefit: Full control over pipeline

3. ✅ **Created Mock Chatbot for Demos**
   - Savings: $20-40/month during non-production phases
   - Use: Stakeholder demos, prototyping

### Pause/Resume Strategy

**When to Pause** (save $20-40/month):
```bash
aws opensearch delete-domain \
  --domain-name cvc-courses \
  --profile cvc-project \
  --region us-west-2
```

**When to Resume** (30-40 min setup):
```bash
python src/setup_opensearch_traditional.py
python src/create_opensearch_index_traditional.py
python src/upload_to_opensearch.py
```

**Data preserved in S3** - nothing is lost when pausing!

---

## Debugging Tips

### Mock Chatbot

**Backend won't start:**
```bash
# Check port 8000
lsof -i :8000

# Test health
curl http://localhost:8000/api/health
```

**Frontend errors:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Custom RAG Pipeline

**Check AWS Profile:**
```bash
aws configure list --profile cvc-project
```

**Test S3 Access:**
```bash
aws s3 ls s3://cvc-rag-course-data --profile cvc-project --region us-west-2
```

**Check Resource Status:**
```bash
python src/check_status.py
```

**OpenSearch Connection:**
```bash
# Get domain status
aws opensearch describe-domain \
  --domain-name cvc-courses \
  --profile cvc-project \
  --region us-west-2
```

### Streamlit Logs

Errors appear in terminal where `streamlit run` was executed. Look for:
- `boto3` client errors (credentials, permissions)
- `ClientError` from AWS API calls
- OpenSearch connection errors
- Embedding API errors
2. Press F5 (or Run → Start Debugging)
3. Streamlit app launches in debug mode
4. Step through code when breakpoint is hit

### Cost Optimization Tips (Applied)

1. ✅ **Use Claude Haiku** (not Sonnet/Opus) - 10x cheaper
2. ✅ **Traditional OpenSearch** - t3.small.search instead of Serverless (60-75% savings)
3. ✅ **Custom RAG Pipeline** - No Bedrock Knowledge Base fees
4. ✅ **Mock Chatbot** - $0 alternative for demos
5. ✅ **Pause when idle** - Delete OpenSearch domain, keep S3 data
6. ✅ **Direct API calls** - No managed service overhead

## Next Phase: Production Deployment

### Scaling to Full Dataset

1. Ingest all 116 colleges from CVC
2. Process 100,000+ courses
3. Update assist.org data regularly via API (`make_simple_transfers.py`)
4. Add prerequisite tracking and course sequencing

### Deployment Options

**Option A: AWS Lambda + API Gateway**
- Serverless, pay-per-request
- API endpoints for external integrations
- Cold start latency (~2-3 seconds)

**Option B: ECS Fargate**
- Containerized Streamlit app
- Always-warm for low latency
- Higher cost but better UX

**Option C: Streamlit Cloud**
- Managed hosting by Streamlit
- Easiest deployment
- Limited AWS integration support

### Integration with CVC Platform

**Current CVC Architecture**:
- Domain: cvc.edu (owned by CVC)
- UI/UX: Parchment/Canvas (3rd party platform)
- APIs: end-to-end (manages 100+ custom integrations)

**Integration Strategy**:
- Deploy RAG chatbot as standalone microservice
- Expose REST API for CVC platform to call
- Embed chat widget via iframe or JavaScript SDK
- SSO integration with CVC authentication

## Documentation Reference

### Quick Reference
- **QUICKSTART.md** - Fastest way to get started (read this first!)
- **REACT_CHATBOT_README.md** - Mock chatbot documentation
- **CUSTOM_RAG_SUMMARY.md** - Full RAG pipeline details
- **PAUSE_RESUME.md** - Cost management and pause/resume instructions
- **CLAUDE.md** - This file (complete project reference)

### By Use Case

**I want to demo the chatbot quickly:**
→ Read `QUICKSTART.md` and run `./run_chatbot.sh`

**I need to understand the GE conversation flow:**
→ Check `backend/app.py` and `REACT_CHATBOT_README.md`

**I want to deploy the production RAG version:**
→ Follow `CUSTOM_RAG_SUMMARY.md`

**I need to pause/resume AWS services:**
→ See `PAUSE_RESUME.md`

**I want to understand the full architecture:**
→ You're reading it! (CLAUDE.md)

---

## Current Project Status (2026-07-06)

### ✅ Completed Milestones

1. **Phase 1**: Project initialization and AWS setup ✅
2. **Phase 2**: Data ingestion (1,981 documents) ✅
3. **Phase 3**: Custom RAG pipeline implementation ✅
4. **Phase 4**: Cost optimization (60-75% reduction) ✅
5. **Phase 5**: React + FastAPI mock chatbot ✅

### 📊 Current State

**Infrastructure:**
- ✅ S3 bucket with 1,000 files (active)
- ⏸️ OpenSearch domain (paused/deleted)
- ⏸️ Bedrock APIs (not in use)
- ✅ All code and data preserved

**Applications:**
- ✅ Mock chatbot (React + FastAPI) - Ready for demos
- ✅ Custom RAG chatbot (Streamlit + OpenSearch) - Code ready, can resume in 30-40 min
- ⚠️ Legacy KB chatbot (Bedrock Knowledge Base) - Deprecated

**Monthly Cost:** ~$0.01 (essentially free)

### 🎯 Next Steps

**Immediate** (Demo Phase):
- ✅ Use mock chatbot for stakeholder demos
- ✅ Collect user feedback on conversation flow
- ✅ Iterate on GE explanations and course display

**Short-term** (Testing):
- Resume custom RAG pipeline for quality testing
- Compare search results: mock vs semantic
- Benchmark response quality
- Test with real user queries

**Long-term** (Production):
- Scale to all 116 CA community colleges
- Ingest 100,000+ courses
- Deploy to AWS (Lambda + API Gateway or ECS)
- Integrate with CVC platform (cvc.edu)
- Add authentication and analytics

---

## Contact & Resources

**Project Owner**: Cal Poly DX Hub (Darren Kraker, Riya, Nick)
**Stakeholder**: Marina Aminy (Executive Director, CVC)
**AWS Account**: `cvc-project` profile
**Code Repository**: `/Users/rishikajain/claude/cvc-rag-chatbot/`
**GitHub**: https://github.com/kitkat357/cvc.git

**Architecture Decisions:**
- ✅ Custom RAG > Bedrock Knowledge Base (cost + control)
- ✅ Traditional OpenSearch > Serverless (60-75% savings)
- ✅ Mock chatbot for demos (zero AWS cost)
- ✅ Direct API calls > Managed services (transparency)

---

*Last Updated*: 2026-07-06  
*Current Phase*: Demo Phase (Mock chatbot ready, RAG pipeline paused)  
*Status*: Production-ready code, AWS services paused for cost savings  
*Achievement*: Two working implementations (mock + production) with 60-75% cost optimization! 🎉
