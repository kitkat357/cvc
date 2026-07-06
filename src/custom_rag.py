"""
Custom RAG pipeline using traditional OpenSearch and Bedrock APIs directly.
No Bedrock Knowledge Base required - full control, lower cost.
"""

import boto3
import json
from typing import List, Dict, Any
import config


class CustomRAG:
    """Custom RAG implementation with traditional OpenSearch."""

    def __init__(self):
        """Initialize clients for Bedrock and OpenSearch."""
        session = boto3.Session(
            profile_name=config.AWS_PROFILE,
            region_name=config.AWS_REGION
        )

        self.bedrock_runtime = session.client('bedrock-runtime')
        self.opensearch = session.client('opensearch')

        # Get OpenSearch endpoint
        domain_status = self.opensearch.describe_domain(DomainName='cvc-courses')
        self.opensearch_endpoint = f"https://{domain_status['DomainStatus']['Endpoint']}"

        # Set up OpenSearch HTTP client with AWS auth
        from requests_aws4auth import AWS4Auth
        import requests

        credentials = session.get_credentials()
        self.awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            config.AWS_REGION,
            'es',
            session_token=credentials.token
        )
        self.requests = requests

        self.index_name = 'cvc-courses-index'

    def embed_text(self, text: str) -> List[float]:
        """
        Embed text using Bedrock Titan Embeddings.

        Args:
            text: Text to embed

        Returns:
            1536-dimension embedding vector
        """
        body = json.dumps({
            "inputText": text
        })

        response = self.bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=body
        )

        result = json.loads(response['body'].read())
        return result['embedding']

    def search_similar(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar documents in OpenSearch.

        Args:
            query: User's search query
            top_k: Number of results to return

        Returns:
            List of matching documents with metadata
        """
        # Embed the query
        query_vector = self.embed_text(query)

        # Build OpenSearch KNN query
        search_body = {
            "size": top_k,
            "query": {
                "knn": {
                    "vector": {
                        "vector": query_vector,
                        "k": top_k
                    }
                }
            },
            "_source": ["text", "metadata"]
        }

        # Execute search
        url = f"{self.opensearch_endpoint}/{self.index_name}/_search"
        response = self.requests.post(
            url,
            auth=self.awsauth,
            json=search_body,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            raise Exception(f"OpenSearch query failed: {response.text}")

        results = response.json()

        # Format results
        documents = []
        for hit in results['hits']['hits']:
            documents.append({
                'text': hit['_source']['text'],
                'metadata': hit['_source']['metadata'],
                'score': hit['_score']
            })

        return documents

    def generate_response(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None,
        language: str = 'en'
    ) -> str:
        """
        Generate response using Claude with retrieved context.

        Args:
            query: User's question
            context_docs: Retrieved documents from search
            conversation_history: Previous conversation turns

        Returns:
            Claude's response
        """
        # Build context from retrieved documents
        context_text = self._format_context(context_docs)

        # Language instruction
        language_instructions = {
            'en': 'Respond in English.',
            'es': 'Respond in Spanish (Español). Translate all your responses to Spanish, but keep course codes and technical terms in English.',
            'zh': 'Respond in Simplified Chinese (简体中文). Translate all your responses to Chinese, but keep course codes and technical terms in English.'
        }

        language_instruction = language_instructions.get(language, language_instructions['en'])

        # Build system prompt with context
        system_prompt = f"""You are a friendly and helpful GE advisor for California community college students transferring to Cal Poly and other universities.

**IMPORTANT: {language_instruction}**

**Your Role:**
- Interview students about their GE needs in a conversational way
- Explain GE terminology and systems clearly
- Help them find the right courses
- Guide them through the transfer process

**GE Systems to Know:**

**IGETC (Intersegmental General Education Transfer Curriculum):**
- Area 1A: English Composition
- Area 1B: Critical Thinking & Composition
- Area 1C: Oral Communication
- Area 2: Mathematical Concepts & Quantitative Reasoning
- Area 3A: Arts
- Area 3B: Humanities
- Area 4: Social & Behavioral Sciences
- Area 5A: Physical Sciences
- Area 5B: Biological Sciences
- Area 5C: Science Laboratory
- Area 6: Language Other Than English

**Cal-GETC (California General Education Transfer Curriculum - Fall 2025+):**
- Area 1A: English Composition
- Area 1B: Critical Thinking & Composition
- Area 1C: Oral Communication
- Area 2: Mathematical Concepts
- Area 3: Arts & Humanities
- Area 4: Social & Behavioral Sciences
- Area 5: Physical & Biological Sciences (with lab)
- Area 6: Ethnic Studies
- Area 7: Language Other Than English

**How to Help Students:**
1. When they ask about GE courses, ask which area they need
2. If they're unsure, explain what each area covers
3. Use the course data below to show specific options
4. Be conversational - interview them to understand their needs

**Available Course & Transfer Data:**

{context_text}

**Guidelines:**
- Be warm and conversational
- Ask clarifying questions
- Explain any terms they might not know
- Cite specific course codes and colleges
- Show transfer information when relevant
- If you don't have the exact course they need, suggest alternatives"""

        # Build messages
        messages = []

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current query
        messages.append({
            "role": "user",
            "content": query
        })

        # Call Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.7,
            "system": system_prompt,
            "messages": messages
        }

        response = self.bedrock_runtime.invoke_model(
            modelId='us.anthropic.claude-haiku-4-5-20251001-v1:0',
            body=json.dumps(request_body)
        )

        result = json.loads(response['body'].read())
        return result['content'][0]['text']

    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context string."""
        context_parts = []

        for i, doc in enumerate(documents, 1):
            metadata = doc['metadata']
            text = doc['text']

            # Format based on source type
            if metadata.get('source_type') == 'catalog':
                context_parts.append(
                    f"Course {i}: {metadata.get('course_code', 'N/A')} - "
                    f"{metadata.get('title', 'N/A')} at {metadata.get('college', 'N/A')}\n"
                    f"{text}\n"
                )
            elif metadata.get('source_type') == 'transfer':
                context_parts.append(
                    f"Transfer Info {i}: {metadata.get('from_course', 'N/A')} from "
                    f"{metadata.get('from_college', 'N/A')} to {metadata.get('to_college', 'N/A')}\n"
                    f"{text}\n"
                )
            else:
                context_parts.append(f"Document {i}:\n{text}\n")

        return "\n---\n".join(context_parts)

    def query(
        self,
        user_query: str,
        top_k: int = 10,
        conversation_history: List[Dict[str, str]] = None,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve + generate.

        Args:
            user_query: User's question
            top_k: Number of documents to retrieve
            conversation_history: Previous conversation turns

        Returns:
            Dict with 'response' and 'sources' (retrieved docs)
        """
        # Step 1: Retrieve relevant documents
        documents = self.search_similar(user_query, top_k=top_k)

        # Step 2: Generate response with context
        response = self.generate_response(
            user_query,
            documents,
            conversation_history,
            language
        )

        return {
            'response': response,
            'sources': documents,
            'num_sources': len(documents)
        }


def test_custom_rag():
    """Quick test of the custom RAG pipeline."""
    print("Testing Custom RAG Pipeline...")

    rag = CustomRAG()

    # Test query
    result = rag.query("I need a math course that transfers to Cal Poly", top_k=5)

    print(f"\nResponse: {result['response']}")
    print(f"\nRetrieved {result['num_sources']} sources")
    print("\nTop 3 sources:")
    for i, doc in enumerate(result['sources'][:3], 1):
        print(f"\n{i}. Score: {doc['score']:.3f}")
        print(f"   {doc['text'][:150]}...")


if __name__ == "__main__":
    test_custom_rag()
