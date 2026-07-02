"""
Create OpenSearch Serverless collection for vector search.
"""

import boto3
import json
import time
import config

def create_opensearch_collection():
    """Create OpenSearch Serverless collection for CVC courses."""

    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    aoss_client = session.client('opensearchserverless')

    collection_name = 'cvc-courses'

    print(f"=== Creating OpenSearch Serverless Collection ===")
    print(f"Collection Name: {collection_name}")
    print(f"Region: {config.AWS_REGION}")
    print(f"Type: VECTORSEARCH\n")

    # Step 1: Create encryption policy
    print("Step 1: Creating encryption policy...")
    encryption_policy = {
        "Rules": [
            {
                "ResourceType": "collection",
                "Resource": [f"collection/{collection_name}"]
            }
        ],
        "AWSOwnedKey": True
    }

    try:
        aoss_client.create_security_policy(
            name=f"{collection_name}-encryption",
            type='encryption',
            policy=json.dumps(encryption_policy)
        )
        print("✓ Encryption policy created")
    except aoss_client.exceptions.ConflictException:
        print("✓ Encryption policy already exists")
    except Exception as e:
        print(f"✗ Error creating encryption policy: {e}")
        return

    # Step 2: Create network policy (public access for now)
    print("\nStep 2: Creating network policy (public access)...")
    network_policy = [
        {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"]
                },
                {
                    "ResourceType": "dashboard",
                    "Resource": [f"collection/{collection_name}"]
                }
            ],
            "AllowFromPublic": True
        }
    ]

    try:
        aoss_client.create_security_policy(
            name=f"{collection_name}-network",
            type='network',
            policy=json.dumps(network_policy)
        )
        print("✓ Network policy created (public access)")
    except aoss_client.exceptions.ConflictException:
        print("✓ Network policy already exists")
    except Exception as e:
        print(f"✗ Error creating network policy: {e}")
        return

    # Step 3: Create collection
    print("\nStep 3: Creating collection...")
    try:
        response = aoss_client.create_collection(
            name=collection_name,
            type='VECTORSEARCH',
            description='Vector search collection for CVC course catalog'
        )

        collection_id = response['createCollectionDetail']['id']
        collection_arn = response['createCollectionDetail']['arn']

        print(f"✓ Collection created!")
        print(f"  ID: {collection_id}")
        print(f"  ARN: {collection_arn}")

        # Wait for collection to be active
        print("\nWaiting for collection to become active (this may take 2-3 minutes)...")

        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(10)

            status_response = aoss_client.batch_get_collection(
                ids=[collection_id]
            )

            if status_response['collectionDetails']:
                status = status_response['collectionDetails'][0]['status']
                print(f"  Status: {status} (attempt {attempt + 1}/{max_attempts})")

                if status == 'ACTIVE':
                    endpoint = status_response['collectionDetails'][0]['collectionEndpoint']
                    print(f"\n✓ Collection is ACTIVE!")
                    print(f"  Endpoint: {endpoint}")
                    break

            if attempt == max_attempts - 1:
                print("\n⚠️ Collection taking longer than expected. Check AWS Console.")
                return

    except aoss_client.exceptions.ConflictException:
        print("✓ Collection already exists")

        # Get existing collection details
        collections = aoss_client.list_collections(
            collectionFilters={'name': collection_name}
        )

        if collections['collectionSummaries']:
            collection_id = collections['collectionSummaries'][0]['id']

            details = aoss_client.batch_get_collection(ids=[collection_id])
            if details['collectionDetails']:
                collection = details['collectionDetails'][0]
                print(f"  Status: {collection['status']}")
                print(f"  Endpoint: {collection.get('collectionEndpoint', 'N/A')}")

    except Exception as e:
        print(f"✗ Error creating collection: {e}")
        return

    # Step 4: Create data access policy for Bedrock
    print("\nStep 4: Creating data access policy for Bedrock...")

    # Get AWS account ID
    sts_client = session.client('sts')
    account_id = sts_client.get_caller_identity()['Account']

    data_policy = [
        {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems"
                    ]
                },
                {
                    "ResourceType": "index",
                    "Resource": [f"index/{collection_name}/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument",
                        "aoss:UpdateIndex",
                        "aoss:DeleteIndex"
                    ]
                }
            ],
            "Principal": [
                f"arn:aws:iam::{account_id}:role/aws-service-role/bedrock.amazonaws.com/AWSServiceRoleForAmazonBedrock"
            ]
        }
    ]

    try:
        aoss_client.create_access_policy(
            name=f"{collection_name}-bedrock-access",
            type='data',
            policy=json.dumps(data_policy)
        )
        print("✓ Data access policy created for Bedrock")
    except aoss_client.exceptions.ConflictException:
        print("✓ Data access policy already exists")
    except Exception as e:
        print(f"⚠️ Error creating data access policy: {e}")
        print("   You may need to create this manually in the AWS Console")

    print("\n" + "="*60)
    print("✓ OpenSearch Serverless setup complete!")
    print("="*60)
    print(f"\nCollection Name: {collection_name}")
    print(f"Collection ID: {collection_id if 'collection_id' in locals() else 'See AWS Console'}")
    print(f"\nNext steps:")
    print(f"1. Go to AWS Console → Bedrock → Knowledge Bases")
    print(f"2. Create Knowledge Base with:")
    print(f"   - Data source: S3 (s3://cvc-rag-course-data/)")
    print(f"   - Embeddings: Titan Embeddings G1")
    print(f"   - Vector store: OpenSearch Serverless")
    print(f"   - Collection: {collection_name}")
    print(f"3. Copy the Knowledge Base ID to your .env file")
    print(f"4. Sync the data source")


if __name__ == "__main__":
    create_opensearch_collection()
