
import sync.appconfig as config

reader = None

if config.READER == 'CSV':
    from model.readers.csv_reader import CsvEventReader
    reader = CsvEventReader()
elif config.READER == 'MSSQL':
    from model.readers.mssql_reader import MssqlEventReader
    reader = MssqlEventReader()
elif config.READER == 'ICS':
    from model.readers.ics_reader import ICSEventReader
    reader = ICSEventReader()

from sync.calendar.sync_event import synch_calendar
synch_calendar(reader)