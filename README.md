**Utility to push csv data to Google Calendar via its API.**

Syncs the following Google Calendar fields:

* summary
* location
* description
* start
* end
* colorId

Uses a default color for events, and color codes them if:
* event is no longer in the file
* event's start date or end date missing


**Instructions**
1. Enable Google Calendar API (https://developers.google.com/calendar/quickstart/python) as a Desktop application.
2. Rename appconfig.rename.py to appconfig.py
In appconfig.py,
3. Optionally create a calendar and get it's ID. If using main accounts calendar use "primary"
4. Use the mapping to fill out the names in your csv file corresponding to supported Google Calendar fields.

Email support coming soon.