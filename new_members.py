#!/usr/bin/env python3

from difflib import SequenceMatcher

import argparse
from aegee_directory import *

AEGEE_MUENCHEN_BODY_ID = 117


def parse_args() -> argparse.Namespace:
    """Parses the script arguments.
    """
    parser = argparse.ArgumentParser(description='List AEGEE-München\'s members without a G-Suite account')
    parser.add_argument('--username', dest='myaegee_user', help='MyAEGEE Username')
    parser.add_argument('--password', dest='myaegee_pass', help='MyAEGEE Password')
    parser.add_argument('--body-id', dest='myaegee_body_id', help='MyAEGEE Antenna Body ID', type=int, default=AEGEE_MUENCHEN_BODY_ID)
    parser.add_argument('--credentials-file', dest='gsuite_credfile', help='G-Suite JSON credentials', default='credentials.json')
    args = parser.parse_args()
    return args


def main() -> None:
    args = parse_args()

    # Get MyAEGEE body members
    myaegee_access_token = myaegee_login(args.myaegee_user, args.myaegee_pass)
    myaegee_members = myaegee_get_members(args.myaegee_body_id, myaegee_access_token)

    # Get G-Suite Directory users
    gsuite_creds = gsuite_auth(args.gsuite_credfile)
    gsuite_users = gsuite_load_directory(gsuite_creds)

    # Match users from MyAEGEE and G-Suite
    missing = []
    for member in myaegee_members:
        email_match = any([user for user in gsuite_users if any(member['user']['email'] == email['address'] for email in user['emails'])])
        name_match = any([user for user in gsuite_users if SequenceMatcher(None, f'{member["user"]["first_name"]} {member["user"]["last_name"]}', user['name']['fullName']).ratio() > 0.9])
        if not email_match and not name_match:
            missing.append(member)
    print(f'{len(myaegee_members) - len(missing)}/{len(myaegee_members)} MyAEGEE users matched')
    print('')
    print('Members without G-Suite account:')
    print('\n'.join(map(lambda m: f'* {m["user"]["first_name"]} {m["user"]["last_name"]} ({m["user"]["email"]})', missing)))


if __name__ == '__main__':
    main()
