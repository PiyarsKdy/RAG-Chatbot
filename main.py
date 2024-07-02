import time
import uvicorn
from fastapi import Depends, FastAPI
import time
import json
import os
from datetime import datetime
import sys
sys.path.append("..")
from openai import OpenAI
import dotenv
from helpers.session_info import *
from helpers.env_loader import *
from helpers.text_extractor import *
from helpers.sql_agent import execute_query
from helpers.calendar_functions import check_availability, book_event
dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
from helpers import auth, company_query_api, instructions_api, upload,files_apis, session_apis,logo_upload, company_details
app = FastAPI()
app.include_router(upload.router)
app.include_router(auth.router)
app.include_router(instructions_api.router)
app.include_router(files_apis.router)
app.include_router(session_apis.router)
app.include_router(logo_upload.router)
app.include_router(company_query_api.router)
app.include_router(company_details.router)
from fastapi.middleware.cors import CORSMiddleware


@app.get("/generateThread", dependencies=[Depends(cookie)])
async def create_company_thread():
    try:
        response = client.beta.threads.create()
        return {"thread_id": response.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/deleteThread", dependencies=[Depends(cookie)])
async def delete_company_thread(t_id: str):
    try:
        response = client.beta.threads.delete(t_id)
        return {"message": "Thread deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# query and retrieval api
@app.post("/query",  dependencies=[Depends(cookie)])
async def process_question(request_data: dict):
    t_id = request_data.get("t_id")
    query = request_data.get("question")
    company_id = request_data.get("company_id")
    print(t_id)
    
    a_id = company_query_api.get_assistant(company_id)
    print(a_id)
    if isinstance(a_id, dict):
        raise HTTPException(status_code=404, detail=a_id['message'])


    curr_date = datetime.today().strftime('%Y-%m-%d')
    date_str = f"Today's date is {curr_date}"
    print(execute_query("INSERT INTO chat_history (sender_id, receiver_id, content, timestamp) VALUES (%s, %s, %s, %s)", (company_id, 0, query, datetime.now().strftime('%Y-%m-%d %H:%M:%S')), cmd = 'commit' ))
    try:
        message = client.beta.threads.messages.create(
            thread_id=t_id,
            role = "user",
            content = query
        )
        run = client.beta.threads.runs.create(
            thread_id=t_id,
            assistant_id=a_id,
            instructions=date_str
        )
        print("2: Entering to retrieval state", datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        i = 0
        while(True):
            if i>0:
                time.sleep(2)
            run = client.beta.threads.runs.retrieve(
                thread_id=t_id,
                run_id=run.id
            )
            i += 1
            if(run.status=='completed'):
                run_status = run.status
                messages = client.beta.threads.messages.list(
                    thread_id=t_id,
                )
                break
            elif run.status=='failed':
                return {"answer": "Failed to retrieve answer from assistant. Please try again"}
            elif run.status=='expired':
                return {"answer": "Failed to retrieve answer from assistant. Please try again"}
            elif run.status=='requires_action':
                tools_to_call = run.required_action.submit_tool_outputs.tool_calls

                tool_output_array = []

                for each_tool in tools_to_call:
                    tool_call_id = each_tool.id
                    function_name =each_tool.function.name
                    function_arg = each_tool.function.arguments

                    function_arg_dict = json.loads(function_arg)

                    if 'time' not in function_arg_dict or function_arg_dict.get('time') == None:
                        output = 'Please, specify time'
                    elif 'date' not in function_arg_dict or function_arg_dict.get('date') == None:
                        output = 'Please, specify date'
                    else:
                        data = {
                            "date": function_arg_dict.get('date'),
                            "time": function_arg_dict.get('time')
                        }
                        if function_name == "check_availability":
                            output = check_availability(data)['message']
                        elif function_name == "book_event":
                            if "book" not in function_arg_dict or function_arg_dict.get('book') == False or function_arg_dict.get('book') == None:
                                output = 'Are you sure you want to book an event on ' + function_arg_dict.get('date') + ' at ' + function_arg_dict.get('time') + '?'
                            else:
                                output = book_event(data)['message']
                    print(output)
                    tool_output_array.append({"tool_call_id": tool_call_id, "output": output})
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=t_id,
                    run_id=run.id,
                    tool_outputs=tool_output_array
                )

        print("3: Exiting from retrieval state", datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
        if run_status == 'completed':
            if messages.data:
                last_message = messages.data[0]
                if last_message.role == 'user':
                    return {"answer": "Sorry, I couldn't find answer from give information"}
                else:
                    execute_query("INSERT INTO chat_history (sender_id, receiver_id, content, timestamp) VALUES (%s, %s, %s, %s)", (0, company_id, last_message.content[0].text.value, datetime.now().strftime('%Y-%m-%d %H:%M:%S')), cmd = 'commit')
                    return {"answer": last_message.content[0].text.value}
        else:

            return {"answer": "Sorry, I couldn't find answer from give information"}
                    
    except Exception as e:
        print(f"Error: {e}")
        return {"answer": "Failed to retrieve answer from assistant. Please try again"}
    # finally:
    #     result = execute_query("INSERT INTO chat_history (sender_id, receiver_id, content, timestamp) VALUES (%s, %s, %s, %s)", (0, company_id, last_message.content[0].text.value, datetime.now().strftime('%Y-%m-%d %H:%M:%S')), cmd = 'commit')


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
   print(os.getenv("OPENAI_API_KEY"))
   uvicorn.run("main:app", host="0.0.0.0", port=8000)


