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
from pytodoist import todoist
from trello import TrelloClient
import pandas as pd

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

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

    utc_now = datetime.datetime.now(timezone('UTC'))
    jst_now = utc_now.astimezone(timezone('Asia/Tokyo'))
    jst_now_iso=jst_now.isoformat()
    jst_next_week_iso=(jst_now + datetime.timedelta(days=7)).isoformat()

    # 今後5件を取得
    # eventsResult = service.events().list(
    #     calendarId='primary', timeMin=jst_now_iso, maxResults=5, singleEvents=True,
    #     orderBy='startTime').execute()

    # これから1週間のカレンダーを取得
    print("カレンダーを取得中..")
    eventsResult = service.events().list(
        calendarId='primary', timeMin=jst_now_iso, timeMax=jst_next_week_iso, singleEvents=True,
        orderBy='startTime').execute()
    events_gcal = eventsResult.get('items', [])


    # google calendarから取得したtodoをtodoistに追加
    df=pd.read_csv("secret/secret.csv")
    id_todoist=df["todoist_id"][0]
    password_todoist=df["todoist_password"][0]
    user = todoist.login(id_todoist, password_todoist)

    projects_todoist = user.get_projects()

    inbox_todoist = user.get_project('Inbox')


    tasks =[]
    if not events_gcal:
        print('No upcoming events found.')
    for event in events_gcal:
        print(event['start'].get('date'),event['summary'])

    print("todoistに追加中..")
    for i, event in enumerate(events_gcal):
        summary = event['summary']
        if "todo" in summary:
            # calendarでの開始時間(start)のdateをdue dateとする
            date = event['start'].get('date')
            print(summary, date)
            # todoistに追加
            # tasks.append(inbox_todoist.add_task(summary, date=date))

    # google calendarから取得したtodoをtrelloに追加
    df=pd.read_csv("secret/secret.csv")
    TRELLO_API_KEY=df["trello_key"][0]
    TRELLO_SECRET=df["trello_secret"][0]
    TRELLO_TOKEN=df["trello_token"][0]

    client = TrelloClient(TRELLO_API_KEY, token=TRELLO_TOKEN)
    # ボードの作成
    created_board = client.add_board("Create from Google Calendar")
    target_board_id = created_board.id

    # list idの取得
    lists = created_board.all_lists()

    print("trelloで追加するリストの選択..")
    for l in lists:
        print("list id: {}".format(l.id))
        print("list name: {}".format(l.name))
        if l.name == "To Do":
            target_list_id = l.id

    # カードを追加するボードやリストを決める
    board = client.get_board(target_board_id)
    target_list = board.get_list(target_list_id)

    print("trelloに追加中..")
    for i, event in enumerate(events_gcal):
        summary = event['summary']
        if "todo" in summary:
            due_datetime = datetime.datetime.strptime(event['start'].get('date'), '%Y-%m-%d') #str->datetime
            print(due_datetime)
            created_card = target_list.add_card(summary)
            created_card.set_due(due_datetime)

if __name__ == '__main__':
    main()
