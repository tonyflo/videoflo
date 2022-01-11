# Trello object

import os
import json
import requests
import webbrowser
import configparser
from pathlib import Path
from datetime import datetime, timedelta
from flo.const import CARDFILE, SETTINGSFILE, DATE_FORMAT


class Trello():

    def __init__(self):
        # get key and token to authorize with trello
        self.config = configparser.ConfigParser()
        self.config.read(SETTINGSFILE)
        try:
            self.key = self.config.get('trello', 'key')
        except configparser.NoOptionError:
            self.key = None
        try:
            self.token = self.config.get('trello', 'token')
        except configparser.NoOptionError:
            self.token = None
        self.query = self._authorize()

        self.url = 'https://api.trello.com/1/'
        self.headers = {"Accept": "application/json"}
        self.board_id = None

    def _make_request(self, method, url, params, json=False):
        try:
            if json:
                response = requests.request(method=method, url=url, json=params, headers=self.headers)
            else:
                response = requests.request(method=method, url=url, params=params, headers=self.headers)
            if False:
                print(response.request.url)
                print(response.request.headers)
            if response.ok:
                return response
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
             print('Not connected to the internet')
             # TODO: this potentially puts us out of sync with Trello
        except requests.exceptions.HTTPError:
            if response.status_code == 409: # 409=conflict, likely a duplicate item (already exists)... let caller handle
                return response
            print('Error {}: {}'.format(response.status_code, response.reason))
        return None


    # save the trello token to the config file and to this object
    def _save_trello_token(self, token):
        if token is None:
            print('An invalid Trello token was provided.')
            return False

        self.config.set('trello', 'token', token)
        with open(SETTINGSFILE, 'w') as configfile:
            self.config.write(configfile)

        self.token = token

        return True

    # save the board id to the config file and to this object
    def _save_board_id(self, board_id, channel):
        if board_id is None:
            print('An invalid board was provided.')
            return False

        self.config.set(channel.id, 'board_id', board_id)
        with open(SETTINGSFILE, 'w') as configfile:
            self.config.write(configfile)

        self.board_id= board_id

        return True

    # save the card id to the directory for this idea
    def save_card(self, card_id, idea):
        card_file = os.path.join(idea.path, CARDFILE)
        with open(card_file, 'w') as f:
            f.write(card_id)

    # either get an existing token or request a new one from trello
    def _authorize(self):
        success = True

        if self.key is None:
            raise ValueError('Could not find Trello key in settings file')

        if self.token is None:
            # get a token from trello via a web browser
            params = {
                'k': self.key,
                'u': 'https://trello.com/1/authorize',
                'n': 'videoflo',
                'e': 'never',
                's': 'read,write',
            }
            authorization_url = '{u}?expiration={e}&name={n}&scope={s}&response_type=token&key={k}'.format(**params)
            webbrowser.open(authorization_url)

            # need the user to input token on the command line
            token = input("Enter your token and hit Enter: ")
            success = self._save_trello_token(token)

        if success:
            return {'key': self.key, 'token': self.token}

        raise ValueError('Unable to authorize with Trello')

    def _have_user_pick_board(self, boards, channel):
        print("Your Trello boards:")
        for num, board in enumerate(boards, start=1):
            print(num, ': ', board['name'])

        if len(boards) == 0:
            print('You do not have any Trello boards yet. Please make one')
            return None

        board_id = None
        while board_id is None:
            print('\nSelect the board associated with {}: '.format(channel.name))
            try:
                x = int(input())
            except ValueError:
                print('\nInvalid choice. Try again.')
                continue

            if x in range(1, len(boards)+1):
                board_name = boards[x-1]['name']
                print('\nYou have chosen {}'.format(board_name))
                board_id = boards[x-1]['id']
            else:
                print('\nTry again.')

        return board_id

    def _get_board(self, channel):

        try:
            self.board_id = self.config.get(channel.id, 'board_id')
            return self.board_id
        except configparser.NoOptionError:
            pass

        url = self.url + 'members/me/boards?fields=name&filter=open'
        params = self.query
        response = self._make_request('GET', url, params, json=True)
        if response is None:
            return None

        boards = response.json()
        board_id = self._have_user_pick_board(boards, channel)
        if board_id is None:
            return None
        success = self._save_board_id(board_id, channel)

        return board_id if success else None

    def _get_card(self, idea):
        card = None
        card_file = os.path.join(idea.path, CARDFILE)
        with open(card_file) as f:
            card_id = f.readline().strip()

        return card_id

    # return the next date based on the board's latest due date and the
    # channel's release schedule
    def _get_next_due_date(self, board_id, schedule):
        if schedule is None:
            return None

        url = self.url + 'boards/{}/cards/open'.format(board_id)
        params = self.query
        params['fields'] = 'due'
        response = self._make_request('GET', url, params)
        if response is None:
            return None

        cards = response.json()
        if len(cards) == 0:
            return None

        dues = [card['due'] for card in cards if card['due'] is not None]
        if len(dues) == 0:
            return None

        dates = [datetime.strptime(due, DATE_FORMAT) for due in dues]
        sorted_dates = sorted(dates)
        latest_date = sorted_dates[-1]

        next_date = latest_date + timedelta(days=1)
        while next_date.isoweekday() not in schedule:
            next_date = next_date + timedelta(days=1)

        return next_date

    def _get_list(self, board_id, name):
        list_id = None
        url = self.url + 'boards/{}/lists'.format(board_id)

        params = self.query
        params['filter'] = 'open'
        params['fields'] = 'all'
        response = self._make_request('GET', url, params)
        if response is None:
            return None

        lists = response.json()
        for lst in lists:
            if lst['name'] != name:
                continue
            list_id = lst['id']

        if list_id is None:
            print('Unable to find {} list. Please run init.'.format(name))

        return list_id

    def _create_list(self, board_id, name):
        url = self.url + 'lists'
        params = self.query
        params['name'] = '{}'.format(name)
        params['idBoard'] = board_id
        params['pos'] = 'bottom'
        response = self._make_request('POST', url, params)
        if response is None:
            return None

        lst = response.json()
        if 'id' not in lst:
            print('Something went wrong when creating the {} list'.format(name))
            return None

        print('Created the Trello list {}.'.format(name))
        return lst

    def move_card(self, idea, list_name):
        channel = idea.channel
        board_id = self._get_board(channel)
        if board_id is None:
            return False

        destination_list_id = self._get_list(board_id, list_name)
        if destination_list_id is None:
            return False

        card_id = self._get_card(idea)
        if card_id is None or card_id == '':
            print('Unable to determine the id for this Trello card')
            return False

        url = self.url + 'cards/{}'.format(card_id)
        params = self.query
        params['idList'] = destination_list_id
        response = self._make_request('PUT', url, params)
        if response is None:
            return False

        card = response.json()
        if 'id' not in card:
            print('Could not move the card to {}'.format(list_name))
            return False

        return True

    def _create_checklist(self, card_id, name):
        url = self.url + 'cards/{}/checklists'.format(card_id)
        params = self.query
        params['name'] = name
        response = self._make_request('POST', url, params)
        if response is None:
            print('Unable to create empty tags checklist')
            return False

    def _create_card(self, list_id, idea, due_date):
        url = self.url + 'cards'
        params = self.query
        params['idList'] = list_id
        params['name'] = idea.name
        params['due'] = due_date
        params['pos'] = 'top'
        response = self._make_request('POST', url, params)
        if response is None:
            return None

        card = response.json()
        if 'id' not in card:
            print('Something went wrong when creating the card')
            return None

        return card

    def make_card(self, idea):
        channel = idea.channel
        board_id = self._get_board(channel)
        if board_id is None:
            return None

        list_id = self._get_list(board_id, 'Script')
        if list_id is None:
            return None

        schedule = idea.channel.schedule
        due_date = self._get_next_due_date(board_id, schedule)
        if due_date is None:
            due_date = datetime.utcnow() + timedelta(days=7)
            print('NOTE: set due date for 1 week from today')

        due_date = due_date.isoformat() + 'Z'
        card = self._create_card(list_id, idea, due_date)
        if card is None:
            return None

        card_id = card['id']
        if card_id is None or card_id == '':
            print('Invalid card id')
            return None

        self._create_checklist(card_id, 'hashtags')
        self._create_checklist(card_id, 'tags')

        return card_id, board_id

    def add_filename_to_card(self, card_id, board_id, filename):
        if not self.is_premium_board(board_id):
            return True # ok to return True here

        field = 'filename'
        field_id = self._get_custom_field_id(board_id, field)
        if field_id is None:
            print('Trello custom field {} probably does not exist. Please run init.'.format(field))
            return False

        value_formatted = {'text': filename}
        self._set_custom_field(card_id, field_id, field, value_formatted)

        return True

    def get_checklist(self, checklist_ids, name):
        checklist_data = None
        # if there are multiple checklists, need to find the tags one
        for cid in checklist_ids:
            url = self.url + 'checklists/{}'.format(cid)

            params = self.query
            params['checkItem_fields'] = 'name,state'
            response = self._make_request('GET', url, params)
            if response is None:
                return None

            checklist_data = response.json()
            if name == checklist_data['name']:
                break

        if checklist_data is None:
            return None

        # TODO: might be able to do something with the state of the checkbox
        items = [item['name'] for item in checklist_data['checkItems']]
        return items

    def get_list(self, list_name, channel):
        board_id = self._get_board(channel)
        if board_id is None:
            return False

        list_id = self._get_list(board_id, list_name)
        if list_id is None:
            return False

        url = self.url + 'lists/{}/cards'.format(list_id)
        params = self.query
        response = self._make_request('GET', url, params)
        if response is None:
            return []

        return response.json()

    def find_path_for_id(self, card_id, channel):
        channel_path = Path(channel.path)
        for card_file in list(channel_path.rglob(CARDFILE)):
            with open(card_file) as f:
                if card_id != f.read().strip():
                    continue
                path = os.path.dirname(card_file)
                return path

        return None


    def attach_links_to_card(self, card_id, video_id):
        url = self.url + 'cards/{}/attachments'.format(card_id)
        attachments = {
            'YouTube Studio': 'https://studio.youtube.com/video/{}/edit',
            'YouTube video': 'https://youtu.be/{}'
        }
        for name, link in attachments.items():
            u = link.format(video_id)
            params = self.query
            params['name'] = name
            params['url'] = u
            response = self._make_request('POST', url, params)
            if response is None:
                break
            if 'id' in response.json():
                continue

            print('Error when attaching "{}" link to card'.format(u))

    def delete_card(self, card_id):
        url = self.url + 'cards/{}'.format(card_id)
        params = self.query
        response = self._make_request('DELETE', url, params)
        if response is None:
            print('Unable to delete card')

    def lists_exist(self, names, channel, create=False):
        board_id = self._get_board(channel)
        if board_id is None:
            return False

        url = self.url + 'boards/{}/lists'.format(board_id)
        params = self.query
        params['filter'] = 'open'
        params['fields'] = 'all'
        response = self._make_request('GET', url, params, json=True)
        if response is None:
            return False
        lists = response.json()

        exist = True
        for name in names:
            this_exists = any(lst['name'] == name for lst in lists)
            if not this_exists:
                if create is False:
                    exist = False
                    print('Trello list called "{}" does not exist. Please run init.'.format(name))
                else:
                    lst = self._create_list(board_id, name)
                    if lst is None:
                        exist = False
                        break

        return exist

    def add_custom_fields(self, channel):
        fields = {
                  'Length': 'number',
                  'Size': 'number',
                  'ProjectSize': 'number',
                  'RenderTime': 'number',
                  'filename': 'text',
        }
        board_id = self._get_board(channel)

        if not self.is_premium_board(board_id):
            return

        for name, kind in fields.items():
            success = self._add_custom_field(board_id, name, kind)
            if not success:
                break

    def _add_custom_field(self, board_id, field_name, field_type):
        url = self.url + 'customFields'
        params = self.query
        params['idModel'] = board_id
        params['modelType'] = 'board'
        params['name'] = field_name
        params['type'] = field_type
        params['display_cardFront'] = 'false'
        params['pos'] = 'bottom'
        response = self._make_request('POST', url, params)
        if response is None:
            return False

        if response.status_code == 409:
            return True # field already exists

        field = response.json()
        if 'id' not in field:
            print('Something went wrong when creating the {} custom field'.format(field_name))
            return False

        print('Added {} field to Trello cards'.format(field_name))
        return True

    def _set_custom_field(self, card_id, field_id, name, value):
        url = self.url + 'card/{}/customField/{}/item'.format(card_id, field_id)
        params = self.query
        params['value'] = value
        response = self._make_request('PUT', url, params, json=True)
        if response is None:
            print('Unable to set custom field: {} = {}'.format(name, value))
            return False

        # TODO: move this error handling into _make_request?
        if response.status_code != 200:
            print('Unable to set {} field: {}'.format(name, response.json()['message']))
            return False

        return True

    def _get_custom_fields(self, board_id):
        url = self.url + 'boards/{}/customFields'.format(board_id)
        params = self.query
        response = self._make_request('GET', url, params)
        if response is None:
            print('Unable to get custom fields from Trello')
            return None
        fields = response.json()
        return fields

    def _get_custom_field_id(self, board_id, name):
        fields = self._get_custom_fields(board_id)
        if fields is None:
            return None

        for field in fields:
            if name != field['name']:
                continue
            return field['id']

        return None

    def set_render_stats(self, idea, stats):
        channel = idea.channel
        board_id = self._get_board(channel)
        if board_id is None:
            return False

        if not self.is_premium_board(board_id):
            return False

        card_id = self._get_card(idea)
        if card_id is None or card_id == '':
            print('Unable to determine the id for this Trello card')
            return False

        fields = self._get_custom_fields(board_id)
        if fields is None:
            return False

        for field in fields:
            name = field['name']
            try:
                value = stats[name]
            except KeyError:
                continue # not all Trello custom fields are render stats
            field_id = field['id']
            value_formatted = {'number': str(value)} # API wants str for numbers
            self._set_custom_field(card_id, field_id, name, value_formatted)

    # determine if Custom Fields can be on this board
    def is_premium_board(self, board_id):
        is_premium = False

        url = self.url + 'boards/{}'.format(board_id)
        params = self.query
        response = self._make_request('GET', url, params, json=True)
        if response is None:
            print('Unable to get board data')
            return is_premium

        board = response.json()
        try:
            organization_id = board['idOrganization']
        except KeyError:
            return is_premium # not premium board because this field doesn't exist

        url = self.url + 'organizations/{}'.format(organization_id)
        params = self.query
        response = self._make_request('GET', url, params, json=True)
        if response is None:
            print('Unable to determine if organization of board')
            return is_premium
        organization = response.json()
        try:
            is_premium = any(item in organization['products'] for item in [110, 111, 119])
        except:
            print('Unable to determine if Custom Fields can be used on this board')

        return is_premium
