"""
Upload course and transfer data to S3 bucket for Bedrock Knowledge Base.
"""

import json
import boto3
from pathlib import Path
import config

def create_s3_bucket():
    """Create S3 bucket if it doesn't exist."""
    session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
    s3_client = session.client('s3')

    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=config.S3_BUCKET_NAME)
        print(f"✓ Bucket {config.S3_BUCKET_NAME} already exists")
    except:
        # Create bucket
        print(f"Creating bucket {config.S3_BUCKET_NAME}...")
        if config.AWS_REGION == 'us-east-1':
            s3_client.create_bucket(Bucket=config.S3_BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=config.S3_BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': config.AWS_REGION}
            )
        print(f"✓ Bucket created successfully")

    # Enable versioning
    s3_client.put_bucket_versioning(
        Bucket=config.S3_BUCKET_NAME,
        VersioningConfiguration={'Status': 'Enabled'}
    )
    print(f"✓ Versioning enabled")

    return s3_client


def upload_course_data(s3_client):
    """Upload course catalog files to S3."""
    print("\n=== Uploading Course Catalogs ===")

    college_mapping = {
        "cerritos": ("cerritos-college", "2019-2025"),
        "mount_san_antonio": ("mount-san-antonio", "2022-2026"),
        "victor_valley": ("victor-valley", "2022-2026"),
    }

    for key, filename in config.COURSE_FILES.items():
        file_path = config.get_data_file_path(filename)
        college_name, year = college_mapping[key]
        s3_key = f"{config.S3_CATALOG_PREFIX}/{college_name}/{year}/courses.json"

        try:
            s3_client.upload_file(
                file_path,
                config.S3_BUCKET_NAME,
                s3_key
            )
            print(f"✓ Uploaded: {s3_key}")
        except Exception as e:
            print(f"✗ Failed to upload {filename}: {e}")


def upload_transfer_data(s3_client):
    """Upload transfer/crosswalk files to S3."""
    print("\n=== Uploading Transfer Data ===")

    transfer_mapping = {
        "vvc_to_csuf": ("victor-valley", "cal-state-fullerton", "2024-2025"),
        "vvc_to_calpoly": ("victor-valley", "cal-poly-slo", "2024-2025"),
        "cuesta_to_calpoly": ("cuesta", "cal-poly-slo", "2024-2025"),
    }

    for key, filename in config.TRANSFER_FILES.items():
        file_path = config.get_data_file_path(filename)
        from_college, to_college, year = transfer_mapping[key]
        s3_key = f"{config.S3_TRANSFER_PREFIX}/{from_college}/to-{to_college}/{year}/transfers.json"

        try:
            s3_client.upload_file(
                file_path,
                config.S3_BUCKET_NAME,
                s3_key
            )
            print(f"✓ Uploaded: {s3_key}")
        except Exception as e:
            print(f"✗ Failed to upload {filename}: {e}")


def verify_uploads(s3_client):
    """Verify all files were uploaded successfully."""
    print("\n=== Verifying Uploads ===")

    response = s3_client.list_objects_v2(Bucket=config.S3_BUCKET_NAME)

    if 'Contents' in response:
        print(f"\n✓ Total files in bucket: {len(response['Contents'])}")
        print("\nFiles:")
        for obj in response['Contents']:
            size_kb = obj['Size'] / 1024
            print(f"  - {obj['Key']} ({size_kb:.2f} KB)")
    else:
        print("✗ No files found in bucket")


def main():
    """Main upload workflow."""
    print(f"=== CVC RAG Data Upload ===")
    print(f"Bucket: {config.S3_BUCKET_NAME}")
    print(f"Region: {config.AWS_REGION}")
    print(f"Profile: {config.AWS_PROFILE}\n")

    # Create bucket and get client
    s3_client = create_s3_bucket()

    # Upload data
    upload_course_data(s3_client)
    upload_transfer_data(s3_client)

    # Verify
    verify_uploads(s3_client)

    print("\n✓ Upload complete!")
    print(f"\nNext steps:")
    print(f"1. Create Bedrock Knowledge Base in AWS Console")
    print(f"2. Point it to s3://{config.S3_BUCKET_NAME}/")
    print(f"3. Configure Titan Embeddings G1")
    print(f"4. Copy Knowledge Base ID to .env file")


if __name__ == "__main__":
    main()
