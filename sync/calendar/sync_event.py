import logging
import os.path
import time
from datetime import datetime as dt
from datetime import timedelta

import sync.appconfig as config
from model.readers.event_reader import EventReader
from sync.security.auth import get_service



def authorize():
    PATH = os.chdir(os.path.dirname(os.path.abspath( __file__ )))
    return get_service(
        path=os.path.dirname(os.path.abspath(__file__)),
        scope="https://www.googleapis.com/auth/calendar",
        build_name="calendar", 
        build_version="v3"
    )


def get_google_cal_events(
    max_results=100, timeMin=dt.utcnow().isoformat() + "Z"
):

    service = authorize()

    events_result = (
        service.events()
        .list(
            calendarId=config.GOOGLE_CALENDAR_ID,
            timeMin=timeMin.isoformat() + "Z",
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return events_result.get("items", [])


def calc_google_merge(event_specs):

    file_ids = []

    min_start_date = get_min_start_date(event_specs)
    google_cal_events = get_google_cal_events(timeMin=min_start_date)
    ids_to_update = []
    gcal_nin_file = []
    ids_to_create = []

    for e in event_specs:
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
            "timeZone": config.TIMEZONE,
        },
        "end": {
            "dateTime": f"{event.end_date_str}T{event.end_time_str}:00",
            "timeZone": config.TIMEZONE,
        },
        "colorId": event.colorId,
    }


def process_events(event_specs):

    if len(event_specs) == 0:
        return

    service = authorize()
    ids_to_update, ids_to_create, gcal_nin_file = calc_google_merge(event_specs)

    throttle_time = 2 if len(event_specs) > 10 else 0

    for event in event_specs:
        time.sleep(throttle_time)
        print(dt.now())
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
            calendarId=config.GOOGLE_CALENDAR_ID, body=get_event_body(s)
        ).execute()

    except Exception as e:
        logging.error(f"Event details: {s}. Import failed: {e}.")

    logging.debug(f"{s.id} created")


def update_event(s, service):

    event = get_event_body(s)
    service.events().update(
        calendarId=config.GOOGLE_CALENDAR_ID, eventId=s.id, body=event
    ).execute()
    logging.debug(f"{s.id} event updated")


def flag_event(id, service):

    event = service.events().get(calendarId=config.GOOGLE_CALENDAR_ID, eventId=id).execute()
    event["colorId"] = "11"  # red
    event['description'] = event['description'].replace('**event not in source file**\n', '')
    event["description"] = f"**event not in source file**\n {event['description']}"
    event["summary"] = f"*{event['summary']}"
    service.events().update(calendarId=config.GOOGLE_CALENDAR_ID, eventId=event["id"], body=event).execute()


def get_min_start_date(event_specs):

    for s in event_specs:
        print(s.start_date_str)

    start_dates = [
        dt.strptime(s.start_datetime_str, config.DATE_FORMAT)
        for s in event_specs
        if s.start_date_str != ""
    ]

    try:
        min_start_date = min(start_dates)
    except ValueError:
        min_start_date = dt.now()
    return min_start_date


def calc_missing_date_str(dt_str: str, hours: int, fmt=config.DATE_FORMAT) -> str:
    date = dt.strptime(dt_str, fmt)
    return dt.strftime(date + timedelta(hours=hours), config.DATE_FORMAT)


def handle_missing_dates(s):
    if s.start_datetime_str == "":
        s.start_datetime_str = calc_missing_date_str(
            dt_str=s.end_datetime_str, hours=-1
        )
        s.colorId = "6"
        s.description = "**start date missing**\n" + s.description
        s.summary = f"*{s.summary}"

    if s.end_datetime_str == "":
        s.end_datetime_str = calc_missing_date_str(dt_str=s.start_datetime_str, hours=1)
        s.colorId = "6"
        s.description = "**end date missing**\n" + s.description
        s.summary = f"*{s.summary}"
    return s



def synch_calendar(reader: EventReader):
    #events = get_event_specs()
    path=os.path.dirname(os.path.abspath( __file__ ))
    events = reader.read_events(path=path)
    if events:
        process_events(events)
        reader.log_sync_date(path=path)

# if __name__ == "__main__":
#     synch_calendar()