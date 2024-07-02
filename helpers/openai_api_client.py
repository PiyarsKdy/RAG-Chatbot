import os, requests  

from dotenv import load_dotenv


load_dotenv()

headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "OpenAI-Beta": "assistants=v1"
    }

def delete_thread(t_id):
    return requests.delete(f"https://api.openai.com/v1/threads/{t_id}", headers=headers)

def post_request_data(url, data):
    return requests.post(url, json=data, headers=headers)

def post_request(url):
    return requests.post(url, headers=headers)
def get_request(url):
    return requests.get(url, headers=headers)