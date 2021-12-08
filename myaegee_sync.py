#!/usr/bin/env python3

from aegee_directory import *
from difflib import SequenceMatcher

import argparse
import re

AEGEE_MUENCHEN_BODY_ID = 117
AEGEE_MUENCHEN_MEMBERS_GROUP = 'members@aegee-muenchen.de'
EXTRA_EXCLUDED = [
    'admin@aegee-muenchen.de',
    'events@aegee-muenchen.de',
    'externalrelations@aegee-muenchen.de',
    'internalrelations@aegee-muenchen.de',
    'it@aegee-muenchen.de',
    'president@aegee-muenchen.de',
    'secretary@aegee-muenchen.de',
    'treasurer@aegee-muenchen.de'
]


def parse_args() -> argparse.Namespace:
    """Parses the script arguments.
    """
    parser = argparse.ArgumentParser(description='Sync AEGEE-München\'s G-Suite Directory')
    parser.add_argument('--username', dest='myaegee_user', help='MyAEGEE Username', required=True)
    parser.add_argument('--password', dest='myaegee_pass', help='MyAEGEE Password', required=True)
    parser.add_argument('--body-id', dest='myaegee_body_id', help='MyAEGEE Antenna Body ID', type=int, default=AEGEE_MUENCHEN_BODY_ID)
    parser.add_argument('--credentials-file', dest='gsuite_credfile', help='G-Suite JSON credentials', default='credentials.json')
    subparsers = parser.add_subparsers(title='subcommands', description='Available subcommands', required=True)
    parser_members_sync = subparsers.add_parser('members-sync')
    parser_actives_sync = subparsers.add_parser('actives-sync')
    parser_members_sync.set_defaults(func=members_sync)
    parser_actives_sync.set_defaults(func=actives_sync)
    args = parser.parse_args()
    return args


def members_sync(args: argparse.Namespace) -> None:
    """Prints differences between members list from MyAEGEE and members@aegee-muenchen.de (missing and extra emails).
    """
    # Get MyAEGEE body members
    myaegee_access_token = myaegee_login(args.myaegee_user, args.myaegee_pass)
    myaegee_members = myaegee_get_members(args.myaegee_body_id, myaegee_access_token)

    # Get G-Suite Directory users
    gsuite_creds = gsuite_auth(args.gsuite_credfile)
    gsuite_users = gsuite_load_group(gsuite_creds, AEGEE_MUENCHEN_MEMBERS_GROUP)

    # Find users from MyAEGEE missing from the G-Suite group
    missing: List[MyAEGEEMember] = []
    for member in myaegee_members:
        is_in_group = any([user for user in gsuite_users if member.user.email == user['email'] or re.sub('@gmail\.com$', '@googlemail.com', member.user.email) == user['email']])
        if not is_in_group:
            missing.append(member)
    if len(missing) > 0:
        print(f'Members missing from {AEGEE_MUENCHEN_MEMBERS_GROUP} (matched {len(myaegee_members) - len(missing)}/{len(myaegee_members)} members):')
        print('\n'.join(map(lambda m: f'* {m.user.first_name} {m.user.last_name} ({m.user.email})', missing)))
    else:
        print(f'All MyAEGEE users included in {AEGEE_MUENCHEN_MEMBERS_GROUP}!')
    print('')

    # Find extra users in the G-Suite group which are not in MyAEGEE
    extra = []
    for user in gsuite_users:
        if user["email"] not in EXTRA_EXCLUDED:
            is_in_myaegee = any([member for member in myaegee_members if member.user.email == user['email'] or re.sub('@gmail\.com$', '@googlemail.com', member.user.email) == user['email']])
            if not is_in_myaegee:
                extra.append(user)
    if len(extra) > 0:
        print(f'Extra users in {AEGEE_MUENCHEN_MEMBERS_GROUP} (matched {len(gsuite_users) - len(extra)}/{len(gsuite_users)} users):')
        print('\n'.join(map(lambda u: f'* {u["email"]}', extra)))
    else:
        print(f'No extra users in {AEGEE_MUENCHEN_MEMBERS_GROUP}!')


def actives_sync(args: argparse.Namespace) -> None:
    """Prints the list of MyAEGEE members without a G-Suite account.
    """
    # Get MyAEGEE body members
    myaegee_access_token = myaegee_login(args.myaegee_user, args.myaegee_pass)
    myaegee_members = myaegee_get_members(args.myaegee_body_id, myaegee_access_token)

    # Get G-Suite Directory users
    gsuite_creds = gsuite_auth(args.gsuite_credfile)
    gsuite_users = gsuite_load_directory(gsuite_creds)

    # Match users from MyAEGEE and G-Suite
    missing: List[MyAEGEEMember] = []
    for member in myaegee_members:
        email_match = any([user for user in gsuite_users if any(member.user.email == email['address'] for email in user['emails'])])
        name_match = any([user for user in gsuite_users if SequenceMatcher(None, f'{member.user.first_name} {member.user.last_name}', user['name']['fullName']).ratio() > 0.9])
        if not email_match and not name_match:
            missing.append(member)
    print(f'{len(myaegee_members) - len(missing)}/{len(myaegee_members)} MyAEGEE users matched')
    print('')
    print('Members without G-Suite account:')
    print('\n'.join(map(lambda m: f'* {m.user.first_name} {m.user.last_name} ({m.user.email})', missing)))


def main() -> None:
    args = parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
