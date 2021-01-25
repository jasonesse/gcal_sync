from model.readers.event_reader import EventReader
from model.event_spec import EventSpec
import sync.appconfig as config
import pyodbc 
from datetime import datetime as dt
import hashlib
import os

class MssqlEventReader(EventReader):
    def read_events(self, path):

        event_specs = []
        cnxn = pyodbc.connect(config.DB_CONNECTION_STRING)
        cursor = cnxn.cursor()
        cursor.execute(
            f"SELECT DISTINCT {config.DB_COLUMN_MAPPING.get('summary')} \
            ,{config.DB_COLUMN_MAPPING.get('location')}\
            ,{config.DB_COLUMN_MAPPING.get('start_datetime_str')}\
            ,{config.DB_COLUMN_MAPPING.get('end_datetime_str')}\
            ,{config.DB_COLUMN_MAPPING.get('description')}\
            ,{config.DB_COLUMN_MAPPING.get('gid')}\
            from telecom.event_data;") 
        row = cursor.fetchone() 
        while row:
            gen_gid = ''
            if config.GENERATE_GCAL_ID:
                str_id = '' or str(row[5])

                #default title name in gcal for missing event titles
                str_summary = row[0] or '(No title)'

                #unique key composed of title and original gid
                str_to_hash = f"{str_id}{str_summary}"
                gen_gid = hashlib.sha224(str.encode(str_to_hash)).hexdigest()

            gid = '' if not row[5] else row[5]
            event_spec = EventSpec(
                summary = row[0]
                ,location = str(row[1])
                ,start_datetime_str = dt.strftime(row[2], config.DATE_FORMAT) if row[2] else ''
                ,end_datetime_str =  dt.strftime(row[3], config.DATE_FORMAT) if row[3] else ''
                ,description = row[4]
                ,gid = gen_gid or gid
            )
            event_specs.append(event_spec)
            row = cursor.fetchone()

        return self.validate_events(event_specs)

    def log_sync_date(self, path):
        os.chdir(path)
        file_modified_date = dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")
        
        with open("sync.log", "w") as log:
            log.write(file_modified_date)

if __name__== '__main__':
    reader = MssqlEventReader()
    reader.read_events()