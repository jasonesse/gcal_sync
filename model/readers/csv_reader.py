import os
import csv
import sync.appconfig as config

from model.readers.event_reader import EventReader
from datetime import datetime as dt
import time

from sync.notification.send_gmail import notify
from model.event_spec import EventSpec

class CsvEventReader(EventReader):

    def get_file_date_metadata(self, path):

        os.chdir(path)
        
        file_modified_date = dt.strptime( time.ctime(os.path.getmtime(config.FILEPATH)), "%a %b %d %H:%M:%S %Y")

        sync_dt = "1900-01-01 00:00:00"
        if os.path.exists("sync.log"):
            with open("sync.log", "r") as log:
                last_sync = log.read()
                sync_dt = last_sync or sync_dt
        last_sync_date = dt.strptime(sync_dt, "%Y-%m-%d %H:%M:%S")

        if last_sync_date > dt.now():
            notify(f'Check the sync/calendar/sync.log file; the date should be in the past. No events will be processed until {last_sync_date}')

        return file_modified_date, last_sync_date 


    def read_events(self, path):

        event_specs = []

        os.chdir(os.path.dirname(os.path.abspath( __file__ )))
        file_exists = os.path.exists(config.FILEPATH)

        if not file_exists:
            return event_specs

        file_modified_date, last_sync_date  = self.get_file_date_metadata(path)
        
        if file_modified_date <= last_sync_date:
            return event_specs

        with open(config.FILEPATH, "r", encoding="UTF-8") as f:
            reader = csv.reader(f, delimiter=config.COLUMN_DELIMETER, quotechar=config.TEXT_SEPARATOR)

            for row_idx, row_data in enumerate(reader):
                if row_idx == 0:
                    # get header indices.
                    try:
                        summary = row_data.index(config.COLUMN_MAPPING.get("summary"))
                        location = row_data.index(config.COLUMN_MAPPING.get("location"))
                        start_datetime_str = row_data.index(
                            config.COLUMN_MAPPING.get("start_datetime_str")
                        )
                        end_datetime_str = row_data.index(config.COLUMN_MAPPING.get("end_datetime_str"))
                        description = row_data.index(config.COLUMN_MAPPING.get("description"))
                        gid = row_data.index(config.COLUMN_MAPPING.get("gid"))
                    except ValueError as e:
                        raise ValueError(
                            f"Check config.COLUMN_MAPPING in appconfig.py. Column name not found in {config.FILEPATH}: {e}"
                        )

                if row_idx > 0:
                    event_spec = EventSpec(
                        summary=row_data[summary],
                        location=row_data[location],
                        start_datetime_str=row_data[start_datetime_str],
                        end_datetime_str=row_data[end_datetime_str],
                        description=row_data[description],
                        gid=row_data[gid],
                    )
                    event_specs.append(event_spec)

        return self.validate_events(event_specs)

    def log_sync_date(self, path):
        os.chdir(path)
        file_modified_date = dt.strptime( time.ctime(os.path.getmtime(config.FILEPATH)), "%a %b %d %H:%M:%S %Y")
        
        with open("sync.log", "w") as log:
            log.write(dt.strftime(file_modified_date, "%Y-%m-%d %H:%M:%S"))