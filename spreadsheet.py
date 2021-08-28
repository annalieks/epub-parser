import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class Spreadsheet:
    scopes: list = ['https://www.googleapis.com/auth/spreadsheets']
    current_row: int = 0

    def __init__(self, id, page, range):
        self.id = id
        self.page = page
        self.range = range
        self.credentials = None
        self.connect()
        self.service = build('sheets', 'v4', credentials=self.credentials)

    def connect(self):
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.credentials = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.scopes)
                self.credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.credentials, token)

    def append(self, rows, value_input_option='RAW'):
        data = {'values': rows}
        return self.service.spreadsheets().values().append(spreadsheetId=self.id,
                                                          range=self.range,
                                                          valueInputOption=value_input_option,
                                                          body=data).execute()

    def write(self, rows, value_input_option='RAW'):
        data = {'values': rows}
        return self.service.spreadsheets().values().write(spreadsheetId=self.id,
                                                          range=self.range,
                                                          valueInputOption=value_input_option,
                                                          body=data).execute()
