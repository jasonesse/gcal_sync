from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from appconfig import GOOGLE_CALENDAR_ID, DATE_FORMAT
import csv
import logging
from send_email.send_gmail import notify

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

class FileSpec:
    def __init__(self, customer, start_date, end_date, description, number):
        self.customer = customer
        self.start_date = start_date
        self.end_date = end_date
        self.description = description
        self.number = number
        self.colorId = "5"  # default color

    def get_start_date_str(self) -> str:
        return self.get_date_str(dt=self.start_date)

    def get_start_time_str(self) -> str:
        return self.get_time_str(dt=self.start_date)

    def get_end_date_str(self) -> str:
        return self.get_date_str(dt=self.end_date)

    def get_end_time_str(self) -> str:
        return self.get_time_str(dt=self.end_date)

    def get_date_str(self, dt) -> str:
        res = ''
        try:
            res = dt[0:10]
        except:
            pass
        return res

    def get_time_str(self, dt) -> str:
        res = ''
        try:
            res = dt[11:16]
        except:
            pass
        return res


    def get_id(self):
        return self.number.lower()

    def __str__(self):
        return f"Customer:{self.customer},Number:{self.number},StartDate:{self.start_date},EndDate:{self.end_date}"

def get_google_api_service():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    return service

def get_google_cal_events(maxResults=100, timeMin=datetime.datetime.utcnow().isoformat() + "Z"):# 'Z' indicates UTC time
    service = get_google_api_service()

    events_result = (
        service.events()
        .list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=timeMin.isoformat() + "Z",
            maxResults=maxResults,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    return events

def get_new_events():
    new_events = []

    with open("change_request.csv", "r", encoding="UTF-8") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')

        for id, row in enumerate(reader):
            if id > 0:
                file_event = FileSpec(
                    customer=row[0],
                    start_date=row[1],
                    end_date=row[2],
                    description=row[3],
                    number=row[4],
                )
                new_events.append(file_event)

    return new_events

def get_min_start_date(new_events):
    start_dates = []
    for s in new_events:
        if s.start_date != '':
            start_dates.append(datetime.datetime.strptime(s.start_date, DATE_FORMAT))
    try:
        min_start_date = min(start_dates)
    except:
        min_start_date = datetime.datetime.now()
    return min_start_date

def calc_missing_date_str(dt_str: str, hours: int, fmt=DATE_FORMAT) -> str:
    dt = datetime.datetime.strptime(dt_str, fmt)
    return datetime.datetime.strftime(
        dt + datetime.timedelta(hours=hours), DATE_FORMAT
    )

def upsert_events(new_events):

    service = get_google_api_service()

    min_start_date = get_min_start_date(new_events)
    google_cal_events = get_google_cal_events(timeMin=min_start_date)
    ids_to_delete = {}

    # delete all google cal events found in file to refresh
    gcal_ids = []
    gcal_dict_id = {} #holds actual id for updating.
    new_event_ids = []
    for gcal_event in google_cal_events:
        gcal_id = gcal_event.get("location")
        gcal_ids.append(gcal_id)
        gcal_dict_id.update({gcal_id:gcal_event.get("id")})
        for e in new_events:
            new_event_ids.append(e.number)
            if e.number == gcal_id:
                ids_to_delete.update({e.number: gcal_event.get("id")})

    #create new events
    for s in new_events:
        
        #if event already exists, delete it to refresh it's data.
        id_to_delete = ids_to_delete.get(s.number,0)
        if id_to_delete != 0:
            service.events().delete(calendarId=GOOGLE_CALENDAR_ID, eventId=id_to_delete).execute()
            logging.info(f"{id} deleted")

        if s.get_start_date_str() != "" and s.get_end_date_str() != "":
            pass
        elif s.get_start_date_str() == "" and s.get_end_date_str() == "":
            #raise ValueError("Both start and end dates are empty.")
            logging.error("Both start and end dates are empty.")
            #notify(f"Both start and end dates are empty") #broken.

            continue
        else:
            if s.start_date == "":
                s.start_date = calc_missing_date_str(dt_str=s.end_date, hours=-1)
                s.colorId = "6"
                s.description = "**start date missing**\n" + s.description

            if s.end_date == "":
                s.end_date = calc_missing_date_str(dt_str=s.start_date, hours=1)
                s.colorId = "6"
                s.description = "**end date missing**\n" + s.description

        try:
            event = {
                #"summary": f"{s.customer} ({s.number})",
                "summary": s.customer,
                "location": s.number,
                "description": s.description,
                "start": {
                    "dateTime": f"{s.get_start_date_str()}T{s.get_start_time_str()}:00",
                    "timeZone": "America/New_York",
                },
                "end": {
                    "dateTime": f"{s.get_end_date_str()}T{s.get_end_time_str()}:00",
                    "timeZone": "America/New_York",
                },
                "colorId": s.colorId,
            }

            # if exists delete first

            event = (
                service.events()
                .insert(calendarId=GOOGLE_CALENDAR_ID, body=event)
                .execute()
            )
        except Exception as e:
            logging.error(f"Event details: {s}. Import failed: {e}.")
            continue

        print(f"{s.get_id()} created")

        #update missing file events to red.
    gcal_nin_file = list(set(gcal_ids) - set(new_event_ids))

    for event_nin_file in gcal_nin_file:
        eventId = gcal_dict_id.get(event_nin_file)
        event = service.events().get(calendarId=GOOGLE_CALENDAR_ID, eventId=eventId).execute()
        event['colorId'] = '11' # red
        service.events().update(calendarId=GOOGLE_CALENDAR_ID, eventId=event['id'], body=event).execute()


# def get_colors():
#     service = get_google_api_service()
#     colors = service.colors().get().execute()

#     # Print available calendarListEntry colors.
#     for id, color in colors['calendar'].iteritem():
#         print('colorId: %s' % id)


if __name__ == "__main__":
    # get_colors()
    new_events = get_new_events()
    upsert_events(new_events)
