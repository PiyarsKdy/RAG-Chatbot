import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import pytz
import dotenv
dotenv.load_dotenv()
# Service account credentials
SCOPES = ['https://www.googleapis.com/auth/calendar']

CALENDER_ID = os.getenv('CALENDER_ID')
credentials = os.getenv('SERVICE_ACCOUNT_CREDS')
info = json.loads(credentials)

def authenticate():
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service



def SCHEDULE_EVENT(date1, time1):
    print("book call")
    time_available = GetAvailabilityByTime(date1, time1)
    if time_available['response'] == 'The slot is not available':
        return {'message': 'The slot is not available'}
    service = authenticate()
    start_time = datetime.strptime(date1 + ' ' + time1, "%Y-%m-%d %H:%M:%S")
    end_time = start_time + timedelta(hours=1)
    ist = pytz.timezone('Asia/Kolkata')
    start_time = ist.localize(start_time)
    end_time = ist.localize(end_time)
    start_time_iso = start_time.isoformat()
    end_time_iso = end_time.isoformat()

    # Create the event
    summary = "This is an appointment"
    description = 'This is a sample appointment description'
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time_iso,
            'timeZone': 'Asia/Kolkata', 
        },
        'end': {
            'dateTime': end_time_iso,
            'timeZone': 'Asia/Kolkata', 
        },
    }
    try:
        print("book try")
        event = service.events().insert(calendarId=CALENDER_ID, body=event).execute()
        return {'message': "Event created successfully."}
    except HttpError as error:
        return {'message': error}

def GetAvailabilityByTime(date1, time1):
    print("avail call")
    service = authenticate()
    print("avail auth")
    start_time = datetime.strptime(date1 + ' ' + time1, "%Y-%m-%d %H:%M:%S")
    end_time = start_time + timedelta(hours=1)
    ist = pytz.timezone('Asia/Kolkata')
    start_time = ist.localize(start_time)
    end_time = ist.localize(end_time)
    start_time_iso = start_time.isoformat()
    end_time_iso = end_time.isoformat()
    print("avail bf event_rsult")
    events_result = service.freebusy().query(
        body={
            "timeMin": start_time_iso,
            "timeMax": end_time_iso,
            "items": [{"id": CALENDER_ID}]
        }
    ).execute()
    print("avail bf busy_periods")
    busy_periods = events_result['calendars'][CALENDER_ID]['busy']
    print("avail af busy_periods")
    if len(busy_periods) == 0:
        return {'response': f'The slot is available'}
    else:
        return {'response': f'The slot is not available'}
