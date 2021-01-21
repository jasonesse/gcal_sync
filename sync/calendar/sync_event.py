from datetime import datetime as dt, timedelta
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import csv
import time
import logging
from sync.notification.send_gmail import notify
from sync.appconfig import FILEPATH, GOOGLE_CALENDAR_ID, DATE_FORMAT, COLUMN_MAPPING


class FileSpec:
    def __init__(self, summary, location, start_datetime_str, end_datetime_str, description, gid):
        self.summary = summary
        self.location = location
        self.start_datetime_str = start_datetime_str
        self.end_datetime_str = end_datetime_str
        self.description = description
        self.gid = gid
        self.colorId = "5"  # default color

    @property
    def id(self):
        return self.gid.lower()

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
        return f"summary:{self.summary},gid:{self.gid},StartDate:{self.start_datetime_str},EndDate:{self.end_datetime_str}"


def get_file_date_metadata():
    file_modified_date = dt.strptime( time.ctime(os.path.getmtime(FILEPATH)), "%a %b %d %H:%M:%S %Y")

    sync_dt = "1900-01-01 00:00:00"
    if os.path.exists("sync.log"):
        with open("sync.log", "r") as log:
            last_sync = log.read()
            sync_dt = last_sync or sync_dt #if empty file take sync_dt
    last_sync_date = dt.strptime(sync_dt, "%Y-%m-%d %H:%M:%S")

    if last_sync_date > dt.now():
        notify(f'Check the sync/calendar/sync.log file; the date should be in the past. No events will be processed until {last_sync_date}')

    return file_modified_date, last_sync_date 

def read_file_events(column_mapping=COLUMN_MAPPING):

    file_events = []

    #does file exist?
    os.chdir(os.path.dirname(os.path.abspath( __file__ )))
    file_exists = os.path.exists(FILEPATH)

    if not file_exists:
        return file_events

    file_modified_date, last_sync_date  = get_file_date_metadata()
    
    if file_modified_date <= last_sync_date:
        return file_events

    with open(FILEPATH, "r", encoding="UTF-8") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')

        for id, row in enumerate(reader):
            if id == 0:
                # get header indices.
                try:
                    summary = row.index(column_mapping.get("summary"))
                    location = row.index(column_mapping.get("location"))
                    start_datetime_str = row.index(
                        column_mapping.get("start_datetime_str")
                    )
                    end_datetime_str = row.index(column_mapping.get("end_datetime_str"))
                    description = row.index(column_mapping.get("description"))
                    gid = row.index(column_mapping.get("gid"))
                except ValueError as e:
                    raise ValueError(
                        f"Check COLUMN_MAPPING in appconfig.py. Column name not found in {FILEPATH}: {e}"
                    )

            if id > 0:
                file_event = FileSpec(
                    summary=row[summary],
                    location=row[location],
                    start_datetime_str=row[start_datetime_str],
                    end_datetime_str=row[end_datetime_str],
                    description=row[description],
                    gid=row[gid],
                )
                file_events.append(file_event)

    return validate_file_events(file_events)


def validate_file_events(file_events):

    valid_file_events = []
    error_msgs = []

    for s in file_events:
        if s.start_datetime_str == "" and s.end_datetime_str == "":
            err_msg = f"{s.gid} : Both start and end dates are empty."
            logging.error(err_msg)
            error_msgs.append(err_msg)
        elif s.gid == "":
            err_msg = f"No {COLUMN_MAPPING.get('gid')} found for event. Check source file."
            logging.error(err_msg)
            error_msgs.append(err_msg)
        else:
            valid_file_events.append(s)

    if len(error_msgs) > 0:
        msg = f"Sync Errors ({FILEPATH}):" + "\n" + "\n".join(error_msgs)
        notify(msg)


    return valid_file_events

def auth():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    os.chdir(os.path.dirname(os.path.abspath( __file__ )))

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
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", ["https://www.googleapis.com/auth/calendar"])
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def get_google_cal_events(
    maxResults=100, timeMin=dt.utcnow().isoformat() + "Z"
):
    service = auth()

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


