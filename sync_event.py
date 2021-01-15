import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from appconfig import FILEPATH, GOOGLE_CALENDAR_ID, DATE_FORMAT
import csv
import logging

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class FileSpec:
    def __init__(
        self, customer, start_datetime_str, end_datetime_str, description, number
    ):
        self.customer = customer
        self.start_datetime_str = start_datetime_str
        self.end_datetime_str = end_datetime_str
        self.description = description
        self.number = number
        self.colorId = "5"  # default color

    @property
    def id(self):
        return self.number.lower()

    @property
    def start_date_str(self):
        return self.get_date_str(dt=self.start_datetime_str)

    @property
    def end_date_str(self):
        return self.get_date_str(dt=self.end_datetime_str)

    @property
    def start_time_str(self):
        return self.get_time_str(dt=self.start_datetime_str)

    @property
    def end_time_str(self):
        return self.get_time_str(dt=self.end_datetime_str)

    def get_date_str(self, dt) -> str:
        res = ""
        try:
            res = dt[0:10]
        except:
            pass
        return res

    def get_time_str(self, dt) -> str:
        res = ""
        try:
            res = dt[11:16]
        except:
            pass
        return res

    def __str__(self):
        return f"Customer:{self.customer},Number:{self.number},StartDate:{self.start_datetime_str},EndDate:{self.end_datetime_str}"


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

    return build("calendar", "v3", credentials=creds, cache_discovery=False)


# TODO timemin
def get_google_cal_events(
    maxResults=100, timeMin=datetime.datetime.utcnow().isoformat() + "Z"
):  # 'Z' indicates UTC time
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
    return events_result.get("items", [])


def read_new_events():

    new_events = []

    with open(FILEPATH, "r", encoding="UTF-8") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')

        for id, row in enumerate(reader):
            if id > 0:
                file_event = FileSpec(
                    customer=row[0],
                    start_datetime_str=row[1],
                    end_datetime_str=row[2],
                    description=row[3],
                    number=row[4],
                )
                new_events.append(file_event)

    return new_events


def get_min_start_date(new_events):

    start_dates = [
        datetime.datetime.strptime(s.start_datetime_str, DATE_FORMAT)
        for s in new_events
        if s.start_date_str != ""
    ]

    try:
        min_start_date = min(start_dates)
    except:
        min_start_date = datetime.datetime.now()
    return min_start_date


def calc_missing_date_str(dt_str: str, hours: int, fmt=DATE_FORMAT) -> str:
    dt = datetime.datetime.strptime(dt_str, fmt)
    return datetime.datetime.strftime(dt + datetime.timedelta(hours=hours), DATE_FORMAT)


def get_gcalids_to_delete(new_events):

    min_start_date = get_min_start_date(new_events)
    google_cal_events = get_google_cal_events(timeMin=min_start_date)
    ids_to_delete = {}

    # delete all google cal events found in file to refresh
    gcal_ids = []
    gcal_dict_id = {}  # holds actual id for updating.
    new_event_ids = []
    for gcal_event in google_cal_events:
        gcal_id = gcal_event.get("location")
        gcal_ids.append(gcal_id)
        gcal_dict_id.update({gcal_id: gcal_event.get("id")})
        for e in new_events:
            new_event_ids.append(e.number)
            if e.number == gcal_id:
                ids_to_delete.update({e.number: gcal_event.get("id")})

    gcal_nin_file = list(set(gcal_ids) - set(new_event_ids))

    return ids_to_delete, gcal_nin_file, gcal_dict_id


def get_event_body(event):
    return {
        # "summary": f"{s.customer} ({s.number})",
        "summary": event.customer,
        "location": event.number,
        "description": event.description,
        "start": {
            "dateTime": f"{event.start_date_str}T{event.start_time_str}:00",
            "timeZone": "America/New_York",
        },
        "end": {
            "dateTime": f"{event.end_date_str}T{event.end_time_str}:00",
            "timeZone": "America/New_York",
        },
        "colorId": event.colorId,
    }


def upsert_events(new_events):

    service = get_google_api_service()

    ids_to_delete, gcal_nin_file, gcal_dict_id = get_gcalids_to_delete(new_events)

    # create new events
    for s in new_events:
        # if event already exists, delete it to refresh it's data.
        id_to_delete = ids_to_delete.get(s.number, 0)
        if id_to_delete != 0:
            service.events().delete(
                calendarId=GOOGLE_CALENDAR_ID, eventId=id_to_delete
            ).execute()
            logging.info(f"{id} deleted")

        if s.start_datetime_str == "" and s.end_datetime_str == "":
            logging.error(f"{s.number} : Both start and end dates are empty.")
            # notify(f"Both start and end dates are empty") #broken.
        else:
            if s.start_datetime_str == "":
                s.start_datetime_str = calc_missing_date_str(
                    dt_str=s.end_datetime_str, hours=-1
                )
                s.colorId = "6"
                s.description = "**start date missing**\n" + s.description

            if s.end_datetime_str == "":
                s.end_datetime_str = calc_missing_date_str(
                    dt_str=s.start_datetime_str, hours=1
                )
                s.colorId = "6"
                s.description = "**end date missing**\n" + s.description

        try:

            service.events().insert(
                calendarId=GOOGLE_CALENDAR_ID, body=get_event_body(s)
            ).execute()

        except Exception as e:
            logging.error(f"Event details: {s}. Import failed: {e}.")
            continue

        logging.debug(f"{s.id} created")

    # update missing file events to red.
    for event_nin_file in gcal_nin_file:
        eventId = gcal_dict_id.get(event_nin_file)
        event = (
            service.events()
            .get(calendarId=GOOGLE_CALENDAR_ID, eventId=eventId)
            .execute()
        )
        event["colorId"] = "11"  # red
        event["description"] = f"**event not in source file**\n {event['description']}"
        service.events().update(
            calendarId=GOOGLE_CALENDAR_ID, eventId=event["id"], body=event
        ).execute()


def synch_event():
    upsert_events(read_new_events())

# def get_colors():
#     service = get_google_api_service()
#     colors = service.colors().get().execute()

#     # Print available calendarListEntry colors.
#     for id, color in colors['calendar'].iteritem():
#         print('colorId: %s' % id)



if __name__ == "__main__":
    # get_colors()
    upsert_events(read_new_events())


