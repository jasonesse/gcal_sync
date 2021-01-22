# gcal_sync

## Utility to push csv data to Google Calendar via its API

Syncs the following Google Calendar fields:

* summary
* location
* description
* start
* end
* colorId


## Decisions

If the start date is missing, or the end date is missing, the event will be one hour long relative to the one that's there.

If there is no id defined in the column mappings, or both dates are missing, **an e-mail notification** will be 
sent with the list of offending events.

The notification is powered by Google Gmail API.


#### Event Colors
Uses a default color* for events, and color codes them if:
* event is no longer in the file
* event's start date or end date missing


*_Note: If the calendar is shared to another user, the colors do not propagate. Stars prefix the title in the case of an issue with the event._

## Instructions

1. Install dependencies with `pip install -r requirements.txt`
2. Rename appconfig.rename.py to appconfig.py
3. Enable Google Calendar API (https://developers.google.com/calendar/quickstart/python) as a Desktop application. Place credentials.json in calendar folder.
4. Enable Google Gmail API (https://developers.google.com/gmail/api/quickstart/python) as a Desktop application. Place credentials.json in notification folder.


*In appconfig.py,*

3. Optionally create a calendar and get it's ID. If using main accounts calendar use "primary"
4. Use the mapping to fill out the names in your csv file corresponding to supported Google Calendar fields.
