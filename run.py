from model.readers.csv_reader import CsvEventReader

reader = CsvEventReader()

from sync.calendar.sync_event import synch_calendar
synch_calendar(reader)