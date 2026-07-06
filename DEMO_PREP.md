# Demo Preparation Guide

Quick reference for pausing AWS resources to save costs and resuming them before a demo.

---

## Current Status (2026-07-06)

✅ **OpenSearch Domain**: Active  
✅ **S3 Bucket**: Active (always keep this - costs $0.01/month)  
✅ **Mock Chatbot**: Ready at http://localhost:5173 (no AWS needed)  

**Current Monthly Cost**: ~$26-40 (OpenSearch only, S3 is negligible)

---

## Option 1: Use Mock Chatbot (No AWS Needed) 🎯 RECOMMENDED

**Best for**: Quick demos, stakeholder presentations, UI/UX showcases

### To Run:
```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
./run_chatbot.sh
```

Then open **http://localhost:5173**

**Pros**:
- ✅ Instant startup (30 seconds)
- ✅ No AWS costs
- ✅ Shows enrollment flow
- ✅ Demonstrates GE conversation logic

**Cons**:
- ❌ Only 10 hardcoded courses
- ❌ No real semantic search
- ❌ Pattern matching instead of AI

---

## Option 2: Use Full RAG Pipeline (AWS Required)

**Best for**: Technical demos, showing semantic search, production-ready features

### Current Status Check

Run this to see if OpenSearch is active:
```bash
python src/check_status.py
```

---

## How to PAUSE AWS Resources (Save ~$26-40/month)

### What Gets Paused:
- ❌ OpenSearch domain (deleted)
- ✅ S3 data (KEPT - your 1,981 documents are safe!)

### Steps to Pause:

1. **Delete OpenSearch Domain**:
```bash
aws opensearch delete-domain \
  --domain-name cvc-courses \
  --profile cvc-project \
  --region us-west-2
```

2. **Wait for deletion** (takes ~10 minutes):
```bash
# Check deletion status
aws opensearch describe-domain \
  --domain-name cvc-courses \
  --profile cvc-project \
  --region us-west-2 2>&1
  
# When fully deleted, you'll see: "ResourceNotFoundException"
```

3. **Verify S3 data is intact**:
```bash
aws s3 ls s3://cvc-rag-course-data/documents/ \
  --profile cvc-project \
  --region us-west-2 \
  --recursive | wc -l
  
# Should show ~1,000 files
```

**After pausing**: Monthly cost drops to ~$0.01 (just S3 storage)

---

## How to RESUME AWS Resources (Before Demo)

### Timeline: **Allow 30-40 minutes before demo**

### Step 1: Recreate OpenSearch Domain (~15 min)
```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate
python src/setup_opensearch_traditional.py
```

**What this does**:
- Creates t3.small.search OpenSearch domain
- Configures access policies for Bedrock
- Waits for domain to become active (~10-15 min)

**Expected output**:
```
=== Creating Traditional OpenSearch Domain ===
Domain Name: cvc-courses
Region: us-west-2
Instance Type: t3.small.search (cost-optimized)
Estimated Cost: ~$20-40/month

✓ Domain creation initiated!
✓ Domain is ACTIVE!
Endpoint: https://search-cvc-courses-....us-west-2.es.amazonaws.com
```

### Step 2: Create Vector Index (~1 min)
```bash
python src/create_opensearch_index_traditional.py
```

**What this does**:
- Creates index with HNSW algorithm
- Sets up 1536-dimension vector field for embeddings

**Expected output**:
```
=== Creating OpenSearch Index ===
✓ Index 'cvc-courses-index' created successfully
```

### Step 3: Upload Data with Embeddings (~10-15 min)
```bash
python src/upload_to_opensearch.py
```

**What this does**:
- Reads 1,981 documents from processed data
- Generates embeddings via Bedrock Titan
- Uploads to OpenSearch in batches of 50

**Expected output**:
```
Processing course catalog: data/cerritos_output_final.json
Processing course catalog: data/VVC_output.json
Processing course catalog: data/output.json
Processing transfer data: data/simple_transfers.json
Processing transfer data: data/simple_transfers (1).json
Processing transfer data: data/simple_transfers (2).json

Uploading batch 1/40 (50 documents)...
Uploading batch 2/40 (50 documents)...
...
✓ Uploaded 1,981 documents successfully
```

