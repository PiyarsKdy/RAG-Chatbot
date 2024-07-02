
from fastapi import Depends, Depends, Form, APIRouter, HTTPException
import os
import sys

from helpers.company_query_api import get_assistant
sys.path.append("..")
from openai import OpenAI
import dotenv

from helpers.session_info import *
dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

router = APIRouter()

# get assistant instructions
@router.get('/get_instructions', dependencies=[Depends(cookie)])
async def get_instructions(company_id: str):

    # get assistant from rds
    a_id = get_assistant(company_id)
    if not a_id:
        raise HTTPException(status_code=404, detail="Assistant not found")
    try:

        my_assistant = client.beta.assistants.retrieve(a_id)
        return {"instructions": my_assistant.instructions}
    except Exception as e:
        print(f"Error retrieving assistant: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving assistant")

# update assistant instructions
@router.post('/update_instructions', dependencies=[Depends(cookie)])
async def update_instructions(request_data: dict):
    company_id = request_data.get('company_id')
    instructions = request_data.get('instructions')

    # get assistant from rds
    a_id = get_assistant(company_id)
    if not a_id:
        raise HTTPException(status_code=404, detail="Assistant not found")
    try:
        my_updated_assistant = client.beta.assistants.update(a_id, instructions=instructions)
        print(my_updated_assistant)
        return {"message": "Instructions updated successfully"}
    except Exception as e:
        print(f"Error updating assistant: {e}")
        raise HTTPException(status_code=500, detail="Error updating assistant")