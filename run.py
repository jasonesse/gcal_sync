from model.readers.csv_reader import CsvEventReader
from model.readers.mssql_reader import MssqlEventReader
import sync.appconfig as config

reader = None

if config.READER == 'CSV':
    reader = CsvEventReader()
elif config.READER == 'MSSQL':
    reader = MssqlEventReader()

from sync.calendar.sync_event import synch_calendar
synch_calendar(reader)