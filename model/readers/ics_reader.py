import os
import csv
import sync.appconfig as config

from model.readers.event_reader import EventReader
from datetime import datetime as dt, timedelta
import time

from sync.notification.send_gmail import notify
from model.event_spec import EventSpec

from icalendar import Calendar, Event
import recurring_ical_events
from datetime import datetime
from pytz import UTC # timezone


class ICSEventReader(EventReader):
    def read_events(self, path):

        event_specs = []

        with open(f'{config.DEFAULT_DATA_PATH}/{config.ICS_DATA_FILENAME}','rb') as fp:
            data = fp.read()
        cal = Calendar.from_ical(data)
        now = datetime.now()
        
        for event in recurring_ical_events.of(cal).between(now, now + timedelta(config.ICS_SYNCH_DAYS)):
            try:
                title = event['SUMMARY'].to_ical().decode('utf-8')
            except:
                continue# title = 'N/A' #continue#title = event['DESCRIPTION'].to_ical().decode('utf-8').split('\\n')[0]

            event_spec = EventSpec(
                summary = title
                ,location = ''
                ,start_datetime_str = dt.strftime(event['DTSTART'].dt, config.DATE_FORMAT) if event['DTSTART'].dt else ''
                ,end_datetime_str =  dt.strftime(event['DTEND'].dt, config.DATE_FORMAT) if event['DTEND'].dt else ''
                ,description = title
                ,gid = f"{event['UID'].to_ical().decode('utf-8')[102:113]}{dt.strftime(event['DTSTART'].dt, '%d') if event['DTSTART'].dt else ''}" #last 10 chars of uid, with sequence for recurring support and day number to ensure unicity.
            )
            event_specs.append(event_spec)

        return self.validate_events(event_specs)

    def log_sync_date(self, path):
        os.chdir(path)
        file_modified_date = dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")
        
        with open("sync.log", "w") as log:
            log.write(file_modified_date)


# if __name__ == '__main__':
#     reader = ICSEventReader()
#     reader.read_events('test')