### Step 4: Start RAG Chatbot
```bash
streamlit run src/cvc_chatbot_custom_rag.py --server.port 8502
```

Open **http://localhost:8502**

### Step 5: Test the System

Try these queries:
1. "I need a math course that transfers to Cal Poly"
2. "Show me biology courses with labs"
3. "I want to satisfy Area 3 GE requirements"

**Expected behavior**:
- Semantic search finds relevant courses
- Shows source documents with relevance scores
- AI-generated responses using Claude Haiku

---

## Quick Resume Checklist (30-40 min before demo)

- [ ] **T-40 min**: Run `python src/setup_opensearch_traditional.py`
- [ ] **T-25 min**: OpenSearch should be active
- [ ] **T-24 min**: Run `python src/create_opensearch_index_traditional.py`
- [ ] **T-23 min**: Run `python src/upload_to_opensearch.py`
- [ ] **T-10 min**: Data upload complete
- [ ] **T-5 min**: Run `streamlit run src/cvc_chatbot_custom_rag.py --server.port 8502`
- [ ] **T-0 min**: Test with a few queries
- [ ] **Demo time**: You're ready! 🎉

---

## Troubleshooting

### OpenSearch domain creation fails
```bash
# Check if domain already exists
aws opensearch describe-domain \
  --domain-name cvc-courses \
  --profile cvc-project \
  --region us-west-2
  
# If exists but in wrong state, delete and retry
aws opensearch delete-domain \
  --domain-name cvc-courses \
  --profile cvc-project \
  --region us-west-2
```

### Index creation fails
```bash
# Check domain endpoint
python src/check_status.py

# Make sure domain is fully active (not "Processing")
```

### Data upload is slow
- Normal! Embedding 1,981 documents takes 10-15 minutes
- Bedrock Titan API processes ~2-3 documents per second
- You'll see progress: "Uploading batch X/40..."

### Chatbot shows "No results found"
```bash
# Verify data was uploaded
python -c "
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

session = boto3.Session(profile_name='cvc-project', region_name='us-west-2')
credentials = session.get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    'us-west-2',
    'es',
    session_token=credentials.token
)

opensearch = session.client('opensearch')
domain = opensearch.describe_domain(DomainName='cvc-courses')
endpoint = domain['DomainStatus']['Endpoint']

client = OpenSearch(
    hosts=[{'host': endpoint, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

count = client.count(index='cvc-courses-index')
print(f\"Total documents: {count['count']}\")
"
```

Expected: `Total documents: 1981`

---

## Cost Breakdown

| State | Monthly Cost | Components |
|-------|--------------|------------|
| **Paused** | ~$0.01 | S3 storage only |
| **Active** | ~$26-40 | OpenSearch t3.small.search + S3 + Bedrock usage |

**Bedrock Costs** (pay-per-use, included in "Active"):
- Titan Embeddings: ~$0.10/month (mostly during upload)
- Claude Haiku: ~$0.25-1.00/month (depends on usage)

---

## Demo Recommendations

### For Non-Technical Audiences:
→ **Use Mock Chatbot** (Option 1)
- Instant startup
- Shows UI/UX and conversation flow
- No risk of AWS issues

### For Technical Audiences / Investors:
→ **Use Full RAG Pipeline** (Option 2)
- Shows real semantic search
- Demonstrates scalability
- Highlights AI capabilities

### For "Just in Case":
→ **Have Both Ready**
- Mock chatbot as backup (always works)
- RAG pipeline for deep dive if asked

---

## After Demo

### If keeping it active for follow-ups:
- Cost: ~$26-40/month
- No action needed

### If pausing to save costs:
```bash
# Delete OpenSearch domain
aws opensearch delete-domain \
  --domain-name cvc-courses \
  --profile cvc-project \
  --region us-west-2
  
# Keep S3 data! (costs only $0.01/month)
```

---

## Contact Info

- **Project Directory**: `/Users/rishikajain/claude/cvc-rag-chatbot/`
- **GitHub**: https://github.com/kitkat357/cvc.git
- **AWS Profile**: `cvc-project`
- **AWS Region**: `us-west-2`

---

*Last Updated*: 2026-07-06  
*Status*: OpenSearch currently active, ready for demos
