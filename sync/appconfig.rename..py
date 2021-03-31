#Calendar/Mail parameters
GOOGLE_CALENDAR_ID = "YOURCALENDARID@group.calendar.google.com"
#GOOGLE_CALENDAR_ID = "primary"
EMAIL_FROM = "FROM"
EMAIL_TO = "TO"
TIMEZONE = "America/New_York"


#File parameters
FILEPATH = "PATHTOFILE/change_request.csv"
COLUMN_DELIMETER = ','
TEXT_SEPARATOR = '"'
DATE_FORMAT= "%Y-%m-%d %H:%M:%S"


# used from snowsoftware extract.
# replace with your own file
# 'Google Calendar column' : 'Your column'
COLUMN_MAPPING  = {
    'summary': 'u_customer_concerned'
    ,'location': 'number'
    ,'start_datetime_str': 'start_date'
    ,'end_datetime_str': 'end_date'
    ,'description': 'short_description'
    ,'gid': 'number'
}


ICS_SYNCH_DAYS = 30
ICS_DATA_FILENAME = 'outlook.ics'