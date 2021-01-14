from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from appconfig import GOOGLE_CALENDAR_ID, SCOPES
import csv
import logging

# If modifying these scopes, delete the file token.pickle.

# GOOGLE_CALENDAR_ID = 'primary'


class SnowFormat:
    def __init__(self, customer, start_date, end_date, description, number):
        self.customer = customer
        self.start_date = start_date
        self.end_date = end_date
        self.description = description
        self.number = number
        self.colorId = "5" # default color

    # fields
    def get_start_date(self):
        return self.get_date(dt=self.start_date)

    def get_start_time(self):
        return self.get_time(dt=self.start_date)

    def get_end_date(self):
        return self.get_date(dt=self.end_date)

    def get_end_time(self):
        return self.get_time(dt=self.end_date)

    # formatting
    def get_date(self, dt):
        return dt[0:10]

    def get_time(self, dt):
        return dt[11:16]

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

    service = build("calendar", "v3", credentials=creds)

    return service


def get_events(maxResults=100):
    service = get_google_api_service()
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    events_result = (
        service.events()
        .list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=now,
            maxResults=maxResults,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    return events


def read():
    snowfile_list = []

    with open("change_request.csv", "r", encoding="UTF-8") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')

        for id, row in enumerate(reader):
            if id > 0:
                snowline = SnowFormat(
                    customer=row[0],
                    start_date=row[1],
                    end_date=row[2],
                    description=row[3],
                    number=row[4],
                )
                snowfile_list.append(snowline)

    return snowfile_list


def delete_events(events):

    future_events = get_events()
    ids_to_delete = []

    #delete all events in the file
    for fevents in future_events:
        for e in events:
            if e.number == fevents.get("location"):
                ids_to_delete.append(fevents.get("id"))

    #delete all events in calendar not in file


    service = get_google_api_service()
    for id in ids_to_delete:
        service.events().delete(calendarId=GOOGLE_CALENDAR_ID, eventId=id).execute()
        print(f"{id} deleted")

# def get_colors():
#     service = get_google_api_service()
#     colors = service.colors().get().execute()

#     # Print available calendarListEntry colors.
#     for id, color in colors['calendar'].iteritem():
#         print('colorId: %s' % id)


def create_events(events):

    service = get_google_api_service()

    for s in events:

        if s.get_start_date() != "" and s.get_end_date() != "":
            pass
        else:
            if s.get_start_date() == "":
                #sub 1h
                #convert to date
                dt = datetime.datetime.strptime(f'{s.get_end_date()} {s.get_end_time()}', '%Y-%m-%d %H:%M')
                new_dt = dt - datetime.timedelta(hours=1)
                dt_str = datetime.datetime.strftime(new_dt, '%Y-%m-%d %H:%M')
                s.start_date = dt_str
                s.colorId = '6'
                s.description = '**start date missing**' + s.description
                pass
            if s.get_end_date() == "":
                # add 1h
                dt = datetime.datetime.strptime(f'{s.get_start_date()} {s.get_start_time()}', '%Y-%m-%d %H:%M')
                new_dt = dt - datetime.timedelta(hours=-1)
                dt_str = datetime.datetime.strftime(new_dt, '%Y-%m-%d %H:%M')
                s.start_date = dt_str
                s.colorId = '6'
                s.description = '**end date missing**' + s.description
                pass



        try:
            event = {
                # 'id': s.get_id(),
                # i.e. YPG (CHG0047241)
                "summary": f"{s.customer} ({s.number})",
                "location": s.number,
                "description": s.description,
                "start": {
                    "dateTime": f"{s.get_start_date()}T{s.get_start_time()}:00",
                    "timeZone": "America/New_York",
                },
                "end": {
                    "dateTime": f"{s.get_end_date()}T{s.get_end_time()}:00",
                    "timeZone": "America/New_York",
                },
                "colorId": s.colorId
            }

            #if exists delete first

            event = (
                service.events()
                .insert(calendarId=GOOGLE_CALENDAR_ID, body=event)
                .execute()
            )
        except Exception as e:
            logging.error(f"Event details: {s}. Import failed: {e}.")
            continue

        print(f"{s.get_id()} created")


if __name__ == "__main__":
    #get_colors()
    events = read()
    delete_events(events)
    create_events(events)
