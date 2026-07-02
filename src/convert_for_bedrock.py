"""
Convert processed JSONL to plain text format for Bedrock Knowledge Base.
Bedrock KB prefers plain text files with metadata in S3 object metadata.
"""

import json
import boto3
from pathlib import Path
import config

def upload_documents_as_text():
    """Upload documents as plain text files to S3 for Bedrock KB ingestion."""

    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    s3_client = session.client('s3')

    # Read processed documents
    jsonl_path = Path(config.DATA_DIR) / "processed" / "all_documents.jsonl"

    if not jsonl_path.exists():
        print(f"✗ File not found: {jsonl_path}")
        print("  Run data_processor.py first")
        return

    print(f"=== Converting Documents for Bedrock KB ===")
    print(f"Reading from: {jsonl_path}\n")

    documents = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            doc = json.loads(line.strip())
            documents.append(doc)

    print(f"Found {len(documents)} documents\n")

    # Clear existing catalog and transfer data (will replace with text format)
    print("Clearing old structured JSON files...")
    prefixes = ['catalogs/', 'transfers/']
    for prefix in prefixes:
        response = s3_client.list_objects_v2(
            Bucket=config.S3_BUCKET_NAME,
            Prefix=prefix
        )

        if 'Contents' in response:
            for obj in response['Contents']:
                s3_client.delete_object(
                    Bucket=config.S3_BUCKET_NAME,
                    Key=obj['Key']
                )
                print(f"  Deleted: {obj['Key']}")

    print(f"✓ Cleared old files\n")

    # Upload each document as a .txt file with metadata in S3 object tags
    print("Uploading documents as plain text...")

    uploaded_count = 0
    for doc in documents:
        # Create plain text content
        text_content = f"{doc['text']}\n\nMetadata:\n"
        for key, value in doc['metadata'].items():
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            text_content += f"- {key}: {value}\n"

        # Determine S3 key based on source type
        metadata = doc['metadata']
        if metadata['source_type'] == 'catalog':
            college_slug = metadata['college'].lower().replace(' ', '-')
            s3_key = f"documents/catalogs/{college_slug}/{doc['document_id']}.txt"
        else:  # transfer
            from_college = metadata['from_college'].lower().replace(' ', '-')
            to_college = metadata['to_college'].lower().replace(' ', '-')
            s3_key = f"documents/transfers/{from_college}-to-{to_college}/{doc['document_id']}.txt"

        # Upload to S3
        try:
            s3_client.put_object(
                Bucket=config.S3_BUCKET_NAME,
                Key=s3_key,
                Body=text_content.encode('utf-8'),
                ContentType='text/plain',
                Metadata={
                    'college': metadata.get('college', ''),
                    'course_code': metadata.get('course_code', metadata.get('from_course', '')),
                    'units': str(metadata.get('units', '')),
                    'source_type': metadata['source_type']
                }
            )
            uploaded_count += 1

            if uploaded_count % 100 == 0:
                print(f"  Uploaded {uploaded_count}/{len(documents)} documents...")

        except Exception as e:
            print(f"  ✗ Error uploading {s3_key}: {e}")

    print(f"\n✓ Uploaded {uploaded_count} documents as plain text files")

    print("\n" + "="*60)
    print("✓ Conversion complete!")
    print("="*60)
    print(f"\nUploaded {uploaded_count} .txt files to S3")
    print(f"\nNext steps:")
    print(f"1. Go to AWS Console → Bedrock → Knowledge Bases")
    print(f"2. Open: cvc-course-catalog")
    print(f"3. Click Data source → Sync")
    print(f"4. Wait for sync to complete (2-5 minutes)")
    print(f"5. Run: streamlit run src/cvc_chatbot_rag.py")


if __name__ == "__main__":
    upload_documents_as_text()
