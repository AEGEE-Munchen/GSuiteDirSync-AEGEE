#!/usr/bin/env python3

import argparse
import os
import re
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any, Dict, List

from gsuitedirsync_aegee.aegee_directory import (
    MyAEGEEMember,
    gsuite_auth,
    gsuite_load_directory,
    gsuite_load_group,
    myaegee_get_members,
    myaegee_login,
)

if TYPE_CHECKING:
    from gsuitedirsync_aegee.aegee_directory import GSuiteMember, GSuiteUser

AEGEE_MUENCHEN_BODY_ID = 117
AEGEE_MUENCHEN_MEMBERS_GROUP = 'members@aegee-muenchen.de'
AEGEE_MUENCHEN_ACTIVES_GROUP = 'actives@aegee-muenchen.de'
AEGEE_MUENCHEN_DOMAIN = 'aegee-muenchen.de'
EXTRA_EXCLUDED = [
    'admin@aegee-muenchen.de',
    'archive@aegee-muenchen.de',
    'events@aegee-muenchen.de',
    'european.affairs@aegee-muenchen.de',
    'externalrelations@aegee-muenchen.de',
    'info@aegee-muenchen.de',
    'internalrelations@aegee-muenchen.de',
    'it@aegee-muenchen.de',
    'publicrelations@aegee-muenchen.de',
    'president@aegee-muenchen.de',
    'projectmanager@aegee-muenchen.de',
    'secretary@aegee-muenchen.de',
    'su@aegee-muenchen.de',
    'treasurer@aegee-muenchen.de'
]


def parse_args() -> argparse.Namespace:
    """Parses the script arguments.
    """
    parser = argparse.ArgumentParser(description='Sync AEGEE-München\'s G-Suite Directory')
    parser.add_argument('--myaegee-user', dest='myaegee_user', help='MyAEGEE Username', default=os.environ.get('MYAEGEE_USER'))
    parser.add_argument('--myaegee-pass', dest='myaegee_pass', help='MyAEGEE Password', default=os.environ.get('MYAEGEE_PASS'))
    parser.add_argument('--body-id', dest='myaegee_body_id', help='MyAEGEE Antenna Body ID', type=int, default=AEGEE_MUENCHEN_BODY_ID)
    parser.add_argument('--credentials-file', dest='gsuite_credfile', help='G-Suite JSON credentials', default='credentials.json')
    subparsers = parser.add_subparsers(title='subcommands', description='Available subcommands', required=True)
    parser_members_sync = subparsers.add_parser('members-sync')
    parser_actives_sync = subparsers.add_parser('actives-sync')
    parser_members_sync.set_defaults(func=members_sync)
    parser_actives_sync.set_defaults(func=actives_sync)
    args = parser.parse_args()
    if not args.myaegee_user or not args.myaegee_pass:
        exit(parser.print_usage())
    return args


