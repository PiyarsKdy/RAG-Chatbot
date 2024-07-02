from fastapi import Depends, APIRouter
import os
import sys
import requests

from helpers.company_query_api import get_assistant
sys.path.append("..")
from openai import OpenAI
import dotenv
from helpers.session_info import *
from helpers.openai_api_client import  get_request

dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


router = APIRouter()

# fetch files attached with assistants
@router.get("/files", dependencies=[Depends(cookie)])
async def get_files(company_id: str):

    # get assistant from rds
    a_id = get_assistant(company_id)
    print(a_id)
    if not a_id:
        print("Error: Assistant not found")
        return {"error": "Assistant not found"}
    
    try:
        response = get_request(f"https://api.openai.com/v1/assistants/{a_id}/files")
    except Exception as e:
        print(f"Error: {e}")
        return {"error": "Failed to get files"}
    if response.status_code == 200:
        ids = [item['id'] for item in response.json()['data']]
        header = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        }
        responses = []
        try:
            for id in ids:
                response = requests.get(f"https://api.openai.com/v1/files/{id}", headers=header)
                responses.append(response.json())
        except Exception as e:
            print(f"Error: {e}")
            return {"error": "Failed to get files"}
        arr = [(item['id'], item['filename']) for item in responses]
        new_arr = []
        for x in arr:
            if x[1].startswith("web- "):
                new_arr.append((x[0], x[1][:-4]))
            else:
                new_arr.append(x)
        return {'data': new_arr}
    else:
        print("Error:", response.status_code, response.text)
        return {"error": "Failed to get files"}

# delete a file
@router.delete('/delete_file', dependencies=[Depends(cookie)])
async def delete_file(request_data: dict):
    company_id = request_data.get('company_id')
    file_id = request_data.get('file_id')

    # get assistant from rds
    a_id = get_assistant(company_id)
    if not a_id:
        print("Error: Assistant not found")
        return {"error": "Assistant not found"}
    
    deleted_assistant_file = client.beta.assistants.files.delete(
        assistant_id=a_id,
        file_id=file_id
    )
    return {"message": "deleted_assistant_file"}