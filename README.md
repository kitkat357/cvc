# CVC RAG Chatbot

AI-powered conversational search interface for California Virtual Campus (CVC) using RAG (Retrieval-Augmented Generation).

## Overview

This project enhances the CVC course search experience by replacing jargon-heavy keyword search with natural language processing and semantic search. Students can ask questions in plain English to find courses across 116 California community colleges.

**Current State**: Prototype with 3 colleges and mock data (91 courses, 1,892 transfer mappings)
**Target**: Scale to 100,000+ courses serving 2.2M students annually

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Streamlit Web Interface                   │
│       (Natural Language Chat Interface)             │
└────────────────┬────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌─────────────┐  ┌──────────────────────────────┐
│   S3 Bucket │  │   AWS Bedrock Services:      │
│  (Course    │→ │   - Knowledge Base           │
│   Data)     │  │   - Titan Embeddings         │
└─────────────┘  │   - Claude Haiku 4.5         │
                 │   - OpenSearch Serverless    │
                 └──────────────────────────────┘
                              │
                              ▼
                 ┌──────────────────────────────┐
                 │   RAG Pipeline:              │
                 │   1. Semantic Search         │
                 │   2. Context Retrieval       │
                 │   3. LLM Response Generation │
                 └──────────────────────────────┘
```

## Features

- **Natural Language Search**: Ask questions in plain English instead of using jargon (CSU GE areas, C-ID codes)
- **Semantic Understanding**: Vector search understands intent, not just keywords
- **Multi-College Support**: Search across multiple community colleges simultaneously
- **Transfer Information**: Shows course equivalencies and articulation agreements
- **Real-Time Updates**: Data synced from S3 automatically
- **Scalable**: OpenSearch Serverless handles 100,000+ courses

## Setup

### Prerequisites

- Python 3.11+
- AWS Account with:
  - Bedrock access (Claude Haiku 4.5, Titan Embeddings)
  - S3 bucket permissions
  - OpenSearch Serverless access
- AWS CLI configured with `cvc-project` profile

### Installation

1. **Clone and navigate to project**:
   ```bash
   cd cvc-rag-chatbot
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your AWS configuration
   ```

   Required variables:
   - `AWS_PROFILE=cvc-project`
   - `AWS_REGION=us-west-2`
   - `S3_BUCKET_NAME=cvc-rag-course-data`
   - `KNOWLEDGE_BASE_ID=<your-kb-id>`

### AWS Infrastructure Setup

#### 1. Create S3 Bucket

```bash
python src/upload_to_s3.py
```

This will:
- Create S3 bucket `cvc-rag-course-data`
- Upload 3 course catalogs (Cerritos, Mount San Antonio, Victor Valley)
- Upload 3 transfer agreement files
- Enable versioning

#### 2. Create OpenSearch Serverless Collection

1. Go to AWS Console → OpenSearch Service → Serverless collections
2. Click "Create collection"
3. Settings:
   - Name: `cvc-courses`
   - Type: Vector search
   - Region: `us-west-2`
4. Configure network access (public with IAM auth recommended for dev)
5. Configure data access policy for Bedrock

#### 3. Create Bedrock Knowledge Base

1. Go to AWS Console → Bedrock → Knowledge Bases
2. Click "Create knowledge base"
3. Configure:
   - Name: `cvc-course-catalog`
   - S3 data source: `s3://cvc-rag-course-data/`
   - Embedding model: Titan Embeddings G1
   - Vector store: Select your OpenSearch Serverless collection
4. Click "Sync data source"
5. Copy Knowledge Base ID to `.env` file

#### 4. Test Setup

```bash
# Process data (optional - S3 already has correct format)
python src/data_processor.py

# Verify S3 uploads
aws s3 ls s3://cvc-rag-course-data --recursive --profile cvc-project

# Run chatbot
streamlit run src/cvc_chatbot_rag.py
```

## Usage

### Run the Chatbot

```bash
source .venv/bin/activate
streamlit run src/cvc_chatbot_rag.py
```

Navigate to `http://localhost:8501`

### Example Queries

**Natural Language:**
- "I need a transferable English class"
- "Show me 3-unit math courses"
- "What psychology courses transfer to Cal Poly?"

**GE Requirements:**
- "Find me Area 3B humanities classes"
- "I need Area 4 social science with 3 units"

**Cross-College:**
- "Which colleges offer biology lab courses?"
- "Compare art courses across all colleges"

### Compare RAG vs. In-Context Learning

```bash
# Terminal 1: Old version (in-context)
cd ..
streamlit run cvc_chatbot_multicollege.py --server.port 8501

# Terminal 2: New version (RAG)
cd cvc-rag-chatbot
streamlit run src/cvc_chatbot_rag.py --server.port 8502
```

## Project Structure

```
cvc-rag-chatbot/
├── .venv/                          # Python virtual environment
├── data/                           # Mock course data (gitignored)
│   ├── cerritos_output_final.json
│   ├── output.json
│   ├── VVC_output.json
│   └── simple_transfers*.json
├── src/
│   ├── cvc_chatbot_rag.py         # RAG-enhanced Streamlit app
│   ├── data_processor.py          # Transform JSON to RAG format
│   ├── upload_to_s3.py            # Upload data to S3
│   └── config.py                  # Centralized configuration
├── tests/
│   └── test_rag_pipeline.py       # Unit/integration tests
├── .vscode/                        # VSCode configuration
├── .env                            # Environment variables (gitignored)
├── .env.example                    # Environment template
├── .gitignore
├── requirements.txt
└── README.md
```

## Development

### Data Processing

Transform JSON files to Knowledge Base format:

```bash
python src/data_processor.py
```

Output: `data/processed/all_documents.jsonl`

### Testing

```bash
pytest tests/
```

### VSCode Debugging

Press F5 to debug Streamlit app (configured in `.vscode/launch.json`)

## Cost Estimate

**Development (Mock Data):**
- S3 storage: <$0.10/month
- Bedrock Knowledge Base: ~$0.10/1K queries
- Claude Haiku: ~$0.25/1M input tokens
- Titan Embeddings: ~$0.10/1M tokens
- **Total**: <$10/month for 1,000+ test queries

**Production (Full Dataset):**
- ~$50-100/month for 10K+ monthly active users

## Next Steps

- [ ] Scale to full CVC dataset (100,000+ courses, 116 colleges)
- [ ] Add course crosswalk visualization with assist.org API
- [ ] Implement user authentication and saved course lists
- [ ] Deploy to AWS Lambda + API Gateway
- [ ] Integrate with summer camp cohort for 5-day sprint
- [ ] Add analytics and usage tracking

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: Claude Haiku 4.5 (via AWS Bedrock)
- **Embeddings**: Bedrock Titan Embeddings G1
- **Vector Database**: OpenSearch Serverless
- **Storage**: AWS S3
- **RAG Framework**: AWS Bedrock Knowledge Bases
- **Language**: Python 3.11+

## License

This project is part of the Cal Poly DX Hub initiative in partnership with California Virtual Campus.

## Contact

For questions about this project, contact the Cal Poly DX Hub team or Marina Aminy (Executive Director, CVC).
