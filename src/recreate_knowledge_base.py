"""
Completely delete old Knowledge Base and create a new one with the new OpenSearch collection.
"""

import boto3
import json
import time
import config

def recreate_knowledge_base():
    """Delete old KB and create fresh one."""

    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    bedrock_agent = session.client('bedrock-agent')
    sts_client = session.client('sts')
    iam_client = session.client('iam')

    kb_name = 'cvc-course-catalog'
    collection_name = 'cvc-courses'
    account_id = sts_client.get_caller_identity()['Account']

    print(f"=== Recreating Bedrock Knowledge Base ===")
    print(f"Name: {kb_name}")
    print(f"Region: {config.AWS_REGION}\n")

    # Step 1: Find and delete old Knowledge Base
    print("Step 1: Looking for existing Knowledge Bases...")

    try:
        kbs = bedrock_agent.list_knowledge_bases()
        old_kb_id = None

        for kb in kbs['knowledgeBaseSummaries']:
            if kb['name'] == kb_name:
                old_kb_id = kb['knowledgeBaseId']
                print(f"✓ Found existing KB: {old_kb_id}")
                print(f"  Status: {kb.get('status', 'UNKNOWN')}")

                # Delete it
                print("  Deleting old Knowledge Base...")
                try:
                    bedrock_agent.delete_knowledge_base(knowledgeBaseId=old_kb_id)
                    print("  ✓ Deletion initiated")

                    # Wait for deletion
                    print("  Waiting for deletion to complete (30 seconds)...")
                    time.sleep(30)

                except Exception as e:
                    print(f"  ⚠️ Error deleting: {e}")
                    print("  Continuing anyway...")

                break

        if not old_kb_id:
            print("✓ No existing Knowledge Base found")

    except Exception as e:
        print(f"⚠️ Error listing KBs: {e}")

    # Step 2: Get IAM role
    print("\nStep 2: Setting up IAM role...")
    role_name = f"{kb_name}-role"
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    print(f"✓ Using role: {role_arn}")

    # Step 3: Get new OpenSearch collection
    print("\nStep 3: Getting new OpenSearch collection...")
    aoss_client = session.client('opensearchserverless')

    try:
        collections = aoss_client.list_collections(
            collectionFilters={'name': collection_name}
        )

        if not collections['collectionSummaries']:
            print(f"✗ OpenSearch collection '{collection_name}' not found!")
            print("   Please run setup_opensearch.py first")
            return

        collection_arn = collections['collectionSummaries'][0]['arn']
        collection_id = collections['collectionSummaries'][0]['id']

        # Get collection endpoint
        details = aoss_client.batch_get_collection(ids=[collection_id])
        collection_endpoint = details['collectionDetails'][0]['collectionEndpoint']

        print(f"✓ Found OpenSearch collection")
        print(f"  ID: {collection_id}")
        print(f"  ARN: {collection_arn}")
        print(f"  Endpoint: {collection_endpoint}")

    except Exception as e:
        print(f"✗ Error getting OpenSearch collection: {e}")
        return

    # Step 4: Wait a bit more to ensure old KB is fully deleted
    print("\nStep 4: Waiting for AWS to fully clean up old resources...")
    time.sleep(30)

    # Step 5: Create new Knowledge Base
    print("\nStep 5: Creating new Knowledge Base...")

    storage_config = {
        'type': 'OPENSEARCH_SERVERLESS',
        'opensearchServerlessConfiguration': {
            'collectionArn': collection_arn,
            'vectorIndexName': 'cvc-courses-index',
            'fieldMapping': {
                'vectorField': 'vector',
                'textField': 'text',
                'metadataField': 'metadata'
            }
        }
    }

    try:
        kb_response = bedrock_agent.create_knowledge_base(
            name=kb_name,
            description='Course catalog and transfer data for California Virtual Campus',
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{config.AWS_REGION}::foundation-model/amazon.titan-embed-text-v1'
                }
            },
            storageConfiguration=storage_config
        )

        kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
        kb_arn = kb_response['knowledgeBase']['knowledgeBaseArn']

        print(f"✓ Knowledge Base created!")
        print(f"  ID: {kb_id}")
        print(f"  ARN: {kb_arn}")

    except Exception as e:
        print(f"✗ Error creating Knowledge Base: {e}")
        print("\nTry waiting a few more seconds and running this script again.")
        return

    # Step 6: Create data source (S3)
    print("\nStep 6: Creating S3 data source...")

    try:
        ds_response = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=f'{kb_name}-s3-source',
            description='S3 bucket containing course catalogs and transfer data',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{config.S3_BUCKET_NAME}'
                }
            },
            dataDeletionPolicy='RETAIN'
        )

        ds_id = ds_response['dataSource']['dataSourceId']
        print(f"✓ Data source created")
        print(f"  ID: {ds_id}")

    except Exception as e:
        print(f"✗ Error creating data source: {e}")
        ds_id = None

    # Step 7: Start ingestion job
    if ds_id:
        print("\nStep 7: Starting data ingestion...")

        try:
            ingestion_response = bedrock_agent.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                description='Initial data sync for CVC course catalog'
            )

            job_id = ingestion_response['ingestionJob']['ingestionJobId']
            print(f"✓ Ingestion job started")
            print(f"  Job ID: {job_id}")
            print(f"  Status: {ingestion_response['ingestionJob']['status']}")

            print("\n  Ingestion will take 2-5 minutes. Monitor in AWS Console:")
            print(f"  Bedrock → Knowledge Bases → {kb_name} → Data source")

        except Exception as e:
            print(f"⚠️ Error starting ingestion: {e}")
            print("   You can manually sync in the AWS Console")

    print("\n" + "="*60)
    print("✓ Knowledge Base recreation complete!")
    print("="*60)
    print(f"\nKnowledge Base ID: {kb_id}")
    print(f"\n📋 IMPORTANT: Update your .env file:")
    print(f"   KNOWLEDGE_BASE_ID={kb_id}")
    print(f"\nNext steps:")
    print(f"1. Update KNOWLEDGE_BASE_ID in .env file")
    print(f"2. Wait for ingestion job to complete (2-5 minutes)")
    print(f"3. Run: streamlit run src/cvc_chatbot_rag.py")


if __name__ == "__main__":
    recreate_knowledge_base()
