import os
import re
import shutil
import sys
import time
import boto3
import dotenv
from fastapi import File, Depends, APIRouter, UploadFile
from helpers.company_query_api import get_assistant
from helpers.session_info import cookie
from helpers.text_extractor import *

sys.path.append("..")
from openai import OpenAI

dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

router = APIRouter()

bucket_name = "kantanna-files-data"
temp_dir = "temp_files"

def create_temp_dir():
    """Create a temporary directory to store files."""
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

def create_file_copy(old_file, new_file_path):
    """Create a copy of the uploaded file in the temporary directory."""
    try:
        with open(new_file_path, 'wb') as new_file:
            shutil.copyfileobj(old_file.file, new_file)
        print(f"File successfully created at: {new_file_path}")
    except FileNotFoundError:
        print(f"Error: File not found")

def upload_file_to_assistant(file_path, assistant_id):
    """Upload a file to the OpenAI assistant."""
    try:
        with open(file_path, 'rb') as f:
            file_obj = client.files.create(file=f, purpose='assistants')
        f.close()
        assistant_file = client.beta.assistants.files.create(assistant_id=assistant_id, file_id=file_obj.id)
    except Exception as e:
        print(f'Error uploading file {file_path}: {e}')

def upload_files_to_assistant(assistant_id, num_files_to_upload):
    """Upload multiple files to the OpenAI assistant."""
    if os.path.exists(temp_dir):
        files = sorted(os.listdir(temp_dir))

        for i in range(num_files_to_upload):
            if i >= len(files):
                break
            f_name = files[i]
            file_path = os.path.join(temp_dir, f_name)
            upload_file_to_assistant(file_path, assistant_id)

    # Clean up temporary files
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))

@router.post("/upload_files", dependencies=[Depends(cookie)])
async def upload_file(company_id: str, upload_file: UploadFile = File(...)):
    """Upload a file to the OpenAI assistant."""
    file_name = upload_file.filename
    create_temp_dir()

    try:
        a_id = get_assistant(company_id)
        num_files = len(client.beta.assistants.files.list(assistant_id=a_id).data)
        print(f"Number of existing files: {num_files}")
    except Exception as e:
        print(f'Error getting number of files for assistant {a_id}: {e}')
        num_files = 0
        return {"error": "Unable to upload file content, try after sometime."}

    if num_files >= 20:
        return {"error": "Content uploading limit has reached."}

    if file_name.endswith(".csv"):
        texts = await extract_text_from_csv(upload_file.file)
        if not texts.strip():
            return {"error": "Unable to extract text from file"}
        cleaned_texts = re.sub('[^A-Za-z0-9]+', ' ', texts)
        try:
            text_file_path = os.path.join(temp_dir, f"{file_name[:-4]}.txt")
            with open(text_file_path, 'w') as text_file:
                text_file.write(cleaned_texts)
        except Exception as e:
            print(f"Error: {e}")
        upload_file_to_assistant(text_file_path, a_id)
    elif file_name.endswith((".pdf", ".txt")):
        file_path = os.path.join(temp_dir, file_name)
        create_file_copy(upload_file, file_path)
        upload_file_to_assistant(file_path, a_id)
    else:
        return {"error": "Unsupported file format"}

    return {"message": "File uploaded successfully"}

@router.post("/upload", dependencies=[Depends(cookie)])
async def upload_by_url(request_data: dict):
    """Upload website content to the OpenAI assistant."""
    url = request_data.get("url")
    company_id = request_data.get("company_id")
    create_temp_dir()

    if not url.startswith("http"):
        url = "http://" + url

    await handle_url(url)  # Function to handle URL and fetch website content

    a_id = get_assistant(company_id)

    if not a_id:
        print("Error: Assistant not found")
        return {"error": "Assistant not found"}

    try:
        num_files = len(client.beta.assistants.files.list(assistant_id=a_id).data)
        print(f"Number of existing files: {num_files}")
    except Exception as e:
        print(f'Error getting number of files for assistant {a_id}: {e}')
        num_files = 0
        return {"error": "Unable to upload website content, try after sometime."}

    if num_files >= 20:
        return {"error": "Content uploading limit has reached."}

    diff = 20 - num_files
    num_files_in_temp_dir = len(os.listdir(temp_dir)) if os.path.exists(temp_dir) else 0

    if num_files_in_temp_dir > diff:
        upload_files_to_assistant(a_id, diff)
        return {"error": "Content uploading limit has reached."}
    else:
        upload_files_to_assistant(a_id, num_files_in_temp_dir)
        return {"message": "Website content uploaded successfully"}