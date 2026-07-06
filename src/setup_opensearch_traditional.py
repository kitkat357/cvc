"""
Create traditional OpenSearch domain (on-demand) for cost savings.
Cost: ~$20-40/month vs ~$90-180/month for Serverless
"""

import boto3
import json
import time
import config

def create_opensearch_domain():
    """Create traditional OpenSearch domain with on-demand instances."""

    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    opensearch = session.client('opensearch')
    sts_client = session.client('sts')

    domain_name = 'cvc-courses'
    account_id = sts_client.get_caller_identity()['Account']

    print(f"=== Creating Traditional OpenSearch Domain ===")
    print(f"Domain Name: {domain_name}")
    print(f"Region: {config.AWS_REGION}")
    print(f"Instance Type: t3.small.search (cost-optimized)")
    print(f"Estimated Cost: ~$20-40/month\n")

    # Check if domain already exists
    print("Step 1: Checking for existing domain...")
    try:
        existing = opensearch.describe_domain(DomainName=domain_name)
        print(f"✓ Domain already exists")
        print(f"  Endpoint: https://{existing['DomainStatus']['Endpoint']}")
        print(f"  Status: {existing['DomainStatus']['Processing']}")
        return
    except opensearch.exceptions.ResourceNotFoundException:
        print("✓ No existing domain found, creating new one...")

    # Step 2: Create domain
    print("\nStep 2: Creating OpenSearch domain...")
    print("  This will take 10-15 minutes...\n")

    # Access policy - allow Bedrock and local profile
    access_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "es:*",
                "Resource": f"arn:aws:es:{config.AWS_REGION}:{account_id}:domain/{domain_name}/*"
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{account_id}:root"
                },
                "Action": "es:*",
                "Resource": f"arn:aws:es:{config.AWS_REGION}:{account_id}:domain/{domain_name}/*"
            }
        ]
    }

    try:
        response = opensearch.create_domain(
            DomainName=domain_name,
            EngineVersion='OpenSearch_2.11',
            ClusterConfig={
                'InstanceType': 't3.small.search',
                'InstanceCount': 1,
                'DedicatedMasterEnabled': False,
                'ZoneAwarenessEnabled': False
            },
            EBSOptions={
                'EBSEnabled': True,
                'VolumeType': 'gp3',
                'VolumeSize': 10
            },
            AccessPolicies=json.dumps(access_policy),
            EncryptionAtRestOptions={
                'Enabled': True
            },
            NodeToNodeEncryptionOptions={
                'Enabled': True
            },
            DomainEndpointOptions={
                'EnforceHTTPS': True,
                'TLSSecurityPolicy': 'Policy-Min-TLS-1-2-2019-07'
            },
            AdvancedSecurityOptions={
                'Enabled': False
            }
        )

        domain_arn = response['DomainStatus']['ARN']
        print(f"✓ Domain creation initiated!")
        print(f"  ARN: {domain_arn}")
        print(f"  Status: {response['DomainStatus']['Processing']}")

    except Exception as e:
        print(f"✗ Error creating domain: {e}")
        return

    # Step 3: Wait for domain to be ready
    print("\nStep 3: Waiting for domain to become active...")
    print("  This typically takes 10-15 minutes")
    print("  You can monitor progress in AWS Console: OpenSearch → Domains\n")

    max_attempts = 60
    attempt = 0

    while attempt < max_attempts:
        try:
            status = opensearch.describe_domain(DomainName=domain_name)
            processing = status['DomainStatus']['Processing']

            if not processing:
                endpoint = status['DomainStatus']['Endpoint']
                print(f"\n✓ Domain is ACTIVE!")
                print(f"  Endpoint: https://{endpoint}")
                break

            attempt += 1
            print(f"  Still creating... (attempt {attempt}/{max_attempts})")
            time.sleep(15)

        except Exception as e:
            print(f"  Error checking status: {e}")
            attempt += 1
            time.sleep(15)

    if attempt >= max_attempts:
        print("\n⚠️ Timeout waiting for domain")
        print("   Domain is still creating, check AWS Console")
        print("   Run this script again later or proceed manually")
        return

    print("\n" + "="*60)
    print("✓ OpenSearch domain setup complete!")
    print("="*60)
    print(f"\nDomain Name: {domain_name}")
    print(f"Endpoint: https://{endpoint}")
    print(f"\nNext steps:")
    print(f"1. Run: python src/create_opensearch_index_traditional.py")
    print(f"2. Run: python src/setup_knowledge_base_traditional.py")
    print(f"3. Update .env with new Knowledge Base ID")
    print(f"4. Run: streamlit run src/cvc_chatbot_rag.py")

    print(f"\n💰 Cost Savings:")
    print(f"  Traditional OpenSearch: ~$20-40/month")
    print(f"  vs Serverless: ~$90-180/month")
    print(f"  Savings: ~$50-140/month!")


if __name__ == "__main__":
    create_opensearch_domain()
