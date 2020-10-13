#!/usr/bin/env python3

from collections.abc import Iterable
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import argparse
import os.path
import pickle
import requests
import sys

AEGEE_MUENCHEN_BODY_ID = 117

"""Parses the script arguments.
"""
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Sync AEGEE-München\'s G-Suite Directory')
    parser.add_argument('--username', dest='myaegee_user', help='MyAEGEE Username')
    parser.add_argument('--password', dest='myaegee_pass', help='MyAEGEE Password')
    parser.add_argument('--body-id', dest='myaegee_body_id', help='MyAEGEE Antenna Body ID', type=int, default=AEGEE_MUENCHEN_BODY_ID)
    parser.add_argument('--credentials-file', dest='gsuite_credfile', help='G-Suite JSON credentials', default='credentials.json')
    args = parser.parse_args()
    return args

"""Logs into MyAEGEE.
Returns the access token required to authenticate API calls.
"""
def myaegee_login(username: str, password: str) -> str:
    LOGIN_ENDPOINT = 'https://my.aegee.eu/api/core/login'
    login = requests.post(LOGIN_ENDPOINT, json={'username': username, 'password': password}).json()
    if not login['success']:
        raise Exception(f'Login error: {login["message"]}')
    return login['access_token']

"""Fetches all the members from a given body.
Returns a list of members who belong to body identified with `body_id`.
"""
def myaegee_get_members(body_id: int, access_token: str) -> Iterable:
    MEMBERS_ENDPOINT = f'https://my.aegee.eu/api/core/bodies/{body_id}/members'
    members = requests.get(MEMBERS_ENDPOINT, headers={'Content-Type': 'application/json', 'X-Auth-Token': access_token}).json()
    if not members['success']:
        raise Exception(f'Error fetching members: {members["message"]}')
    return members['data']

"""Loads the G-Suite authentication.
"""
def gsuite_auth(credentials_file: str) -> None:
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/admin.directory.user']
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
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

"""Loads the G-Suite Directory users.
Returns a list of G-Suite users who belong to the domain.
"""
def gsuite_load_directory(creds) -> Iterable:
    service = build('admin', 'directory_v1', credentials=creds)

    # Call the Admin SDK Directory API
    results = service.users().list(customer='my_customer', maxResults=10, orderBy='email').execute()
    return results.get('users', [])

def main() -> None:
    args = parse_args()

    # Get MyAEGEE body members
    myaegee_access_token = myaegee_login(args.myaegee_user, args.myaegee_pass)
    myaegee_members = myaegee_get_members(args.myaegee_body_id, myaegee_access_token)

    # Get G-Suite Directory users
    gsuite_creds = gsuite_auth(args.gsuite_credfile)
    gsuite_users = gsuite_load_directory(gsuite_creds)

    # Match users from MyAEGEE and G-Suite
    matched = []
    for member in myaegee_members:
        print(f'Processing {member["user"]["first_name"]} {member["user"]["last_name"]}...')
        user_matches = [user for user in gsuite_users if any(member['user']['email'] == email for email in user['emails'])]
        matched.append(member['user']['email'])
    print(matched)

if __name__ == '__main__':
    main()
