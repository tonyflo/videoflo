# Trello object

import os
import json
import requests
import webbrowser
import configparser
from pathlib import Path
from flo.const import cardfile, settingsfile


class Trello():

    def __init__(self):
        # get key and token to authorize with trello
        self.config = configparser.ConfigParser()
        self.config.read(settingsfile)
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

    def _make_request(self, method, url, params):
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                headers=self.headers,
            )
            return response
        except requests.exceptions.ConnectionError:
             print('Not connected to the internet')
             # TODO: this puts us out of sync with Trello
        return None


    # save the trello token to the config file and to this object
    def _save_trello_token(self, token):
        if token is None:
            print('An invalid Trello token was provided.')
            return False

        self.config.set('trello', 'token', token)
        with open(settingsfile, 'w') as configfile:
            self.config.write(configfile)

        self.token = token

        return True

    # save the board id to the config file and to this object
    def _save_board_id(self, board_id, channel):
        if board_id is None:
            print('An invalid board was provided.')
            return False

        self.config.set(channel.id, 'board_id', board_id)
        with open(settingsfile, 'w') as configfile:
            self.config.write(configfile)

        self.board_id= board_id

        return True

    # save the card id to the directory for this idea
    def save_card(self, card_id, idea):
        card_file = os.path.join(idea.path, cardfile)
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

        board_id = None
        while board_id is None:
            print('\nSelect the board associated with {}: '.format(channel.name))
            x = int(input())

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
        response = self._make_request('GET', url, params)
        if response is None:
            return None

        boards = response.json()
        board_id = self._have_user_pick_board(boards, channel)
        success = self._save_board_id(board_id, channel)

        return board_id if success else None

    def _get_card(self, idea):
        card = None
        card_file = os.path.join(idea.path, cardfile)
        with open(card_file) as f:
            card_id = f.readline().strip()

        return card_id

    def _get_list(self, board_id, name):
        list_id = None
        url = self.url + 'boards/{}/lists'.format(board_id)

        params = self.query
        params['filter'] = 'open'
        response = self._make_request('GET', url, params)
        if response is None:
            return None

        lists = response.json()
        for lst in lists:
            if lst['name'] != name:
                continue
            list_id = lst['id']

        if list_id is None:
            print('Unable to find {} board. Please create it.'.format(name))

        return list_id


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

        card = response.json()
        if 'id' not in card:
            print('Could not move the card to {}'.format(list_name))
            return False

        return True

    def _create_checklist(self, card_id):
        url = self.url + 'cards/{}/checklists'.format(card_id)
        params = self.query
        params['name'] = 'tags'
        response = self._make_request('POST', url, params)
        if response is None:
            print('Unable to create empty tags checklist')
            return False

    def _create_card(self, list_id, idea):
        url = self.url + 'cards'
        params = self.query
        params['idList'] = list_id
        params['name'] = idea.name
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

        card = self._create_card(list_id, idea)
        if card is None:
            return None

        card_id = card['id']
        if card_id is None or card_id == '':
            print('Invalid card id')
            return None

        self._create_checklist(card_id)

        return card_id

    def get_tags_from_checklist(self, checklist_ids):
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
            if 'tags' == checklist_data['name']:
                break

        if checklist_data is None:
            return None

        # TODO: might be able to do something with the state of the checkbox
        tags = [tag['name'] for tag in checklist_data['checkItems']]
        return tags


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

        return response.json()

    def find_path_for_id(self, card_id, channel):
        channel_path = Path(channel.path)
        for card_file in list(channel_path.rglob(cardfile)):
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
            if 'id' in response.json():
                continue

            print('Error when attaching "{}" link to card'.format(u))

    def delete_card(self, card_id):
        url = self.url + 'cards/{}'.format(card_id)
        params = self.query
        response = self._make_request('DELETE', url, params)

    def lists_exist(self, names, channel):
        board_id = self._get_board(channel)
        url = self.url + 'boards/{}/lists'.format(board_id)
        params = self.query
        response = self._make_request('GET', url, params)
        lists = response.json()

        exist = True
        for name in names:
            this_exists = any(lst['name'] == name for lst in lists)
            if not this_exists:
                exist = False
                print('Please create the Trello board called "{}"'.format(name))

        return exist
