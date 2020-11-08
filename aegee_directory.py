from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from typing import List, Any

import os.path
import pickle
import requests


def myaegee_login(username: str, password: str) -> str:
    """Logs into MyAEGEE.
    Returns the access token required to authenticate API calls.
    """
    _LOGIN_ENDPOINT = 'https://my.aegee.eu/api/core/login'
    login = requests.post(_LOGIN_ENDPOINT, json={'username': username, 'password': password}).json()
    if not login['success']:
        raise Exception(f'Login error: {login["message"]}')
    return login['access_token']


def myaegee_get_members(body_id: int, access_token: str) -> List:
    """Fetches all the members from a given body.
    Returns a list of members who belong to body identified with `body_id`.
    """
    _MEMBERS_ENDPOINT = f'https://my.aegee.eu/api/core/bodies/{body_id}/members'
    members = requests.get(_MEMBERS_ENDPOINT, headers={'Content-Type': 'application/json', 'X-Auth-Token': access_token}).json()
    if not members['success']:
        raise Exception(f'Error fetching members: {members["message"]}')
    return members['data']


def gsuite_auth(credentials_file: str) -> Credentials:
    """Loads the G-Suite authentication.
    """
    # If modifying these scopes, delete the file token.pickle.
    _SCOPES = ['https://www.googleapis.com/auth/admin.directory.user', 'https://www.googleapis.com/auth/admin.directory.group.member.readonly']
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, _SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def gsuite_load_directory(creds: Any) -> List:
    """Loads the G-Suite Directory users.
    Returns a list of G-Suite users who belong to the domain.
    """
    service = build('admin', 'directory_v1', credentials=creds)

    # Call the Admin SDK Directory API
    results = service.users().list(customer='my_customer', orderBy='email').execute()
    return results.get('users', [])


def gsuite_load_group(creds: Any, group_email: str) -> List:
    """Loads the list of members of the inpuit group.
    Returns a list of emails that belong to the input group.
    """
    service = build('admin', 'directory_v1', credentials=creds)

    # Call the Admin SDK Directory API
    results = service.members().list(groupKey=group_email).execute()
    return results.get('members', [])
