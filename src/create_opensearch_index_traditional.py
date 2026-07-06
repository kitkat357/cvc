"""
Create vector index in traditional OpenSearch domain.
"""

import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
import config

def create_index():
    """Create vector search index in traditional OpenSearch domain."""

    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    opensearch = session.client('opensearch')
    credentials = session.get_credentials()

    domain_name = 'cvc-courses'
    index_name = 'cvc-courses-index'

    print(f"=== Creating OpenSearch Index (Traditional) ===")
    print(f"Domain: {domain_name}")
    print(f"Index: {index_name}\n")

    # Step 1: Get domain endpoint
    print("Step 1: Getting domain endpoint...")
    try:
        status = opensearch.describe_domain(DomainName=domain_name)
        endpoint = status['DomainStatus']['Endpoint']
        print(f"✓ Endpoint: https://{endpoint}")
    except Exception as e:
        print(f"✗ Error getting domain: {e}")
        print("   Make sure the domain is created and active")
        return

    # Step 2: Set up AWS authentication
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        config.AWS_REGION,
        'es',
        session_token=credentials.token
    )

    # Step 3: Create index with vector mapping
    print("\nStep 2: Creating index with vector mapping...")

    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": 1536,
                    "method": {
                        "name": "hnsw",
                        "space_type": "l2",
                        "engine": "faiss",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "text": {
                    "type": "text"
                },
                "metadata": {
                    "type": "object",
                    "enabled": True
                }
            }
        }
    }

    url = f"https://{endpoint}/{index_name}"

    try:
        response = requests.put(
            url,
            auth=awsauth,
            json=index_body,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            print(f"✓ Index created successfully!")
            print(f"  Name: {index_name}")
            print(f"  Vector dimension: 1536")
            print(f"  Algorithm: HNSW (Faiss)")
        else:
            print(f"✗ Error creating index: {response.status_code}")
            print(f"  Response: {response.text}")
            return

    except Exception as e:
        print(f"✗ Error: {e}")
        return

    # Step 4: Verify index
    print("\nStep 3: Verifying index...")

    try:
        verify_url = f"https://{endpoint}/{index_name}/_settings"
        verify_response = requests.get(verify_url, auth=awsauth)

        if verify_response.status_code == 200:
            print(f"✓ Index verified!")
            settings = verify_response.json()
            print(f"  Settings: {json.dumps(settings[index_name]['settings']['index'], indent=2)}")
        else:
            print(f"⚠️ Could not verify index")

    except Exception as e:
        print(f"⚠️ Verification error: {e}")

    print("\n" + "="*60)
    print("✓ OpenSearch index setup complete!")
    print("="*60)
    print(f"\nNext step: Run setup_knowledge_base_traditional.py")


if __name__ == "__main__":
    create_index()
