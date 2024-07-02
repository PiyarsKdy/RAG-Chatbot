import io
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
import dotenv
import os
import json
import boto3
from openai import OpenAI
import requests
from urllib.parse import urlparse
import secrets
import string
from helpers.constants import *
from helpers.session_info import *

dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_api_key(length=18):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_company_id(domain):
    return execute_query("SELECT company_id, name FROM company_details WHERE domain = %s", (domain, ), cmd = 'fetchone')

def store_assistant(assistant_id, company_id):
    return execute_query("INSERT INTO company_assistants_store (assistant_id,company_id) VALUES (%s, %s)", (assistant_id, company_id), cmd = 'commit')


from helpers.sql_agent import execute_query

dotenv.load_dotenv()
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
router = APIRouter()

def get_image_type(url):
    # Parse the URL to get the path
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # Get the file extension from the path
    _, ext = os.path.splitext(path)
    
    # Remove the dot from the extension
    ext = ext.lstrip('.')
    
    return ext.lower()

bucket_name = "kantanna-assets"

def fetch_and_upload_logo(url_or_file, domain, company,  hex):
    global bucket_name

    if isinstance(url_or_file, str):
        # URL case
        image_type = get_image_type(url_or_file)
        try:
            logo_response = requests.get(url_or_file)
            logo_data = io.BytesIO(logo_response.content)
            s3.upload_fileobj(logo_data, bucket_name, f"{domain}.{image_type}", ExtraArgs={'ContentType': 'image/jpeg'})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching/uploading image: {e}")
    else:
        # File case
        image_type = get_image_type(url_or_file.filename)
        try:
            s3.upload_fileobj(url_or_file.file, bucket_name, f"{domain}.{image_type}", ExtraArgs={'ContentType': url_or_file.content_type})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading file to bucket: {e}")

    if hex:
        try:
            s3.put_object(Body=json.dumps({"hex": hex, "chatbotName": company, "image_path": f"https://kantanna-assets.s3.amazonaws.com/{domain}.{image_type}"}), Bucket=bucket_name, Key=f"{domain}.json")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error putting json object in bucket: {e}")

@router.post('/logo_url',dependencies=[Depends(cookie)])
async def logo_url(request_data: dict):
    # userid = request_data.get("userid")
    url = request_data.get("logo")
    domain = request_data.get("domain")
    hex = request_data.get('hex')
    company = request_data.get('company')
    api_key = generate_api_key()
    path = f"s3://kantanna-assets/{domain}.{get_image_type(url)}"
    # resp = execute_query("SELECT company_id, name FROM company_details WHERE domain = %s", (domain, ), cmd = 'fetchone')
    company_record = get_company_id(domain)
    if company_record:
        return {"error": "Domain already exists"}
    else:
        print(execute_query("INSERT INTO company_details (name, domain, auth_key, s3_logo_path, theme_color) VALUES (%s, %s, %s, %s, %s)", (company, domain, api_key, path, hex), cmd = 'commit'))
        company_record = get_company_id(domain)
    print(company_record)

    if company_record:
        name = company_record[1]
        company_id = str(company_record[0])
        try:
            # creates assistant
            assistant = client.beta.assistants.create(
                name = name,
                instructions = "Analyze the user content. Only call 'check_availability' if the user wants to check slot availability and both date and time are given. Only call 'book_event' if the user wants to book a slot and both date and time are provided. In all other cases, use the retrieval tool to answer the user's query. Do not assume dates and time. You have to ask user to be more specific and enter required details. Before calling 'book_event', always ask for user confirmation.",
                model = "gpt-4-turbo-preview",
                tools = [{
                    "type" : "retrieval",
                },
                {
                    "type" : "function", "function" : check_availability
                },
                {
                    "type": "function", "function" : book_event
                }],
            )
            print(assistant.id)
            print(store_assistant(assistant.id, company_id)  )  
        except Exception as e:
            print(e)
            return {"error": "assistant is not created"}

    fetch_and_upload_logo(url, domain, company, hex)
    return {'message': "created successfully"}

    

@router.post('/logo_file', dependencies=[Depends(cookie)])
async def logo_file(hex: str = Form(...), domain : str = Form(...),company : str = Form(...), files: UploadFile = File(...)):
    api_key = generate_api_key()
    path = f"s3://kantanna-assets/{domain}.{get_image_type(files.filename)}"
    company_record = get_company_id(domain)
    if company_record:
        return {"error": "Domain already exists"}
    else:
        print(execute_query("INSERT INTO company_details (name, domain, auth_key, s3_logo_path, theme_color) VALUES (%s, %s, %s, %s, %s)", (company, domain, api_key, path, hex), cmd = 'commit'))
        company_record = get_company_id(domain)
    print(company_record)

    if company_record:
        name = company_record[1]
        company_id = str(company_record[0])
        try:
            # creates assistant
            assistant = client.beta.assistants.create(
                name = name,
                instructions = "Analyze the user content. Only call 'check_availability' if the user wants to check slot availability and both date and time are given. Only call 'book_event' if the user wants to book a slot and both date and time are provided. In all other cases, use the retrieval tool to answer the user's query. Do not assume dates and time. You have to ask user to be more specific and enter required details. Before calling 'book_event', always ask for user confirmation.",
                model = "gpt-4-turbo-preview",
                tools = [{
                    "type" : "retrieval",
                },
                {
                    "type" : "function", "function" : check_availability
                },
                {
                    "type": "function", "function" : book_event
                }],
            )
            print(assistant.id)
            print(store_assistant(assistant.id, company_id)  )  
        except Exception as e:
            print(e)
            return {"error": "assistant is not created"}
    
    
    fetch_and_upload_logo(files, domain, company, hex)
    return {'message': "created successfully"}
