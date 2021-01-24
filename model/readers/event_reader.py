from abc import ABC
from abc import abstractmethod
import logging

from sync.notification.send_gmail import notify
import sync.appconfig as config 

logging_format = "%(asctime)s (%(levelname)s): %(message)s"
logging.basicConfig(level=logging.INFO, format=logging_format)


class EventReader(ABC):
    def __init__(self):
        pass

    def connect(self):
        pass

    @abstractmethod
    def read_events(self):
        pass

    @abstractmethod
    def log_sync_date(self):
        pass


    #def validate_events(self, event_specs: list[EventSpec]) -> list[EventSpec]:
    def validate_events(self, event_specs):
        valid_event_specs = []
        error_msgs = []

        for event_spec in event_specs:
            if event_spec.start_datetime_str == "" and event_spec.end_datetime_str == "":
                err_msg = f"{event_spec.gid} : Both start and end dates are empty."
                logging.error(err_msg)
                error_msgs.append(err_msg)
            elif event_spec.gid == "":
                id_column_name = config.COLUMN_MAPPING.get('gid')
                err_msg = f"No {id_column_name} found for event. Check source file."
                logging.error(err_msg)
                error_msgs.append(err_msg)
            else:
                valid_event_specs.append(event_spec)

        if len(error_msgs) > 0:
            msg = f"Sync Errors ({config.FILEPATH}):" + "\n" + "\n".join(error_msgs)
            notify(msg)


        return valid_event_specs