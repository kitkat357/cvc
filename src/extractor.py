import fitz
import boto3
import json
from botocore.exceptions import ClientError
import time

import logging

logger = logging.getLogger(__name__)

MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0" 
REGION = "us-west-2"
PROMPT_FILE_PATH = "prompts/course_extraction.txt"

def load_prompt_with_text(page_text: str) -> str:
    """
    Reads the base prompt and appends the page text.
    """
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as file:
        base_prompt = file.read()
    return f"{base_prompt}\n\nText to process (1 page of catalog): {page_text}"


def invoke_bedrock(page_text: str) -> str:
    """
    Calls Bedrock with the prompt and page text.
    Returns the raw model response.
    """

    client = boto3.client("bedrock-runtime", region_name=REGION)
    prompt = load_prompt_with_text(page_text)

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 32768,
        "temperature": 0.3,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    try:
        response = client.invoke_model_with_response_stream(
            modelId=MODEL_ID, 
            body=json.dumps(native_request),
            contentType="application/json",
            accept="application/json")
        event_stream = response.get('body')

        full_response=""

        for event in event_stream:
            chunk = event.get('chunk')
            if chunk:
                message = json.loads(chunk.get("bytes").decode())
                if message['type'] == "content_block_delta":
                    full_response+=message['delta']['text']

    except ClientError as e:
        logger.error(f"Bedrock client error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
    return full_response

def clean_model_response(response: str) -> str:
    """
    Removes Markdown-style code blocks from the Claude response.
    """
    if response.startswith("```json"):
        response = response[len("```json"): 2].strip()
    if response.endswith("```"):
        response = response[:-3].strip()
    return response

# print(f"\n\n--- Page {page_number + 1} Text ---\n{page_text[:1000]}\n")

def extract_courses_from_pdf(pdf_path: str) -> list:
    """
    Extracts and processes text from each PDF page, calling the Claude model for structured output.
    Returns a list of all raw course dictionaries from all pages.
    """
    all_courses = []
    pdf_document = fitz.open(pdf_path)

    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text("text")
        print(f"\n\n--- Page {page_number + 1} Text ---\n{page_text[:1000]}\n")

        model_response = invoke_bedrock(page_text)
        print(f"\n--- Raw Model Response ---\n{model_response}\n")


        if model_response:
            json_string = clean_model_response(model_response)
            try:
                page_courses = json.loads(json_string)
                all_courses.extend(page_courses)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed on page {page_number + 1}: {e}")

        if (page_number + 1) % 2 == 0:
            time.sleep(30)

    return all_courses


def merging_incomplete_courses(all_courses: list) -> list:
    """
    Merges courses that are split across pages due to incomplete entries.
    Returns a cleaned list with complete course entries.
    """
    final_courses = []
    i = 0

    while i < len(all_courses):
        course = all_courses[i]
        if not course.get("incomplete"):
            del course["incomplete"]
            final_courses.append(course)
            i+=1
        else:
            if i < len(all_courses) - 1:
                next_part = all_courses[i + 1]
                for attribute in ["department_code", "course_number", "title", "units", "department"]:
                    if course.get(attribute) == "":
                        course[attribute] = next_part[attribute]
                if next_part.get("description") != "":

                    if course.get("description"):
                        course["description"] = course["description"] + " " + next_part["description"]
                    else:
                        course["description"] = next_part["description"]
                    del course["incomplete"]
                    final_courses.append(course)
                    i+=2
            else:
                del course["incomplete"]
                final_courses.append(course)
                i += 1
    return final_courses

def fill_missing_department_names(courses: list) -> list:
    """
    Fills in missing department names based on department_code matches.
    """
    dept_map = {}

    for course in courses:
        code = course.get("department_code")
        name = course.get("department")
        if code and name:
            dept_map[code] = name 

    for course in courses:
        if course.get("department") == "":
            code = course.get("department_code")
            if code in dept_map:
                course["department"] = dept_map[code]

    return courses

def write_catalog_json(academic_year: str, institution: str, courses: list, output_path: str):
    """
    Writes the final JSON catalog to the specified file.
    """
    catalog = {
        "catalog_info": {
            "academic_year": academic_year,
            "institution": institution
        },
        "total_courses": len(courses),
        "courses": courses
    }

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(catalog, output_file, indent=2)