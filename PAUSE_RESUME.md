# Project Pause/Resume Guide

## ✅ Project Status: PAUSED (Custom RAG Pipeline Ready)

**Date Last Updated**: 2026-07-06  
**Current Cost**: ~$0.01/month (S3 storage only)  
**Architecture**: Custom RAG Pipeline with Traditional OpenSearch (when active)  
**Status**: All AWS compute resources deleted, data preserved in S3

---

## 🔄 Architecture Migration (2026-07-06)

### Old Setup (Deleted)
- ❌ OpenSearch Serverless collection (was $90-180/month)
- ❌ Bedrock Knowledge Base (no longer needed)

### New Setup (Custom RAG Pipeline - Cost-Optimized!)
- ✅ **Custom RAG Implementation**: Direct Bedrock API calls, no managed Knowledge Base
- ✅ **Traditional OpenSearch**: t3.small.search instances (~$20-40/month when active)
- ✅ **1,981 Documents Processed**: All courses and transfers embedded and indexed
- ✅ **Full Control**: 100% Python code, no black-box services
- 💰 **60-75% Cost Savings** vs Serverless OpenSearch

---

## ✅ What Was Kept (Safe)

- ✅ **S3 Bucket**: `cvc-rag-course-data` with 1,981 documents (costs <$0.01/month)
- ✅ **IAM Role**: `cvc-course-catalog-role` (free)
- ✅ **Git Repository**: https://github.com/kitkat357/cvc.git (all code backed up)
- ✅ **Local Files**: All source code in `/Users/rishikajain/claude/cvc-rag-chatbot/`

**Nothing is lost!** All your data is preserved in S3.

---

## 🚀 How to Resume with Traditional OpenSearch (Cost-Optimized)

### Resume Steps (30-40 minutes - one-time setup)

```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate

# Step 1: Create traditional OpenSearch domain (~15 min)
python src/setup_opensearch_traditional.py

# Step 2: Create OpenSearch index (~1 min)
python src/create_opensearch_index_traditional.py

# Step 3: Create Knowledge Base (~5 min)
python src/setup_knowledge_base_traditional.py
# Copy the new Knowledge Base ID from output

# Step 4: Update .env file with new KB ID
# Edit .env and update KNOWLEDGE_BASE_ID=<new-id>

# Step 5: Start chatbot
streamlit run src/cvc_chatbot_rag.py --server.port 8502
```

**Total time**: 30-40 minutes (traditional domains take longer to create)  
**Monthly cost**: ~$20-40/month (60-75% cheaper than Serverless!)

### Quick Start/Stop (After Initial Setup)

Once the domain is created, you can pause/resume quickly:

**To Pause** (stop charges):
```bash
# Delete the domain (keeps S3 data)
aws opensearch delete-domain --domain-name cvc-courses --profile cvc-project --region us-west-2
```

**To Resume** (from paused state):
```bash
# Recreate domain and sync data (~30 min)
python src/setup_opensearch_traditional.py
python src/create_opensearch_index_traditional.py
python src/setup_knowledge_base_traditional.py
```

---

## 💰 Cost Comparison

| Architecture | Monthly Cost | Daily Cost | Notes |
|--------------|-------------|------------|-------|
| **Traditional OpenSearch** (current) | $20-40 | $0.67-1.33 | t3.small.search instance |
| **OpenSearch Serverless** (old) | $90-180 | $3-6 | Pay per OCU-hour |
| **Paused** (S3 only) | $0.01 | $0.0003 | Just storage |
| **Deleted** (nothing) | $0 | $0 | Everything removed |

### Cost Breakdown (Traditional)

- **OpenSearch Domain**: $20-40/month
  - t3.small.search instance: ~$0.036/hour × 730 hours = ~$26/month
  - 10GB gp3 storage: ~$1/month
- **S3 Storage**: <$0.01/month
- **Bedrock Usage**: Pay per use
  - Claude Haiku: ~$0.25/1M input tokens
  - Titan Embeddings: ~$0.10/1M tokens

**Total**: ~$20-40/month vs $90-180/month with Serverless  
**Savings**: ~$50-140/month (60-75% reduction!)

---

## 📊 Alternative: Delete Everything

If you want to **completely delete the project** (including S3 data):

```bash
# Delete S3 bucket and all data
aws s3 rb s3://cvc-rag-course-data --force --profile cvc-project

# Delete IAM role
aws iam delete-role-policy --role-name cvc-course-catalog-role --policy-name S3Access --profile cvc-project
aws iam delete-role-policy --role-name cvc-course-catalog-role --policy-name BedrockAccess --profile cvc-project
aws iam delete-role-policy --role-name cvc-course-catalog-role --policy-name OpenSearchAccess --profile cvc-project
aws iam delete-role --role-name cvc-course-catalog-role --profile cvc-project

# Delete local files (optional)
rm -rf /Users/rishikajain/claude/cvc-rag-chatbot
```

**Warning**: This is permanent! You'd need to rebuild from GitHub and re-upload data.

---

## 📝 Notes

- **S3 data is preserved**: Your 1,981 course documents are still in S3 (~$0.01/month)
- **Code is on GitHub**: https://github.com/kitkat357/cvc.git
- **Resume anytime**: Just run the 5 commands above
- **No data loss**: OpenSearch is just an index - all original data is in S3

---

## 🔔 When to Resume

Resume the project when:
- You want to demo to stakeholders
- You're ready to scale to 116 colleges
- You want to do more testing
- You're deploying to production

Don't resume if:
- You're just planning/documenting
- You're waiting for more data
- You don't need the chatbot running

---

**Questions?** Check the main README.md or CLAUDE.md in this repo.
