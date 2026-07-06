# Custom RAG Pipeline Summary

## ✅ What We Built (2026-07-06)

Successfully migrated from expensive Bedrock Knowledge Bases to a **custom RAG pipeline** with full control and 60-75% cost savings!

---

## 🏗️ Architecture

### Custom RAG Pipeline Components

1. **`src/custom_rag.py`** - Core RAG implementation
   - Direct Bedrock Titan Embeddings API calls
   - OpenSearch vector search with KNN
   - Claude Haiku 4.5 for response generation
   - No Bedrock Knowledge Base dependency

2. **`src/upload_to_opensearch.py`** - Data ingestion pipeline
   - Processes course catalogs and transfer agreements
   - Generates embeddings via Bedrock Titan
   - Bulk uploads to OpenSearch with metadata
   - **Result**: 1,981 documents successfully indexed

3. **`src/cvc_chatbot_custom_rag.py`** - Streamlit chatbot UI
   - Uses custom RAG pipeline instead of KB API
   - Shows source documents with relevance scores
   - Full conversation context support
   - CVC-branded interface

4. **`src/setup_opensearch_traditional.py`** - Infrastructure setup
   - Creates traditional OpenSearch domain
   - t3.small.search instance (cost-optimized)
   - ~15 minutes to provision

5. **`src/create_opensearch_index_traditional.py`** - Index creation
   - 1536-dimension vector index
   - HNSW algorithm with Faiss
   - Optimized for semantic search

---

## 💰 Cost Comparison

| Architecture | Monthly Cost | Status |
|--------------|-------------|--------|
| **OpenSearch Serverless + Bedrock KB** | $90-180/month | ❌ Old approach |
| **Traditional OpenSearch + Custom RAG** | $20-40/month | ✅ Current (60-75% savings!) |
| **Paused (S3 only)** | $0.01/month | ✅ Right now |

### Cost Breakdown (When Active)

**Traditional OpenSearch Domain:**
- t3.small.search instance: $0.036/hour × 730 hours = ~$26/month
- 10GB gp3 storage: ~$1/month
- **Subtotal**: ~$27/month

**Bedrock Usage (pay-per-use):**
- Claude Haiku: ~$0.25/1M input tokens, ~$1.25/1M output tokens
- Titan Embeddings: ~$0.10/1M tokens
- Typical usage: <$5/month for testing

**Total Active Cost**: ~$20-40/month

---

## 📊 Data Processed

Successfully uploaded **1,981 documents** with embeddings:

### Course Catalogs (91 courses)
- Cerritos College: 37 courses (2019-2025)
- Mount San Antonio College: 15 courses (2024-2025)
- Victor Valley College: 39 courses (2024-2025)

### Transfer Agreements (1,890 mappings)
- Victor Valley → Cal State Fullerton: 474 transfers
- Victor Valley → Cal Poly SLO: 709 transfers
- Cuesta → Cal Poly SLO: 709 transfers

---

## 🚀 How to Resume

### Quick Start (30-40 minutes)

```bash
cd /Users/rishikajain/claude/cvc-rag-chatbot
source .venv/bin/activate

# Step 1: Create OpenSearch domain (~15 min)
python src/setup_opensearch_traditional.py

# Step 2: Create vector index (~1 min)
python src/create_opensearch_index_traditional.py

# Step 3: Upload data with embeddings (~10 min)
python src/upload_to_opensearch.py

# Step 4: Start chatbot
streamlit run src/cvc_chatbot_custom_rag.py --server.port 8502
```

**Note**: Data upload is already done! Steps 1-2 recreate infrastructure, step 3 re-uploads the 1,981 documents.

---

## 🎯 Key Advantages of Custom RAG

### 1. **Full Control**
- You own the entire pipeline
- No black-box Bedrock Knowledge Base
- Debug and customize every step

### 2. **Cost Savings**
- 60-75% cheaper than Serverless
- Traditional OpenSearch scales down when idle
- Pay-per-use Bedrock APIs only

### 3. **Flexibility**
- Easy to modify search logic
- Custom ranking and filtering
- Add new features (e.g., hybrid search, reranking)

### 4. **Learning Opportunity**
- Understand how RAG works under the hood
- Portfolio-worthy implementation
- Foundation for future enhancements

---

## 📁 Key Files Created

### Core Implementation
- `src/custom_rag.py` - Main RAG pipeline class
- `src/upload_to_opensearch.py` - Data ingestion
- `src/cvc_chatbot_custom_rag.py` - Streamlit UI

### Infrastructure Setup
- `src/setup_opensearch_traditional.py` - Domain creation
- `src/create_opensearch_index_traditional.py` - Index setup
- `src/check_status.py` - Resource status checker

### Documentation
- `PAUSE_RESUME.md` - Updated with custom RAG instructions
- `CUSTOM_RAG_SUMMARY.md` - This file!

---

## 🔧 Technical Details

### Vector Search Configuration
- **Embedding Model**: AWS Bedrock Titan Text Embeddings G1
- **Vector Dimensions**: 1536
- **Algorithm**: HNSW (Hierarchical Navigable Small World)
- **Engine**: Faiss
- **Distance Metric**: L2 (Euclidean)

### RAG Pipeline Flow
1. **User Query** → Embed with Titan (1536-dim vector)
2. **Vector Search** → OpenSearch KNN retrieval (top-k results)
3. **Context Building** → Format documents with metadata
4. **LLM Generation** → Claude Haiku with retrieved context
5. **Response** → Display with source citations

### Performance
- **Query Latency**: ~1-2 seconds (embed + search + generate)
- **Batch Upload**: 50 docs/batch with 0.5s delay (rate limiting)
- **Index Size**: 1,981 documents × 1536 dimensions

---

## 🎓 Next Steps

### Immediate (Testing)
1. Resume services (30 min setup)
2. Test chatbot with various queries
3. Verify search quality and relevance

### Short-term Enhancements
1. Add hybrid search (keyword + semantic)
2. Implement reranking for better results
3. Add filters (college, units, GE area)
4. Cache embeddings for common queries

### Long-term (Production)
1. Scale to all 116 CA community colleges
2. Deploy to AWS (Lambda + API Gateway)
3. Add user authentication
4. Integrate with CVC platform
5. Analytics and monitoring

---

## 💡 Cost Management Tips

### When to Pause
- Not actively testing/demoing
- Between development sessions
- Waiting for stakeholder feedback

### When to Resume
- Demo to stakeholders
- Active development/testing
- User acceptance testing
- Production deployment

### How to Pause
```bash
# Delete OpenSearch domain (keeps S3 data)
aws opensearch delete-domain \
  --domain-name cvc-courses \
  --profile cvc-project \
  --region us-west-2
```

**Result**: Costs drop to ~$0.01/month (S3 only)

---

## ✅ Current Status

**Infrastructure**: 
- ✅ OpenSearch domain: DELETED (paused)
- ✅ S3 bucket: Active (1,000 files preserved)
- ✅ Data processing scripts: Ready
- ✅ Chatbot code: Ready
- ✅ All embeddings: Can be regenerated in ~10 minutes

**Cost**: ~$0.01/month (essentially free)

**Ready to Resume**: Yes! Just run the 4 commands above.

---

## 📞 Support

For questions or issues:
1. Check `PAUSE_RESUME.md` for resume instructions
2. Review `CLAUDE.md` for project architecture
3. Run `python src/check_status.py` to diagnose
4. Logs in terminal when running scripts

---

**Built**: 2026-07-06  
**Status**: Paused but ready to resume  
**Achievement**: 60-75% cost reduction with full control! 🎉
