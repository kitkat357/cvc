# Phase 2: AWS Infrastructure Setup - Summary

## Completed ✓

### 1. S3 Bucket Created
- **Bucket Name**: `cvc-rag-course-data`
- **Region**: `us-west-2`
- **Files Uploaded**: 1,983 documents (converted to .txt format)
- **Structure**:
  ```
  s3://cvc-rag-course-data/
  └── documents/
      ├── catalogs/
      │   ├── cerritos-college/
      │   ├── mount-san-antonio/
      │   └── victor-valley/
      └── transfers/
          ├── victor-valley-to-cal-state-fullerton/
          ├── victor-valley-to-cal-poly-slo/
          └── cuesta-to-cal-poly-slo/
  ```
- **Versioning**: Enabled
- **Total Size**: ~456 KB

### 2. OpenSearch Serverless Collection Created
- **Collection Name**: `cvc-courses`
- **Collection ID**: `j409jdcw8ff01uuoo5od`
- **Type**: VECTORSEARCH
- **Status**: ACTIVE ✓
- **Endpoint**: `https://j409jdcw8ff01uuoo5od.us-west-2.aoss.amazonaws.com`
- **Index Created**: `cvc-courses-index`
  - Vector dimension: 1536 (Titan Embeddings G1)
  - Algorithm: HNSW (Faiss)
  - Parameters: ef_construction=512, m=16

### 3. Security Policies Configured
- ✓ Encryption policy: AWS-owned key
- ✓ Network policy: Public access (IAM auth)
- ✓ Data access policy: Configured for:
  - Your IAM user/role
  - Bedrock service role
  - Knowledge Base IAM role

### 4. Bedrock Knowledge Base Created
- **Name**: `cvc-course-catalog`
- **Knowledge Base ID**: `LRSHYRSQ6L` ⭐
- **ARN**: `arn:aws:bedrock:us-west-2:350681797478:knowledge-base/LRSHYRSQ6L`
- **Embedding Model**: Titan Embeddings G1 (`amazon.titan-embed-text-v1`)
- **Vector Store**: OpenSearch Serverless (cvc-courses collection)
- **Data Source Created**: S3 bucket `cvc-rag-course-data`
- **Data Source ID**: `XC53CWCQ7G`

### 5. IAM Role Created
- **Role Name**: `cvc-course-catalog-role`
- **ARN**: `arn:aws:iam::350681797478:role/cvc-course-catalog-role`
- **Permissions**:
  - ✓ S3 read access (cvc-rag-course-data bucket)
  - ✓ Bedrock model invocation (Titan Embeddings)
  - ✓ OpenSearch Serverless access (cvc-courses collection)

### 6. Environment Configuration
- **File**: `.env` created with Knowledge Base ID
- **Configuration**:
  ```env
  AWS_PROFILE=cvc-project
  AWS_REGION=us-west-2
  S3_BUCKET_NAME=cvc-rag-course-data
  KNOWLEDGE_BASE_ID=LRSHYRSQ6L
  CLAUDE_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0
  ```

---

## Data Processing Pipeline

### Initial Upload (Structured JSON)
- ❌ Failed: Bedrock KB doesn't support nested JSON metadata
- Learned: KB expects plain text files (.txt, .md, .pdf)

### Conversion (Plain Text Format)
- ✓ Converted 1,983 documents from JSONL to plain text
- Format: Each course/transfer as individual .txt file
- Metadata: Embedded in text content + S3 object metadata
- Structure:
  ```
  91 courses (catalogs) → 91 .txt files
  1,892 transfers → 1,892 .txt files
  Total: 1,983 documents
  ```

---

## Scripts Created

### Infrastructure Setup Scripts
1. **`src/upload_to_s3.py`**
   - Creates S3 bucket
   - Uploads data with proper structure
   - Enables versioning

2. **`src/setup_opensearch.py`**
   - Creates OpenSearch Serverless collection
   - Configures encryption, network, and data access policies
   - Waits for collection to become ACTIVE

3. **`src/create_opensearch_index.py`**
   - Creates vector index in OpenSearch
   - Configures HNSW algorithm for vector search
   - Sets dimension to 1536 for Titan Embeddings

4. **`src/setup_knowledge_base.py`**
   - Creates IAM role with required permissions
   - Creates Bedrock Knowledge Base
   - Connects to S3 and OpenSearch
   - Creates data source and starts ingestion

### Data Processing Scripts
5. **`src/data_processor.py`**
   - Transforms course/transfer JSON to structured documents
   - Adds metadata fields
   - Outputs JSONL format

