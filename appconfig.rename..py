# rename file to appconfig.py
FILEPATH = "PATHTOFILE/change_request.csv"
GOOGLE_CALENDAR_ID = "YOURCALENDARID@group.calendar.google.com"
# GOOGLE_CALENDAR_ID = "primary"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
EMAIL_FROM = "FROM"
EMAIL_TO = "TO"

# used from snowsoftware extract.
# replace with your own file
COLUMN_MAPPING  = {
    'summary': 'u_customer_concerned'
    ,'location': 'number'
    ,'start_datetime_str': 'start_date'
    ,'end_datetime_str': 'end_date'
    ,'description': 'short_description'
    ,'gid': 'number'
}