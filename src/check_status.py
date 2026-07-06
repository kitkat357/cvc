"""
Quick status check for all AWS resources.
"""

import boto3
import config

def check_status():
    """Check status of all CVC RAG resources."""

    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    opensearch = session.client('opensearch')
    bedrock_agent = session.client('bedrock-agent')
    s3 = session.client('s3')

    print("="*60)
    print("CVC RAG Chatbot - Resource Status Check")
    print("="*60)

    # Check S3 Bucket
    print("\n1. S3 Bucket:")
    try:
        s3.head_bucket(Bucket=config.S3_BUCKET_NAME)
        objects = s3.list_objects_v2(Bucket=config.S3_BUCKET_NAME)
        count = objects.get('KeyCount', 0)
        print(f"   ✅ Bucket '{config.S3_BUCKET_NAME}' exists")
        print(f"   📁 Files: {count}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Check OpenSearch Domain
    print("\n2. OpenSearch Domain:")
    try:
        status = opensearch.describe_domain(DomainName='cvc-courses')
        domain = status['DomainStatus']
        processing = domain['Processing']
        endpoint = domain.get('Endpoint', 'Not ready yet')

        if processing:
            print(f"   🔄 Status: CREATING")
            print(f"   ⏳ Endpoint: Not ready yet")
        else:
            print(f"   ✅ Status: ACTIVE")
            print(f"   🌐 Endpoint: https://{endpoint}")

    except opensearch.exceptions.ResourceNotFoundException:
        print(f"   ❌ Domain 'cvc-courses' does not exist")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Check Knowledge Bases
    print("\n3. Bedrock Knowledge Bases:")
    try:
        kbs = bedrock_agent.list_knowledge_bases()

        if not kbs['knowledgeBaseSummaries']:
            print(f"   ❌ No Knowledge Bases found")
        else:
            for kb in kbs['knowledgeBaseSummaries']:
                name = kb['name']
                kb_id = kb['knowledgeBaseId']
                status = kb.get('status', 'UNKNOWN')

                if status == 'ACTIVE':
                    print(f"   ✅ {name}")
                    print(f"      ID: {kb_id}")
                elif status == 'DELETE_UNSUCCESSFUL':
                    print(f"   ⚠️  {name} (stuck in deletion)")
                    print(f"      ID: {kb_id}")
                else:
                    print(f"   🔄 {name} ({status})")
                    print(f"      ID: {kb_id}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Check .env file
    print("\n4. Environment Configuration:")
    try:
        if config.KNOWLEDGE_BASE_ID:
            print(f"   ✅ KNOWLEDGE_BASE_ID set: {config.KNOWLEDGE_BASE_ID}")
        else:
            print(f"   ⚠️  KNOWLEDGE_BASE_ID not set in .env")
    except:
        print(f"   ⚠️  KNOWLEDGE_BASE_ID not set in .env")

    print("\n" + "="*60)
    print("Status check complete!")
    print("="*60)


if __name__ == "__main__":
    check_status()
