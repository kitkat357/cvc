"""
Create Bedrock Knowledge Base and connect to S3 + OpenSearch.
"""

import boto3
import json
import time
import config

def create_knowledge_base():
    """Create Bedrock Knowledge Base for CVC courses."""

    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    bedrock_agent = session.client('bedrock-agent')
    sts_client = session.client('sts')
    iam_client = session.client('iam')

    kb_name = 'cvc-course-catalog'
    collection_name = 'cvc-courses'
    account_id = sts_client.get_caller_identity()['Account']

    print(f"=== Creating Bedrock Knowledge Base ===")
    print(f"Name: {kb_name}")
    print(f"Region: {config.AWS_REGION}")
    print(f"S3 Bucket: {config.S3_BUCKET_NAME}\n")

    # Step 1: Create IAM role for Knowledge Base
    print("Step 1: Creating IAM role for Knowledge Base...")

    role_name = f"{kb_name}-role"
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    try:
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Bedrock Knowledge Base to access S3 and OpenSearch'
        )
        role_arn = role_response['Role']['Arn']
        print(f"✓ IAM role created: {role_arn}")

        # Wait for role to propagate
        time.sleep(10)

    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"✓ IAM role already exists")
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    # Step 2: Attach policies to role
    print("\nStep 2: Attaching IAM policies...")

    # S3 policy
    s3_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{config.S3_BUCKET_NAME}",
                    f"arn:aws:s3:::{config.S3_BUCKET_NAME}/*"
                ]
            }
        ]
    }

    try:
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='S3Access',
            PolicyDocument=json.dumps(s3_policy)
        )
        print("✓ S3 access policy attached")
    except Exception as e:
        print(f"⚠️ Error attaching S3 policy: {e}")

    # Bedrock model invocation policy
    bedrock_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel"
                ],
                "Resource": [
                    f"arn:aws:bedrock:{config.AWS_REGION}::foundation-model/amazon.titan-embed-text-v1"
                ]
            }
        ]
    }

    try:
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='BedrockAccess',
            PolicyDocument=json.dumps(bedrock_policy)
        )
        print("✓ Bedrock model invocation policy attached")
    except Exception as e:
        print(f"⚠️ Error attaching Bedrock policy: {e}")

    # OpenSearch policy
    aoss_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "aoss:APIAccessAll"
                ],
                "Resource": [
                    f"arn:aws:aoss:{config.AWS_REGION}:{account_id}:collection/*"
                ]
            }
        ]
    }

    try:
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='OpenSearchAccess',
            PolicyDocument=json.dumps(aoss_policy)
        )
        print("✓ OpenSearch access policy attached")
    except Exception as e:
        print(f"⚠️ Error attaching OpenSearch policy: {e}")

    # Wait for policies to propagate
    time.sleep(10)

    # Step 3: Get OpenSearch collection ARN
    print("\nStep 3: Getting OpenSearch collection details...")
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
        print(f"  ARN: {collection_arn}")
        print(f"  Endpoint: {collection_endpoint}")

    except Exception as e:
        print(f"✗ Error getting OpenSearch collection: {e}")
        return

    # Step 4: Create Knowledge Base
    print("\nStep 4: Creating Knowledge Base...")

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

    except bedrock_agent.exceptions.ConflictException:
        print("✓ Knowledge Base already exists")

        # Get existing KB ID
        kbs = bedrock_agent.list_knowledge_bases()
        for kb in kbs['knowledgeBaseSummaries']:
            if kb['name'] == kb_name:
                kb_id = kb['knowledgeBaseId']
                print(f"  ID: {kb_id}")
                break

    except Exception as e:
        print(f"✗ Error creating Knowledge Base: {e}")
        return

    # Step 5: Create data source (S3)
    print("\nStep 5: Creating S3 data source...")

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
            }
        )

        ds_id = ds_response['dataSource']['dataSourceId']
        print(f"✓ Data source created")
        print(f"  ID: {ds_id}")

    except bedrock_agent.exceptions.ConflictException:
        print("✓ Data source already exists")

        # Get existing data source ID
        data_sources = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
        if data_sources['dataSourceSummaries']:
            ds_id = data_sources['dataSourceSummaries'][0]['dataSourceId']
            print(f"  ID: {ds_id}")

    except Exception as e:
        print(f"✗ Error creating data source: {e}")
        ds_id = None

    # Step 6: Start ingestion job
    if ds_id:
        print("\nStep 6: Starting data ingestion...")

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
    print("✓ Knowledge Base setup complete!")
    print("="*60)
    print(f"\nKnowledge Base ID: {kb_id}")
    print(f"\n📋 IMPORTANT: Copy this to your .env file:")
    print(f"   KNOWLEDGE_BASE_ID={kb_id}")
    print(f"\nNext steps:")
    print(f"1. Copy the Knowledge Base ID above to .env file")
    print(f"2. Wait for ingestion job to complete (2-5 minutes)")
    print(f"3. Run: streamlit run src/cvc_chatbot_rag.py")
    print(f"4. Test queries!")


if __name__ == "__main__":
    create_knowledge_base()
