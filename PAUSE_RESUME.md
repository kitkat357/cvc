# Project Pause/Resume Guide

## ✅ Project Status: PAUSED

**Date Paused**: 2026-07-03  
**Reason**: Stop idle charges (~$90-180/month)  
**Current Cost**: ~$0.01/month (essentially free)

---

## 🛑 What Was Deleted

- ❌ OpenSearch Serverless collection `j409jdcw8ff01uuoo5od` (was $90-180/month)
- ❌ Bedrock Knowledge Base `NVIJPDFIJU` (no cost when idle anyway)
- ❌ Streamlit app process

---

## ✅ What Was Kept (Safe)

- ✅ **S3 Bucket**: `cvc-rag-course-data` with 1,981 documents (costs <$0.01/month)
- ✅ **IAM Role**: `cvc-course-catalog-role` (free)
- ✅ **Git Repository**: https://github.com/kitkat357/cvc.git (all code backed up)
- ✅ **Local Files**: All source code in `/Users/rishikajain/claude/cvc-rag-chatbot/`

**Nothing is lost!** All your work can be restored in 20-30 minutes.

---

## 🚀 How to Resume the Project

### Quick Resume (20-30 minutes)

```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate

# Step 1: Recreate OpenSearch collection (~10 min)
python src/setup_opensearch.py

# Step 2: Create OpenSearch index (~1 min)
python src/create_opensearch_index.py

# Step 3: Recreate Knowledge Base (~5 min)
python src/setup_knowledge_base.py
# Copy the new Knowledge Base ID from output

# Step 4: Update .env file with new KB ID
# Edit .env and update KNOWLEDGE_BASE_ID=<new-id>

# Step 5: Start chatbot
streamlit run src/cvc_chatbot_rag.py --server.port 8502
```

**Total time**: 20-30 minutes  
**Total cost**: $0 (just your time)

---

## 💰 Cost Comparison

| State | Monthly Cost | Daily Cost |
|-------|-------------|------------|
| **Active** (with OpenSearch) | $90-180 | $3-6 |
| **Paused** (S3 only) | $0.01 | $0.0003 |
| **Deleted** (nothing) | $0 | $0 |

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
