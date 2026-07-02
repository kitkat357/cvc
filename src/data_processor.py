"""
Process course and transfer data into Bedrock Knowledge Base format.
Transforms JSON files into structured documents with metadata for RAG retrieval.
"""

import json
import config
from pathlib import Path


def process_course_catalog(file_path: str, college_name: str, academic_year: str) -> list:
    """
    Process a course catalog JSON file into Knowledge Base format.

    Args:
        file_path: Path to JSON file
        college_name: Name of the college
        academic_year: Academic year (e.g., "2024-2025")

    Returns:
        List of processed course documents
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    courses = data.get('courses', [])
    processed_docs = []

    for course in courses:
        dept_code = course.get('department_code', '').strip()
        course_num = course.get('course_number', '').strip()
        title = course.get('title', '').strip()
        department = course.get('department', '').strip()
        description = course.get('enhanced_description') or course.get('description', '')
        units = course.get('units', '0')

        # Create document ID
        doc_id = f"{college_name}_{dept_code}_{course_num}".lower().replace(' ', '-')

        # Create searchable text
        text = f"{title} - {department}: {description}"

        # Create document
        doc = {
            "document_id": doc_id,
            "text": text,
            "metadata": {
                "college": college_name,
                "department_code": dept_code,
                "course_number": course_num,
                "course_code": f"{dept_code} {course_num}",
                "title": title,
                "department": department,
                "units": str(units),
                "academic_year": academic_year,
                "source_type": "catalog"
            }
        }

        processed_docs.append(doc)

    return processed_docs


def process_transfer_data(file_path: str, from_college: str, to_college: str, academic_year: str) -> list:
    """
    Process transfer/articulation data into Knowledge Base format.

    Args:
        file_path: Path to JSON file
        from_college: Source college name
        to_college: Destination college name
        academic_year: Academic year (e.g., "2024-2025")

    Returns:
        List of processed transfer documents
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    transfers = data.get('transfers', [])
    processed_docs = []

    for transfer in transfers:
        from_course = transfer.get('from_course', '').strip()
        title = transfer.get('course_title', '').strip()
        units = transfer.get('units', 0)
        department = transfer.get('department', '').strip()
        transfers_to = transfer.get('transfers_to', [])

        # Create document ID
        doc_id = f"transfer_{from_college}_{from_course}_{to_college}".lower().replace(' ', '-').replace('/', '-')

        # Create searchable text with transfer information
        transfer_list = ", ".join(transfers_to) if transfers_to else "No equivalent course"
        text = f"{from_course} ({title}) from {from_college} transfers to: {transfer_list} at {to_college}"

        # Create document
        doc = {
            "document_id": doc_id,
            "text": text,
            "metadata": {
                "from_college": from_college,
                "to_college": to_college,
                "from_course": from_course,
                "course_title": title,
                "units": str(units),
                "department": department,
                "transfers_to": transfers_to,
                "academic_year": academic_year,
                "source_type": "transfer"
            }
        }

        processed_docs.append(doc)

    return processed_docs


def export_for_knowledge_base(documents: list, output_path: str):
    """
    Export documents in JSON Lines format for Bedrock Knowledge Base.

    Args:
        documents: List of processed documents
        output_path: Path to output file
    """
    with open(output_path, 'w') as f:
        for doc in documents:
            f.write(json.dumps(doc) + '\n')

    print(f"✓ Exported {len(documents)} documents to {output_path}")


def main():
    """Main processing workflow."""
    print("=== CVC Data Processing for RAG ===\n")

    all_documents = []

    # Process course catalogs
    print("Processing course catalogs...")
    college_mapping = {
        "cerritos": ("Cerritos College", "2019-2025"),
        "mount_san_antonio": ("Mount San Antonio College", "2022-2026"),
        "victor_valley": ("Victor Valley College", "2022-2026"),
    }

    for key, (college_name, year) in college_mapping.items():
        file_path = config.get_data_file_path(config.COURSE_FILES[key])
        docs = process_course_catalog(file_path, college_name, year)
        all_documents.extend(docs)
        print(f"  ✓ {college_name}: {len(docs)} courses")

    # Process transfer data
    print("\nProcessing transfer data...")
    transfer_mapping = {
        "vvc_to_csuf": ("Victor Valley College", "Cal State Fullerton", "2024-2025"),
        "vvc_to_calpoly": ("Victor Valley College", "Cal Poly SLO", "2024-2025"),
        "cuesta_to_calpoly": ("Cuesta College", "Cal Poly SLO", "2024-2025"),
    }

    for key, (from_college, to_college, year) in transfer_mapping.items():
        file_path = config.get_data_file_path(config.TRANSFER_FILES[key])
        docs = process_transfer_data(file_path, from_college, to_college, year)
        all_documents.extend(docs)
        print(f"  ✓ {from_college} → {to_college}: {len(docs)} transfers")

    # Export
    output_dir = Path(config.DATA_DIR) / "processed"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "all_documents.jsonl"

    export_for_knowledge_base(all_documents, str(output_path))

    print(f"\n✓ Total documents processed: {len(all_documents)}")
    print(f"✓ Output file: {output_path}")
    print(f"\nNext step: Run upload_to_s3.py to upload to AWS")


if __name__ == "__main__":
    main()