def calc_google_merge(file_events):

    file_ids = []

    min_start_date = get_min_start_date(file_events)
    google_cal_events = get_google_cal_events(timeMin=min_start_date)
    ids_to_update = []
    gcal_nin_file = []
    ids_to_create = []

    for e in file_events:
        file_ids.append(e.id)

    if len(google_cal_events) == 0:  # brand new calendar
        ids_to_create = file_ids
        return ids_to_update, ids_to_create, gcal_nin_file

    # delete all google cal events found in file to refresh
    gcal_ids = []
    for gcal_event in google_cal_events:
        gcal_id = gcal_event.get("id")
        gcal_ids.append(gcal_id)
        for e in file_ids:
            if e == gcal_id:
                ids_to_update.append(e)

    gcal_nin_file = list(set(gcal_ids) - set(file_ids))
    ids_to_create = list(set(file_ids) - set(ids_to_update))

    return ids_to_update, ids_to_create, gcal_nin_file


def get_event_body(event):
    return {
        "id": event.id,
        # "summary": f"{s.summary} ({s.gid})",
        "summary": event.summary,
        "location": event.location,
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


def process_events(file_events):

    if len(file_events) <= 0:
        return
    
    service = auth()
    ids_to_update, ids_to_create, gcal_nin_file = calc_google_merge(file_events)

    for event in file_events:
        event = handle_missing_dates(event)

        if event.id in ids_to_update:
            update_event(event, service)
        if event.id in ids_to_create:
            insert_event(event, service)

    for gcal_id in gcal_nin_file:
        flag_event(gcal_id, service)

def insert_event(s, service):

    try:
        service.events().insert(
            calendarId=GOOGLE_CALENDAR_ID, body=get_event_body(s)
        ).execute()

    except Exception as e:
        logging.error(f"Event details: {s}. Import failed: {e}.")

    logging.debug(f"{s.id} created")


def update_event(s, service):

    event = get_event_body(s)
    service.events().update(
        calendarId=GOOGLE_CALENDAR_ID, eventId=s.id, body=event
    ).execute()
    logging.debug(f"{s.id} event updated")


def flag_event(id, service):

    event = service.events().get(calendarId=GOOGLE_CALENDAR_ID, eventId=id).execute()
    event["colorId"] = "11"  # red
    event['description'] = event['description'].replace('**event not in source file**\n', '')
    event["description"] = f"**event not in source file**\n {event['description']}"
    event["summary"] = '*' + event["summary"]
    service.events().update(calendarId=GOOGLE_CALENDAR_ID, eventId=event["id"], body=event).execute()


def get_min_start_date(file_events):

    start_dates = [
        dt.strptime(s.start_datetime_str, DATE_FORMAT)
        for s in file_events
        if s.start_date_str != ""
    ]

    try:
        min_start_date = min(start_dates)
    except:
        min_start_date = dt.now()
    return min_start_date


def calc_missing_date_str(dt_str: str, hours: int, fmt=DATE_FORMAT) -> str:
    date = dt.strptime(dt_str, fmt)
    return dt.strftime(date + timedelta(hours=hours), DATE_FORMAT)


def handle_missing_dates(s):
    if s.start_datetime_str == "":
        s.start_datetime_str = calc_missing_date_str(
            dt_str=s.end_datetime_str, hours=-1
        )
        s.colorId = "6"
        s.description = "**start date missing**\n" + s.description
        s.summary = '*' + s.summary

    if s.end_datetime_str == "":
        s.end_datetime_str = calc_missing_date_str(dt_str=s.start_datetime_str, hours=1)
        s.colorId = "6"
        s.description = "**end date missing**\n" + s.description
        s.summary = '*' + s.summary
    return s

def log_file_date():
    os.chdir(os.path.dirname(os.path.abspath( __file__ )))
    file_modified_date = dt.strptime( time.ctime(os.path.getmtime(FILEPATH)), "%a %b %d %H:%M:%S %Y")
    
    with open("sync.log", "w") as log:
        log.write(dt.strftime(file_modified_date, "%Y-%m-%d %H:%M:%S"))

def synch_calendar():
    events = read_file_events()
    if events:
        process_events(events)
        log_file_date()


# def get_colors():
#     service = get_google_api_service()
#     colors = service.colors().get().execute()

#     # Print available calendarListEntry colors.
#     for id, color in colors['calendar'].iteritem():
#         print('colorId: %s' % id)


if __name__ == "__main__":
    # get_colors()
    synch_calendar()
