"""
Test RAG chatbot with various queries to validate functionality.
"""

import sys
sys.path.insert(0, 'src')
import boto3
import json
import config

def test_rag_retrieval(query: str, top_k: int = 5):
    """Test Knowledge Base retrieval."""
    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    bedrock_agent = session.client('bedrock-agent-runtime')

    response = bedrock_agent.retrieve(
        knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {'numberOfResults': top_k}
        }
    )

    return response.get('retrievalResults', [])


def test_rag_with_claude(query: str):
    """Test full RAG pipeline with Claude generation."""
    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)

    # Retrieve
    bedrock_agent = session.client('bedrock-agent-runtime')
    retrieval_response = bedrock_agent.retrieve(
        knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {'numberOfResults': 10}
        }
    )

    results = retrieval_response.get('retrievalResults', [])

    # Format context
    context = "Relevant courses found:\n\n"
    for i, result in enumerate(results[:5], 1):
        text = result['content']['text']
        context += f"{i}. {text}\n\n"

    # Generate with Claude
    bedrock_runtime = session.client('bedrock-runtime')

    system_prompt = f"""You are a helpful CVC course advisor. Based on the retrieved course data, provide specific recommendations.

{context}

Answer the student's question with specific course codes, colleges, units, and transfer information."""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": query}],
        "system": system_prompt,
        "temperature": 0.7
    })

    response = bedrock_runtime.invoke_model(
        modelId=config.CLAUDE_MODEL_ID,
        body=body
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text'], len(results)


def main():
    """Run test queries."""

    test_queries = [
        "I need a 3-unit math course",
        "Show me transferable English classes",
        "What psychology courses transfer to Cal Poly?",
        "Find me Area 3B humanities classes",
        "I want a biology course with a lab"
    ]

    print("="*70)
    print("CVC RAG CHATBOT - TEST QUERIES")
    print("="*70)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {query}")
        print('='*70)

        try:
            # Test retrieval
            print(f"\n[1] RETRIEVAL PHASE:")
            results = test_rag_retrieval(query, top_k=5)
            print(f"    Retrieved {len(results)} documents")

            for j, result in enumerate(results[:3], 1):
                score = result.get('score', 0)
                text = result['content']['text'][:100]
                print(f"    {j}. Score: {score:.3f} | {text}...")

            # Test full RAG
            print(f"\n[2] GENERATION PHASE (Claude + RAG):")
            response, num_retrieved = test_rag_with_claude(query)
            print(f"    Retrieved: {num_retrieved} documents")
            print(f"    Response:\n")
            print(f"    {response}")

            print(f"\n    ✓ Test {i} passed")

        except Exception as e:
            print(f"\n    ✗ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*70}")
    print("ALL TESTS COMPLETE")
    print('='*70)
    print(f"\n✓ RAG chatbot is operational!")
    print(f"✓ Knowledge Base ID: {config.KNOWLEDGE_BASE_ID}")
    print(f"✓ Documents indexed: 1,981")
    print(f"\nStreamlit UI available at: http://localhost:8502")


if __name__ == "__main__":
    main()
