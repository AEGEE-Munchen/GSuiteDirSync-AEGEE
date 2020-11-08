#!/usr/bin/env python3

from aegee_directory import *

import argparse
import re

AEGEE_MUENCHEN_BODY_ID = 117
AEGEE_MUENCHEN_MEMBERS_GROUP = 'members@aegee-muenchen.de'


def parse_args() -> argparse.Namespace:
    """Parses the script arguments.
    """
    parser = argparse.ArgumentParser(description='Sync AEGEE-München\'s G-Suite Directory')
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
    gsuite_users = gsuite_load_group(gsuite_creds, AEGEE_MUENCHEN_MEMBERS_GROUP)

    # Match users from MyAEGEE and members@aegee-muenchen.de
    missing = []
    for member in myaegee_members:
        email_match = any([user for user in gsuite_users if member['user']['email'] == user['email'] or re.sub('@gmail\.com$', '@googlemail.com', member['user']['email']) == user['email']])
        if not email_match:
            missing.append(member)
    print(f'{len(myaegee_members) - len(missing)}/{len(myaegee_members)} MyAEGEE users matched')
    print('')
    if len(missing) > 0:
        print(f'Members missing from {AEGEE_MUENCHEN_MEMBERS_GROUP}:')
        print('\n'.join(map(lambda m: f'* {m["user"]["first_name"]} {m["user"]["last_name"]} ({m["user"]["email"]})', missing)))
    else:
        print(f'All MyAEGEE users included in {AEGEE_MUENCHEN_MEMBERS_GROUP}!')


if __name__ == '__main__':
    main()
