from fastapi import  Response, APIRouter
import os
import sys
from uuid import uuid4

sys.path.append("..")
from openai import OpenAI
import dotenv
from helpers.session_info import *
from helpers.constants import *
from helpers.sql_agent import execute_query
from helpers.openai_api_client import  post_request

dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def get_user(email):
    return execute_query("SELECT user_id, name, password FROM users WHERE email = %s", (email, ), cmd = 'fetchone')

def store_assistant(userid,assistant_id):
    return execute_query("INSERT INTO assistant_store (userid,assistant_id) VALUES (%s, %s)", (userid, assistant_id), cmd = 'commit')

def get_assistant(userid):
    return execute_query("SELECT assistant_id FROM assistant_store WHERE userid = %s", (userid, ), cmd = 'fetchone')[0]

router = APIRouter()

@router.post("/register")
async def register(request_data: dict,response: Response):
    name = request_data.get("name")
    email = request_data.get("email")
    password = request_data.get("password")
    resp = execute_query("INSERT INTO users (email, name, password) VALUES (%s, %s, %s)", (email, name, password), cmd = 'commit')
    if resp:
        if 'message' in resp:
            return {"error": "User already exists"}
    user_record = get_user(email)
    if user_record:
        name = user_record[1]
        id = str(user_record[0])

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
        except Exception as e:
            print(e)
            return {"error": "assistant is not created"}
        
        # store assistant
        store_assistant(id, assistant.id)

        # create session
        session = uuid4()
        data = SessionData(userid=id)

        await backend.create(session, data)
        cookie.attach_to_response(response, session)
        
        # create thread
        resp = post_request("https://api.openai.com/v1/threads")
        if resp.status_code == 200:
            t_id = resp.json().get('id')
        else:
            print("Error:", resp.status_code, resp.text)
            return {"error": "thread is not created"}
        return {"message": "User logged in...", "name": name,"session": session,"t_id":t_id }
    else: 
        return {"message": "User not found", "session": None, "name": None,"t_id": None }
    pass


@router.post("/login")
async def login(request_data: dict, response: Response):
    email = request_data.get("email")
    password = request_data.get("password")
    user_record = get_user(email)

    if user_record:
        pw = user_record[2]
        if password != pw:
            return {"message": "Wrong password", "session": None, "name": None,"t_id": None}
        name = user_record[1]
        id = str(user_record[0])

        # create session
        session = uuid4()
        data = SessionData(userid=id)

        await backend.create(session, data)
        cookie.attach_to_response(response, session)

        print(f"created session for {id}")

        # create thread
        resp = post_request("https://api.openai.com/v1/threads")
        if resp.status_code == 200:
            t_id = resp.json().get('id')
            print(t_id)
        else:
            print("Error:", resp.status_code, resp.text)
        return {"message": "User logged in...", "name": name,"session": session,"t_id":t_id}
    else:
        return {"message": "User not found", "session": None, "name": None,"t_id": None }

