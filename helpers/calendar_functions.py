from helpers.calendar_client import     SCHEDULE_EVENT, GetAvailabilityByTime

def check_availability(req: dict):
    date = req.get('date')
    time = req.get('time')
    try:
        response = GetAvailabilityByTime(date, time)
        print(response)
        return {'message': response['response']}
    except:
        return {"message": "Please specify valid date range"}


def book_event(req:dict):
    date = req.get('date')
    time = req.get('time')
    return SCHEDULE_EVENT(date, time)