6. **`src/convert_for_bedrock.py`**
   - Converts JSONL to plain text files
   - Uploads to S3 in correct format for Bedrock KB
   - Preserves metadata in S3 object tags

---

## Current Status

✅ **READY FOR TESTING**

All infrastructure is configured and operational:
- S3 bucket with 1,983 .txt files
- OpenSearch Serverless collection ACTIVE
- Bedrock Knowledge Base created
- Data source configured

**Next Action**: Trigger data sync in Knowledge Base

---

## Testing Steps

### 1. Start Data Sync

**Option A: AWS Console** (Recommended for first time)
```
1. Go to: https://console.aws.amazon.com/bedrock/home?region=us-west-2#/knowledge-bases
2. Click: cvc-course-catalog
3. Click: Data sources tab
4. Click: cvc-course-catalog-s3-source
5. Click: Sync button
6. Wait: 2-5 minutes for sync to complete
7. Verify: Status shows "COMPLETE" with 1,983 documents indexed
```

**Option B: AWS CLI**
```bash
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id LRSHYRSQ6L \
  --data-source-id XC53CWCQ7G \
  --profile cvc-project \
  --region us-west-2
```

### 2. Verify Sync Completion

```bash
# Monitor ingestion job
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id LRSHYRSQ6L \
  --data-source-id XC53CWCQ7G \
  --max-results 1 \
  --profile cvc-project \
  --region us-west-2
```

Look for:
- `status`: `COMPLETE`
- `numberOfDocumentsScanned`: 1983
- `numberOfNewDocumentsIndexed`: 1983
- `numberOfDocumentsFailed`: 0

### 3. Test Knowledge Base Query

```python
import boto3

session = boto3.Session(profile_name='cvc-project', region_name='us-west-2')
bedrock_agent = session.client('bedrock-agent-runtime')

response = bedrock_agent.retrieve(
    knowledgeBaseId='LRSHYRSQ6L',
    retrievalQuery={'text': 'I need a 3-unit math course'},
    retrievalConfiguration={
        'vectorSearchConfiguration': {'numberOfResults': 5}
    }
)

for result in response['retrievalResults']:
    print(f"Score: {result['score']}")
    print(f"Text: {result['content']['text'][:200]}...")
    print(f"Metadata: {result.get('metadata', {})}")
    print("---")
```

### 4. Run RAG Chatbot

```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate
streamlit run src/cvc_chatbot_rag.py
```

**Test Queries**:
- "I need a transferable English class"
- "Show me 3-unit math courses"
- "What psychology courses transfer to Cal Poly?"
- "Find me Area 3B humanities classes"

---

## Troubleshooting

### If Ingestion Fails

**Check S3 data format**:
```bash
aws s3 ls s3://cvc-rag-course-data/documents/ --recursive --profile cvc-project | head
```

Should see .txt files, not .json files.

**Check OpenSearch index**:
```bash
aws opensearchserverless batch-get-collection \
  --ids j409jdcw8ff01uuoo5od \
  --profile cvc-project \
  --region us-west-2
```

Should show status: ACTIVE

**Check IAM permissions**:
```bash
aws iam get-role --role-name cvc-course-catalog-role --profile cvc-project
aws iam list-role-policies --role-name cvc-course-catalog-role --profile cvc-project
```

### If Queries Return No Results

1. Verify sync completed successfully
2. Check number of documents indexed (should be 1,983)
3. Try simpler query: "math"
4. Check OpenSearch index has documents:
   ```bash
   # Query index stats (requires data access policy)
   curl -X GET "https://j409jdcw8ff01uuoo5od.us-west-2.aoss.amazonaws.com/cvc-courses-index/_count" \
     --aws-sigv4 "aws:amz:us-west-2:aoss" \
     --user "$AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY"
   ```

---

## Cost Estimate (Current Setup)

**Monthly Costs with Mock Data**:
- S3 Storage: <$0.10 (456 KB)
- OpenSearch Serverless: ~$20-40 (depends on usage)
- Bedrock Knowledge Base: ~$0.10 per 1,000 queries
- Claude Haiku: ~$0.25 per 1M tokens
- Titan Embeddings: ~$0.10 per 1M tokens (one-time for ingestion)

**Total**: ~$25-50/month for development/testing

**Per Query Cost**: ~$0.0005 (half a cent)

---

## Next Phase: Testing & Validation

Once data sync completes:
1. ✅ Test RAG queries via boto3
2. ✅ Run Streamlit chatbot
3. ✅ Compare RAG vs. in-context learning (old chatbot)
4. ✅ Validate response accuracy
5. ✅ Measure query latency
6. ✅ Document findings

---

**Status**: Phase 2 infrastructure complete, awaiting data sync ⏳
