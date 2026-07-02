"""
Configuration module for CVC RAG Chatbot.
Loads environment variables and provides centralized AWS configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AWS Configuration
AWS_PROFILE = os.getenv("AWS_PROFILE", "cvc-project")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "cvc-rag-course-data")

# Bedrock Configuration
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "")
CLAUDE_MODEL_ID = os.getenv(
    "CLAUDE_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0"
)

# Data paths (relative to project root)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Course data files
COURSE_FILES = {
    "cerritos": "cerritos_output_final.json",
    "mount_san_antonio": "output.json",
    "victor_valley": "VVC_output.json",
}

# Transfer data files
TRANSFER_FILES = {
    "vvc_to_csuf": "simple_transfers.json",
    "vvc_to_calpoly": "simple_transfers (1).json",
    "cuesta_to_calpoly": "simple_transfers (2).json",
}

# S3 path structure
S3_CATALOG_PREFIX = "catalogs"
S3_TRANSFER_PREFIX = "transfers"
S3_METADATA_PREFIX = "metadata"


def get_data_file_path(filename: str) -> str:
    """Get full path to a data file."""
    return os.path.join(DATA_DIR, filename)


def validate_config() -> bool:
    """Validate that required configuration is set."""
    if not KNOWLEDGE_BASE_ID:
        print("WARNING: KNOWLEDGE_BASE_ID not set in environment")
        return False
    return True
