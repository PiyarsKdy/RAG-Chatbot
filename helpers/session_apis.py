from fastapi import APIRouter, Depends, Response

from helpers.openai_api_client import delete_thread
from helpers.session_info import *

router = APIRouter()

@router.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data


@router.post("/delete_session")
async def del_session(t_id: str,response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    resp = delete_thread(t_id)
    if resp.status_code == 200:
        print("thread deleted")
    else:
        print("Error:", resp.status_code, resp.text)
    return "deleted session"