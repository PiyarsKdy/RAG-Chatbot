from datetime import datetime
import json
import os
import time
import dotenv
from fastapi import   APIRouter, HTTPException, Response
from openai import OpenAI

from helpers.calendar_functions import book_event, check_availability
from helpers.sql_agent import execute_query
dotenv.load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

router = APIRouter()


def get_assistant(company_id):
    try:
        result = execute_query("SELECT assistant_id FROM company_assistants_store WHERE company_id = %s", (company_id,), cmd='fetchone')
        if result is None:
            return {"message": "No assistant found for the given company_id"}
        else:
            return result[0]
    except Exception as e:
        return {"message": str(e)}
    
def get_auth_key(company_id):
    try:
        result = execute_query("SELECT auth_key FROM company_details WHERE company_id = %s", (company_id,), cmd='fetchone')
        if result is None:
            return {"message": "Not authorized"}
        else:
            return result[0]
    except Exception as e:
        return {"message": str(e)}
    

@router.get("/createThread")
async def create_thread():
    try:
        response = client.beta.threads.create()
        return {"thread_id": response.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/companyQuery")
async def process_question(request_data: dict):
    t_id = request_data.get("t_id")
    query = request_data.get("question")
    company_id = request_data.get("company_id")
    auth_key = request_data.get("auth_key")

    db_auth_key = get_auth_key(company_id)
    if isinstance(db_auth_key, dict):
        raise HTTPException(status_code=404, detail=a_id['message'])
    elif auth_key != db_auth_key:
        raise HTTPException(status_code=404, detail='Not authorized')

    a_id = get_assistant(company_id)
    if isinstance(a_id, dict):
        raise HTTPException(status_code=404, detail=a_id['message'])

    curr_date = datetime.today().strftime('%Y-%m-%d')
    date_str = f"Today's date is {curr_date}"
    execute_query("INSERT INTO chat_history (sender_id, receiver_id, content, timestamp) VALUES (%s, %s, %s, %s)", (company_id, 0, query, datetime.now().strftime('%Y-%m-%d %H:%M:%S')), cmd = 'commit' )
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
        # result = execute_query("INSERT INTO chat_history (sender_id, receiver_id, content, timestamp) VALUES (%s, %s, %s, %s)", (0, company_id, last_message.content[0].text.value, datetime.now().strftime('%Y-%m-%d %H:%M:%S')), cmd = 'commit')
