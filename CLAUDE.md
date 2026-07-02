# CLAUDE.md - CVC RAG Chatbot Project

## Project Overview

**Name**: CVC LLM Search Enhancement - RAG Chatbot
**Purpose**: Enhance California Virtual Campus (CVC) course search with natural language processing and semantic search
**Primary Users**: California community college students seeking transferable courses
**Scale**: Currently 3 colleges (mock data), target 116 colleges with 100,000+ courses serving 2.2M students

## Architecture

### Technology Stack

- **Frontend**: Streamlit (Python web framework for ML/AI apps)
- **LLM**: Claude Haiku 4.5 via AWS Bedrock (`us.anthropic.claude-haiku-4-5-20251001-v1:0`)
- **Embeddings**: AWS Bedrock Titan Embeddings G1 (1536-dimension vectors)
- **Vector Database**: AWS OpenSearch Serverless (vector engine)
- **RAG Framework**: AWS Bedrock Knowledge Bases (managed RAG pipeline)
- **Storage**: AWS S3 (`cvc-rag-course-data` bucket)
- **Region**: us-west-2 (Oregon)
- **AWS Profile**: `cvc-project`

### RAG Pipeline

1. **User Query** → Streamlit chat input
2. **Semantic Embedding** → Bedrock Titan converts query to 1536-dim vector
3. **Vector Search** → OpenSearch Serverless finds similar course documents
4. **Context Retrieval** → Top-k relevant courses retrieved (default k=15)
5. **LLM Generation** → Claude Haiku generates response with retrieved context
6. **Response Display** → Formatted in Streamlit chat interface

### Data Flow

```
S3 Bucket (cvc-rag-course-data)
├── catalogs/{college}/{year}/courses.json
└── transfers/{from}-to-{to}/{year}/transfers.json
        ↓
Bedrock Knowledge Base (auto-sync)
        ↓
OpenSearch Serverless (vector index)
        ↓
Bedrock Agent Runtime (retrieve API)
        ↓
Claude Haiku (response generation)
```

## Project Structure

### Core Modules

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

### Running the Application

```bash
# Activate venv
source .venv/bin/activate

# Run RAG chatbot
streamlit run src/cvc_chatbot_rag.py

# Or run on specific port
streamlit run src/cvc_chatbot_rag.py --server.port 8502

# Compare with old version
streamlit run ../cvc_chatbot_multicollege.py --server.port 8501
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

## Debugging Tips

### Check AWS Profile

```bash
aws configure list --profile cvc-project
```

### Test S3 Access

```bash
aws s3 ls s3://cvc-rag-course-data --profile cvc-project --region us-west-2
```

### Verify Knowledge Base Sync

AWS Console → Bedrock → Knowledge Bases → `cvc-course-catalog` → Data source → Check last sync status

### Streamlit Logs

Errors appear in terminal where `streamlit run` was executed. Look for:
- `boto3` client errors (credentials, permissions)
- `ClientError` from AWS API calls
- Knowledge Base ID not found errors

### VSCode Debugging

1. Set breakpoints in `src/cvc_chatbot_rag.py`
2. Press F5 (or Run → Start Debugging)
3. Streamlit app launches in debug mode
4. Step through code when breakpoint is hit

## Cost Management

### Development Costs (<$10/month)

- S3: <$0.10/month (few MB of JSON)
- OpenSearch Serverless: ~$0.25/OCU-hour (scales to zero when idle)
- Bedrock Knowledge Base: ~$0.10/1K queries
- Claude Haiku: ~$0.25/1M input tokens
- Titan Embeddings: ~$0.10/1M tokens

### Cost Optimization Tips

1. **Use Claude Haiku** (not Sonnet/Opus) - 10x cheaper
2. **Limit top_k** - Retrieving 15 docs instead of 50 reduces cost
3. **OpenSearch Serverless** - Only pay when querying (not idle EC2 instances)
4. **S3 versioning** - Keep old versions in case of data corruption

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

## Contact & Resources

**Project Owner**: Cal Poly DX Hub (Darren Kraker, Riya, Nick)
**Stakeholder**: Marina Aminy (Executive Director, CVC)
**AWS Account**: `cvc-project` profile
**Documentation**: This CLAUDE.md file + README.md
**Code Repository**: `/Users/rishikajain/claude/cvc-rag-chatbot/`

---

*Last Updated*: 2026-07-02
*Project Phase*: Phase 1 Complete (Project Initialization), Ready for Phase 2 (AWS Infrastructure Setup)
