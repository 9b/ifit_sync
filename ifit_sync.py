"""Parse FIT file(s) generated from TrainingPeaks and upload to iFit."""
import base64
import copy
import json
import fitparse
import os
import re
import requests
import sys
import time

from bs4 import BeautifulSoup
from lxml import html
from argparse import ArgumentParser


SESSION = requests.Session()
USERAGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'"
CONFIG_PATH = os.path.expanduser('~/.config/ifit_sync')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
SESSION_FILE = os.path.join(CONFIG_PATH, 'session')
CONFIG_DEFAULTS = {'email': '', 'password': ''}


def obfuscate(p, action):
    """Obfuscate the auth details to avoid easy snatching.
    It's best to use a throw away account for these alerts to avoid having
    your authentication put at risk by storing it locally.
    """
    key = "ru7sll3uQrGtDPcIW3okutpFLo6YYtd5bWSpbZJIopYQ0Du0a1WlhvJOaZEH"
    s = list()
    if action == 'store':
        return base64.urlsafe_b64encode(p.encode()).decode()
    else:
        e = base64.urlsafe_b64decode(p)
        return e.decode()


def ifit_auth(email, password):
    """Authenticate to the iFit portal and seed the session."""
    login = 'https://www.ifit.com/web-api/login'
    data = {'email': email, 'password': password}
    SESSION.post(login, data=data)
    return True


def ifit_post(workout):
    """Post the workout to iFit using the authenticated session."""
    base = SESSION.get("https://www.ifit.com/workout/create#time%20based%20workout")
    soup = BeautifulSoup(base.content, 'html.parser')
    token = soup.find('meta', {'name': 'csrf-token'})['content']
    SESSION.headers.update({'x-csrf-token': token})
    SESSION.headers.update({'user-agent': USERAGENT})
    SESSION.headers.update({'referer': 'https://www.ifit.com/workout/create'})
    SESSION.headers.update({'from-client': 'true'})
    SESSION.headers.update({'origin': 'https://www.ifit.com'})
    create = "https://www.ifit.com/api/workouts/create"
    response = SESSION.post(create, data={'workout': json.dumps(workout)})
    return response.json()


def ifit_frame():
    """Define the frame to fill."""
    return {
        "type": "run",
        "userDefined": True,
        "targetType": "seconds",
        "fromAMap": False,
        "controls": list(),
        "targetValue": 0,
        "title": None,
    }


def mps_to_mph(mps):
    """Convert Meters per Second to Miles Per Hour."""
    if not mps:
        return None
    return 2.23694 * mps


def dict_pick(content, key, value, needle=True):
    """Find match in a list of dicts based on key/value."""
    item = next((item for item in content if item[key] == value), None)
    if item and needle:
        return item['value']


def main():
    """Core."""
    parser = ArgumentParser()
    subs = parser.add_subparsers(dest='cmd')
    setup_parser = subs.add_parser('setup')
    setup_parser.add_argument('-e', '--email', dest='email', required=True,
                              help='Email of the iFit user.', type=str)
    setup_parser.add_argument('-p', '--password', dest='pwd', required=True,
                              help='Password of the iFit user.', type=str)
    setup_parser = subs.add_parser('sync', help="Sync a FIT file to iFit")
    setup_parser.add_argument('--file', '-f', help="FIT file to process",
                              required=True)
    setup_parser.add_argument('-d', '--debug', action='store_true',
                              help='Run in debug mode')
    args = parser.parse_args()

    if args.cmd == 'setup':
        if not os.path.exists(CONFIG_PATH):
            os.makedirs(CONFIG_PATH)
        if not os.path.exists(CONFIG_FILE):
            json.dump(CONFIG_DEFAULTS, open(CONFIG_FILE, 'w'), indent=4,
                      separators=(',', ': '))
        config = CONFIG_DEFAULTS
        config['email'] = args.email
        config['password'] = str(obfuscate(args.pwd, 'store'))
        json.dump(config, open(CONFIG_FILE, 'w'), indent=4,
                  separators=(',', ': '))

    config = json.load(open(CONFIG_FILE))
    config['password'] = obfuscate(str(config['password']), 'fetch')
    if config['password'] == '':
        raise Exception("Run setup before any other actions!")

    if args.cmd == 'sync':
        if not os.path.isfile(args.file):
            raise Exception("File path isn't valid!")

        _authenticated = ifit_auth(config['email'], config['password'])
        fitfile = fitparse.FitFile(args.file)
        record = next(fitfile.get_messages('workout'))
        content = record.as_dict()['fields']
        speeds = list()

        # Outer parse
        ifit_workout = ifit_frame()
        ifit_workout['title'] = "TP-%s" % (dict_pick(content, 'name', 'wkt_name'))

        # Record conversion
        for record in fitfile.get_messages('workout_step'):
            content = record.as_dict()['fields']
            if not dict_pick(content, 'name', 'wkt_step_name'):
                continue
            ifit_workout['controls'].append({
                'at': int(ifit_workout['targetValue']),
                'value': dict_pick(content, 'name', 'custom_target_speed_high'),
                'type': "mps"
            })
            ifit_workout['targetValue'] += int(dict_pick(content, 'name',
                                                         'duration_time'))
            speeds.append(mps_to_mph(dict_pick(content, 'name',
                                               'custom_target_speed_high')))

        mins, _ = divmod(ifit_workout['targetValue'], 60)
        top_speed = sorted(speeds, reverse=True)[0]
        comment = "time: %d(min), max: %.2f(mph), steps: %d" % (mins, top_speed,
                                                                len(ifit_workout['controls']))
        ifit_workout['description'] = comment
        raw_response = ifit_post(ifit_workout)

        if raw_response['success']:
            print("[+] Created: %s (%s) - %s" % (raw_response['title'],
                  raw_response['baseFilename'], raw_response['description']))

        if args.debug:
            print(json.dumps(raw_response, indent=4))


if __name__ == '__main__':
    main()
