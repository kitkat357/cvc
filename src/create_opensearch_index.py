"""
Create OpenSearch index for vector search.
"""

import boto3
import requests
from requests_aws4auth import AWS4Auth
import json
import config

def create_index():
    """Create OpenSearch Serverless index with vector field mapping."""

    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)

    # Get AWS credentials for signing requests
    credentials = session.get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        config.AWS_REGION,
        'aoss',  # OpenSearch Serverless service name
        session_token=credentials.token
    )

    # Get collection endpoint
    aoss_client = session.client('opensearchserverless')
    collections = aoss_client.list_collections(
        collectionFilters={'name': 'cvc-courses'}
    )

    if not collections['collectionSummaries']:
        print("✗ Collection 'cvc-courses' not found!")
        return

    collection_id = collections['collectionSummaries'][0]['id']
    details = aoss_client.batch_get_collection(ids=[collection_id])
    endpoint = details['collectionDetails'][0]['collectionEndpoint']

    print(f"=== Creating OpenSearch Index ===")
    print(f"Endpoint: {endpoint}")
    print(f"Index: cvc-courses-index\n")

    # Index settings and mappings for vector search
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
                    "dimension": 1536,  # Titan Embeddings G1 dimension
                    "method": {
                        "name": "hnsw",
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

    # Create index
    url = f"{endpoint}/cvc-courses-index"

    try:
        response = requests.put(
            url,
            auth=awsauth,
            json=index_body,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            print("✓ Index created successfully!")
            print(f"  Name: cvc-courses-index")
            print(f"  Vector dimension: 1536")
            print(f"  Algorithm: HNSW (Faiss)")
        elif response.status_code == 400 and 'resource_already_exists' in response.text:
            print("✓ Index already exists")
        else:
            print(f"✗ Error creating index:")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return

    except Exception as e:
        print(f"✗ Error: {e}")
        return

    # Verify index was created
    try:
        verify_response = requests.get(
            url,
            auth=awsauth
        )

        if verify_response.status_code == 200:
            print("\n✓ Index verified!")
            index_info = verify_response.json()
            print(f"  Settings: {json.dumps(index_info.get('cvc-courses-index', {}).get('settings', {}), indent=2)}")

    except Exception as e:
        print(f"⚠️ Could not verify index: {e}")

    print("\n" + "="*60)
    print("✓ OpenSearch index setup complete!")
    print("="*60)
    print(f"\nNext step: Run setup_knowledge_base.py")


if __name__ == "__main__":
    # Check if requests_aws4auth is installed
    try:
        import requests_aws4auth
    except ImportError:
        print("Installing requests-aws4auth...")
        import subprocess
        subprocess.check_call(['.venv/bin/pip', 'install', 'requests-aws4auth'])
        print("✓ Installed requests-aws4auth")

    create_index()
