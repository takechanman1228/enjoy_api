from __future__ import print_function
import httplib2
import os
import pprint

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

from pytz import timezone
import datetime
# from datetime import datetime
from pytodoist import todoist
import pandas as pd

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.
/
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    # now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    utc_now = datetime.datetime.now(timezone('UTC'))
    jst_now = utc_now.astimezone(timezone('Asia/Tokyo'))
    jst_now_iso=jst_now.isoformat()
    jst_next_week_iso=(jst_now + datetime.timedelta(days=7)).isoformat()
    print(utc_now)
    print(jst_now)
    print(jst_now_iso)
    print(jst_next_week_iso)
    # now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    # 今後5件を取得
    # eventsResult = service.events().list(
    #     calendarId='primary', timeMin=jst_now_iso, maxResults=5, singleEvents=True,
    #     orderBy='startTime').execute()

    # これから1週間のカレンダーを取得
    eventsResult = service.events().list(
        calendarId='primary', timeMin=jst_now_iso, maxResults=5, singleEvents=True,
        orderBy='startTime').execute()
    events_gcal = eventsResult.get('items', [])


    # todoist
    df=pd.read_csv("secret/secret.csv")
    id_todoist=df["todoist_id"][0]
    password_todoist=df["todoist_password"][0]
    user = todoist.login(id_todoist, password_todoist)

    projects_todoist = user.get_projects()

    inbox_todoist = user.get_project('Inbox')
    # task=[0] * 15
    tasks =[]
    if not events_gcal:
        print('No upcoming events found.')
    for i, event in enumerate(events_gcal):
        summary = event['summary']
        # if "todo" in summary:
        if "P" in summary: #test
            date = event['start'].get('date')

            # todoistに追加
            tasks.append(inbox_todoist.add_task(summary, date=date))
            print(tasks[i].content, tasks[i].due_date)

if __name__ == '__main__':
    main()
