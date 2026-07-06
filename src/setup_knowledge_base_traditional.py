"""
Create Bedrock Knowledge Base connected to traditional OpenSearch domain.
"""

import boto3
import json
import time
import config

def create_knowledge_base():
    """Create Bedrock Knowledge Base for traditional OpenSearch."""

    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    bedrock_agent = session.client('bedrock-agent')
    opensearch = session.client('opensearch')
    sts_client = session.client('sts')

    kb_name = 'cvc-course-catalog-v2'
    domain_name = 'cvc-courses'
    account_id = sts_client.get_caller_identity()['Account']

    print(f"=== Creating Bedrock Knowledge Base (Traditional OpenSearch) ===")
    print(f"KB Name: {kb_name}")
    print(f"OpenSearch Domain: {domain_name}")
    print(f"Region: {config.AWS_REGION}\n")

    # Step 1: Get OpenSearch domain endpoint
    print("Step 1: Getting OpenSearch domain details...")

    try:
        domain_status = opensearch.describe_domain(DomainName=domain_name)
        domain_endpoint = domain_status['DomainStatus']['Endpoint']
        domain_arn = domain_status['DomainStatus']['ARN']

        print(f"✓ Found OpenSearch domain")
        print(f"  ARN: {domain_arn}")
        print(f"  Endpoint: https://{domain_endpoint}")

    except Exception as e:
        print(f"✗ Error getting OpenSearch domain: {e}")
        return

    # Step 2: Get IAM role
    print("\nStep 2: Using existing IAM role...")
    role_name = 'cvc-course-catalog-role'
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    print(f"✓ Role ARN: {role_arn}")

    # Step 3: Create Knowledge Base
    print("\nStep 3: Creating Knowledge Base...")

    storage_config = {
        'type': 'OPENSEARCH_SERVERLESS',
        'opensearchServerlessConfiguration': {
            'collectionArn': domain_arn,
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
            description='CVC course catalog with traditional OpenSearch (cost-optimized)',
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
        kb_id = None
        for kb in kbs['knowledgeBaseSummaries']:
            if kb['name'] == kb_name:
                kb_id = kb['knowledgeBaseId']
                print(f"  ID: {kb_id}")
                break

        if not kb_id:
            print("✗ Could not find existing KB")
            return

    except Exception as e:
        print(f"✗ Error creating Knowledge Base: {e}")
        return

    # Step 4: Create data source (S3)
    print("\nStep 4: Creating S3 data source...")

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

    except bedrock_agent.exceptions.ConflictException:
        print("✓ Data source already exists")

        # Get existing data source ID
        data_sources = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
        if data_sources['dataSourceSummaries']:
            ds_id = data_sources['dataSourceSummaries'][0]['dataSourceId']
            print(f"  ID: {ds_id}")
        else:
            ds_id = None

    except Exception as e:
        print(f"✗ Error creating data source: {e}")
        ds_id = None

    # Step 5: Start ingestion job
    if ds_id:
        print("\nStep 5: Starting data ingestion...")

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
    print(f"\n📋 IMPORTANT: Update your .env file:")
    print(f"   KNOWLEDGE_BASE_ID={kb_id}")
    print(f"\nNext steps:")
    print(f"1. Update KNOWLEDGE_BASE_ID in .env file")
    print(f"2. Wait for ingestion job to complete (2-5 minutes)")
    print(f"3. Run: streamlit run src/cvc_chatbot_rag.py")
    print(f"\n💰 Monthly Cost Breakdown:")
    print(f"  • OpenSearch t3.small.search: ~$20-40/month")
    print(f"  • S3 storage: <$0.01/month")
    print(f"  • Total: ~$20-40/month")
    print(f"  vs Previous Serverless: ~$90-180/month")


if __name__ == "__main__":
    create_knowledge_base()
