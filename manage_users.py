#!/usr/bin/env python3
import argparse
import getpass

from model import *

def main():
    parser = argparse.ArgumentParser(description='Create or delete users')
    subparsers = parser.add_subparsers(dest='subparser_name')

    create_parser = subparsers.add_parser('list')

    create_parser = subparsers.add_parser('create')
    create_parser.add_argument('name')
    create_parser.add_argument('--admin', action='store_true')

    create_parser = subparsers.add_parser('delete')
    create_parser.add_argument('name')

    args = parser.parse_args()

    db = open_db()
    if args.subparser_name == 'create':
        user = User(name=args.name, admin=args.admin)
        password = getpass.getpass("Enter Password: ")
        password_confirm = getpass.getpass("Confirm Password: ")
        if password == password_confirm:
            user.set_password(password)
            user.insert(db)
        else:
            print("Passwords dont match")
    elif args.subparser_name == 'delete':
        user = User.get_by_name(db, args.name)
        if user is None:
            print("User does not exist")
        else:
            user.delete(db)
    elif args.subparser_name == 'list':
        for user in User.get_all(db):
            print('"{}"'.format(user.name))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