def print_users(users: List[MyAEGEEMember | Dict[str, Any]]):
    if len(users) > 0:
        if isinstance(users[0], MyAEGEEMember):
            sorted_users = sorted(users, key=lambda m: m.user.email)
            print('\n'.join(map(lambda m: f'* {m.user.first_name} {m.user.last_name} ({m.user.email})', sorted_users)))
        elif users[0]['kind'] == 'admin#directory#user':
            sorted_users = sorted(users, key=lambda u: u['primaryEmail'])
            print('\n'.join(map(lambda u: f"* {u['name']['fullName']} ({', '.join(filter(lambda email: email.endswith(f'@{AEGEE_MUENCHEN_DOMAIN}'), map(lambda email: email['address'], u['emails'])))})", sorted_users)))
        elif users[0]['kind'] == 'admin#directory#member':
            sorted_users = sorted(users, key=lambda u: u['email'])
            print('\n'.join(map(lambda m: f"* {m['email']}", sorted_users)))
        else:
            raise NotImplementedError(f"Unknown user type: {users[0]['kind']}")


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
        is_in_group = any([user for user in gsuite_users if member.user.email.lower() == user['email'].lower() or re.sub('@gmail\.com$', '@googlemail.com', member.user.email.lower()) == user['email'].lower()])
        if not is_in_group:
            missing.append(member)
    if len(missing) > 0:
        print(f'Members missing from {AEGEE_MUENCHEN_MEMBERS_GROUP} (matched {len(myaegee_members) - len(missing)}/{len(myaegee_members)} members):')
        print_users(missing)
    else:
        print(f'All MyAEGEE users included in {AEGEE_MUENCHEN_MEMBERS_GROUP}!')
    print('')

    # Find extra users in the G-Suite group which are not in MyAEGEE
    extra: List[GSuiteMember] = []
    for user in gsuite_users:
        if user['email'] not in EXTRA_EXCLUDED:
            is_in_myaegee = any([member for member in myaegee_members if member.user.email.lower() == user['email'].lower() or re.sub('@gmail\.com$', '@googlemail.com', member.user.email.lower()) == user['email'].lower()])
            if not is_in_myaegee:
                extra.append(user)
    if len(extra) > 0:
        print(f'Extra users in {AEGEE_MUENCHEN_MEMBERS_GROUP} (matched {len(gsuite_users) - len(extra)}/{len(gsuite_users)} users):')
        print_users(extra)
    else:
        print(f'No extra users in {AEGEE_MUENCHEN_MEMBERS_GROUP}!')
    print('')


def actives_sync(args: argparse.Namespace) -> None:
    """Prints the list of MyAEGEE members without a G-Suite account.
    """
    # Get MyAEGEE body members
    myaegee_access_token = myaegee_login(args.myaegee_user, args.myaegee_pass)
    myaegee_members = myaegee_get_members(args.myaegee_body_id, myaegee_access_token)

    # Get G-Suite Directory users
    gsuite_creds = gsuite_auth(args.gsuite_credfile)
    gsuite_users = gsuite_load_directory(gsuite_creds)
    gsuite_active_users = gsuite_load_group(gsuite_creds, AEGEE_MUENCHEN_ACTIVES_GROUP)

    # Match users from MyAEGEE and G-Suite
    missing: List[MyAEGEEMember] = []
    for member in myaegee_members:
        email_match = any([user for user in gsuite_users if any(member.user.email == email['address'] for email in user['emails'])])
        name_match = any([user for user in gsuite_users if SequenceMatcher(None, f'{member.user.first_name} {member.user.last_name}', user['name']['fullName']).ratio() > 0.9])
        if not email_match and not name_match:
            missing.append(member)
    print(f'Members without G-Suite account (matched {len(myaegee_members) - len(missing)}/{len(myaegee_members)} users):')
    print_users(missing)
    print('')

    # Find extra users with G-Suite account which are not in MyAEGEE
    extra: List[GSuiteUser] = []
    for user in gsuite_users:
        user_emails = list(map(lambda email: email['address'], user['emails']))
        if not any([email in EXTRA_EXCLUDED for email in user_emails]):
            email_match = any([member.user.email in user_emails for member in myaegee_members])
            name_match = any([SequenceMatcher(None, f'{member.user.first_name} {member.user.last_name}', user['name']['fullName']).ratio() > 0.9 for member in myaegee_members])
            if not email_match and not name_match:
                extra.append(user)
    if len(extra) > 0:
        print(f'Extra users in G-Suite (matched {len(gsuite_users) - len(extra)}/{len(gsuite_users)} users):')
        print_users(extra)
    else:
        print('No extra users in G-Suite!')
    print('')

    # Find G-Suite users that are not in the actives group
    actives_missing: List[GSuiteUser] = []
    for user in gsuite_users:
        is_in_group = any([active_user['id'] == user['id'] for active_user in gsuite_active_users])
        if not is_in_group:
            actives_missing.append(user)
    if len(actives_missing) > 0:
        print(f'G-Suite members not included in {AEGEE_MUENCHEN_ACTIVES_GROUP} (found {len(gsuite_users) - len(actives_missing)}/{len(gsuite_users)} active users)')
        print_users(actives_missing)
    else:
        print(f'All G-Suite users included in {AEGEE_MUENCHEN_ACTIVES_GROUP}!')
    print('')


def main() -> None:
    args = parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
