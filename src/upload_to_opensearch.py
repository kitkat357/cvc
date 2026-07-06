"""
Process course/transfer data and upload to OpenSearch with embeddings.
This replaces the Bedrock Knowledge Base data sync.
"""

import boto3
import json
import time
from typing import List, Dict, Any
from pathlib import Path
import config


class DataUploader:
    """Upload course data to OpenSearch with embeddings."""

    def __init__(self):
        """Initialize AWS clients."""
        session = boto3.Session(
            profile_name=config.AWS_PROFILE,
            region_name=config.AWS_REGION
        )

        self.bedrock_runtime = session.client('bedrock-runtime')
        self.opensearch = session.client('opensearch')

        # Get OpenSearch endpoint
        domain_status = self.opensearch.describe_domain(DomainName='cvc-courses')
        self.opensearch_endpoint = f"https://{domain_status['DomainStatus']['Endpoint']}"

        # Set up OpenSearch HTTP client with AWS auth
        from requests_aws4auth import AWS4Auth
        import requests

        credentials = session.get_credentials()
        self.awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            config.AWS_REGION,
            'es',
            session_token=credentials.token
        )
        self.requests = requests

        self.index_name = 'cvc-courses-index'

    def embed_text(self, text: str) -> List[float]:
        """Embed text using Bedrock Titan Embeddings."""
        body = json.dumps({"inputText": text})

        response = self.bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=body
        )

        result = json.loads(response['body'].read())
        return result['embedding']

    def process_course_catalog(self, file_path: str, college_name: str, year: str) -> List[Dict]:
        """Process a course catalog JSON file."""
        print(f"\nProcessing {college_name} catalog ({year})...")

        with open(file_path, 'r') as f:
            data = json.load(f)

        documents = []

        # Handle different JSON structures
        courses_list = data.get('courses', [])
        if not courses_list:
            # Try alternative structure (dict of depts)
            for dept_code, courses in data.items():
                if isinstance(courses, list):
                    courses_list.extend(courses)

        for course in courses_list:
            if not isinstance(course, dict):
                continue

            dept_code = course.get('department_code', 'MISC')

            # Build document text
            text_parts = [
                f"{course.get('title', 'Unknown Course')} - {course.get('department', dept_code)} Department",
                course.get('description', course.get('enhanced_description', '')),
            ]

            # Add units
            if 'units' in course:
                units_str = str(course['units']).replace('.000', '')
                text_parts.append(f"Units: {units_str}")

            # Add GE info
            if 'ge_areas' in course and course['ge_areas']:
                ge_text = "Satisfies GE Areas: " + ", ".join(course['ge_areas'])
                text_parts.append(ge_text)

            # Add transferability
            if course.get('csu_transferable'):
                text_parts.append("CSU Transferable")
            if course.get('uc_transferable'):
                text_parts.append("UC Transferable")

            text = ". ".join(filter(None, text_parts))

            # Build metadata
            metadata = {
                'college': college_name,
                'department_code': dept_code,
                'course_number': course.get('course_number', ''),
                'course_code': f"{dept_code} {course.get('course_number', '')}",
                'title': course.get('title', ''),
                'department': course.get('department', dept_code) or dept_code,
                'units': str(course.get('units', '')).replace('.000', ''),
                'academic_year': year,
                'source_type': 'catalog'
            }

            # Create document ID
            doc_id = f"{college_name.lower().replace(' ', '_')}_{dept_code}_{course.get('course_number', '')}".replace(' ', '_')

            documents.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })

        print(f"  Processed {len(documents)} courses")
        return documents

    def process_transfer_data(self, file_path: str, from_college: str, to_college: str, year: str) -> List[Dict]:
        """Process a transfer agreement JSON file."""
        print(f"\nProcessing transfers: {from_college} → {to_college} ({year})...")

        with open(file_path, 'r') as f:
            data = json.load(f)

        documents = []

        # Get transfers list
        transfers_list = data.get('transfers', [])

        for course in transfers_list:
            if not isinstance(course, dict):
                continue

            from_course = course.get('from_course', '')
            title = course.get('course_title', '')

            # Build transfer destinations text
            transfers_to = course.get('transfers_to', [])
            if transfers_to:
                dest_text = ", ".join(transfers_to)
            else:
                dest_text = "No direct equivalent"

            # Build document text
            text = (
                f"{from_course} ({title}) from {from_college} transfers to: {dest_text} "
                f"at {to_college}. Units: {course.get('units', 'N/A')}. "
                f"Department: {course.get('department', 'N/A')}."
            )

            # Build metadata
            metadata = {
                'from_college': from_college,
                'to_college': to_college,
                'from_course': from_course,
                'course_title': title,
                'units': str(course.get('units', '')),
                'department': course.get('department', ''),
                'transfers_to': transfers_to,
                'academic_year': year,
                'source_type': 'transfer'
            }

            # Create document ID
            doc_id = f"transfer_{from_college.lower().replace(' ', '_')}_{from_course}_{to_college.lower().replace(' ', '_')}".replace(' ', '_').replace(',', '')

            documents.append({
                'id': doc_id,
                'text': text,
                'metadata': metadata
            })

        print(f"  Processed {len(documents)} transfer mappings")
        return documents

    def upload_documents(self, documents: List[Dict], batch_size: int = 50):
        """
        Upload documents to OpenSearch with embeddings.

        Args:
            documents: List of dicts with 'id', 'text', 'metadata'
            batch_size: Number of documents to upload per batch
        """
        print(f"\nUploading {len(documents)} documents to OpenSearch...")
        print(f"Batch size: {batch_size}")

        url = f"{self.opensearch_endpoint}/_bulk"

        total_batches = (len(documents) + batch_size - 1) // batch_size

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(documents))
            batch = documents[start_idx:end_idx]

            # Build bulk request
            bulk_data = []

            for doc in batch:
                # Generate embedding
                vector = self.embed_text(doc['text'])

                # Index action
                bulk_data.append(json.dumps({
                    "index": {
                        "_index": self.index_name,
                        "_id": doc['id']
                    }
                }))

                # Document data
                bulk_data.append(json.dumps({
                    "text": doc['text'],
                    "metadata": doc['metadata'],
                    "vector": vector
                }))

            # Upload batch
            bulk_body = "\n".join(bulk_data) + "\n"

            response = self.requests.post(
                url,
                auth=self.awsauth,
                data=bulk_body,
                headers={"Content-Type": "application/x-ndjson"}
            )

            if response.status_code not in [200, 201]:
                print(f"  ⚠️ Batch {batch_num + 1}/{total_batches} failed: {response.text[:200]}")
            else:
                result = response.json()
                errors = result.get('errors', False)
                if errors:
                    print(f"  ⚠️ Batch {batch_num + 1}/{total_batches} had errors")
                else:
                    print(f"  ✓ Batch {batch_num + 1}/{total_batches} uploaded successfully ({len(batch)} docs)")

            # Rate limiting - avoid overwhelming Bedrock embeddings API
            time.sleep(0.5)

        print(f"\n✓ Upload complete!")

    def process_all_data(self):
        """Process and upload all course and transfer data."""
        print("="*60)
        print("Processing and Uploading Course Data")
        print("="*60)

        all_documents = []

        # Process course catalogs
        print("\n--- Processing Course Catalogs ---")

        catalogs = [
            ('data/cerritos_output_final.json', 'Cerritos College', '2019-2025'),
            ('data/output.json', 'Mount San Antonio College', '2024-2025'),
            ('data/VVC_output.json', 'Victor Valley College', '2024-2025'),
        ]

        for file_path, college, year in catalogs:
            try:
                docs = self.process_course_catalog(file_path, college, year)
                all_documents.extend(docs)
            except FileNotFoundError:
                print(f"  ⚠️ File not found: {file_path}")
            except Exception as e:
                print(f"  ⚠️ Error processing {file_path}: {e}")

        # Process transfer agreements
        print("\n--- Processing Transfer Agreements ---")

        transfers = [
            ('data/simple_transfers.json', 'Victor Valley College', 'Cal State Fullerton', '2024-2025'),
            ('data/simple_transfers (1).json', 'Victor Valley College', 'Cal Poly SLO', '2024-2025'),
            ('data/simple_transfers (2).json', 'Cuesta College', 'Cal Poly SLO', '2024-2025'),
        ]

        for file_path, from_college, to_college, year in transfers:
            try:
                docs = self.process_transfer_data(file_path, from_college, to_college, year)
                all_documents.extend(docs)
            except FileNotFoundError:
                print(f"  ⚠️ File not found: {file_path}")
            except Exception as e:
                print(f"  ⚠️ Error processing {file_path}: {e}")

        print(f"\n{'='*60}")
        print(f"Total documents to upload: {len(all_documents)}")
        print(f"{'='*60}")

        # Upload to OpenSearch
        if all_documents:
            self.upload_documents(all_documents)

            # Verify upload
            print("\nVerifying upload...")
            verify_url = f"{self.opensearch_endpoint}/{self.index_name}/_count"
            response = self.requests.get(verify_url, auth=self.awsauth)

            if response.status_code == 200:
                count = response.json()['count']
                print(f"✓ Index now contains {count} documents")
            else:
                print(f"⚠️ Could not verify: {response.text}")

        print("\n" + "="*60)
        print("✓ Data processing complete!")
        print("="*60)
        print("\nNext step: Run streamlit with the custom RAG pipeline")
        print("  streamlit run src/cvc_chatbot_custom_rag.py --server.port 8502")


if __name__ == "__main__":
    uploader = DataUploader()
    uploader.process_all_data()
