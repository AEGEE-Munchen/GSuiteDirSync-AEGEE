#!/usr/bin/env python3

from collections.abc import Iterable
import argparse
import requests
import sys

AEGEE_MUENCHEN_BODY_ID = 117

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Sync AEGEE-München\'s G-Suite Directory')
    parser.add_argument('--username', dest='myaegee_user', help='MyAEGEE Username')
    parser.add_argument('--password', dest='myaegee_pass', help='MyAEGEE Password')
    parser.add_argument('--body-id', dest='myaegee_body_id', help='MyAEGEE Antenna Body ID', type=int, default=AEGEE_MUENCHEN_BODY_ID)
    args = parser.parse_args()
    return args

# Login to MyAEGEE
def myaegee_login(username: str, password: str) -> str:
    LOGIN_ENDPOINT = 'https://my.aegee.eu/api/core/login'
    login = requests.post(LOGIN_ENDPOINT, json={'username': username, 'password': password}).json()
    if not login['success']:
        raise Exception(f'Login error: {login["message"]}')
    return login['access_token']

# Fetch members from MyAEGEE
def myaegee_get_members(body_id: int, access_token: str) -> Iterable:
    MEMBERS_ENDPOINT = f'https://my.aegee.eu/api/core/bodies/{body_id}/members'
    members = requests.get(MEMBERS_ENDPOINT, headers={'Content-Type': 'application/json', 'X-Auth-Token': access_token}).json()
    if not members['success']:
        raise Exception(f'Error fetching members: {members["message"]}')
    return members['data']

def main() -> None:
    args = parse_args()
    access_token = myaegee_login(args.myaegee_user, args.myaegee_pass)
    members = myaegee_get_members(args.myaegee_body_id, access_token)
    print(members)

if __name__ == '__main__':
    main()
