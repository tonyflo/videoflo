"""Planka 2.x integration for VideoFlo's production workflow."""

import configparser
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import requests

from flo.const import CARDFILE, SETTINGSFILE, DATE_FORMAT


def parse_date(value):
    """Accept ISO 8601 dates with or without fractional seconds/UTC offsets."""
    date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return date.astimezone(timezone.utc)


def format_date(value):
    return parse_date(value).strftime(DATE_FORMAT) if value else None


class Planka:
    FIELD_NAMES = ('Length', 'Size', 'ProjectSize', 'RenderTime', 'filename')
    GROUP_NAME = 'VideoFlo'

    def __init__(self):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(SETTINGSFILE)
        self.url = self.config.get('planka', 'url', fallback='').strip().rstrip('/')
        self.api_key = os.environ.get('PLANKA_API_KEY') or self.config.get(
            'planka', 'api_key', fallback='').strip()
        self.token = os.environ.get('PLANKA_TOKEN') or self.config.get(
            'planka', 'token', fallback='').strip()
        # Configuration is validated on first request so --offline still works.

    def _request(self, method, path, data=None):
        parsed = urlsplit(self.url)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValueError('Set [planka] url to your Planka instance URL in settings.ini')
        if not self.api_key and not self.token:
            raise ValueError('Set PLANKA_API_KEY or PLANKA_TOKEN (or [planka] api_key/token)')
        headers = {'Accept': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        else:
            headers['Authorization'] = 'Bearer ' + self.token
        api_url = self.url if self.url.endswith('/api') else self.url + '/api'
        try:
            response = requests.request(method, api_url + '/' + path,
                                        json=data, headers=headers, timeout=30)
            if not response.ok:
                print('Planka Error {}: {} ({} {})'.format(
                    response.status_code, response.reason, method, path))
                if response.status_code == 401:
                    print('Check your Planka API key or replace the expired access token.')
                return None
            if response.status_code == 204:
                return {}
            payload = response.json()
            if not isinstance(payload, dict):
                print('Unexpected Planka response. This integration requires Planka 2.x.')
                return None
            return payload
        except requests.exceptions.RequestException:
            print('Unable to reach Planka. Try --offline, then sync.py when connected.')
        except ValueError:
            print('Planka returned invalid JSON. Check the instance URL and reverse proxy.')
        return None

    def _get_board(self, channel):
        board_id = self.config.get(channel.id, 'planka_board_id', fallback='').strip()
        if board_id:
            return board_id
        response = self._request('GET', 'projects')
        if response is None:
            return None
        boards = response.get('included', {}).get('boards', [])
        projects = {p['id']: p['name'] for p in response.get('items', [])}
        if not boards:
            print('No Planka boards found. Create a board and grant this user editor access.')
            return None
        print('Your Planka boards:')
        for i, board in enumerate(boards, 1):
            print('{}: {} / {}'.format(i, projects.get(board['projectId'], ''), board['name']))
        while True:
            try:
                choice = int(input('Select the board for {}: '.format(channel.name)))
                if 1 <= choice <= len(boards):
                    break
            except ValueError:
                pass
            print('Invalid choice. Try again.')
        board_id = str(boards[choice - 1]['id'])
        self.config.set(channel.id, 'planka_board_id', board_id)
        with open(SETTINGSFILE, 'w') as configfile:
            self.config.write(configfile)
        return board_id

    def _board(self, board_id):
        return self._request('GET', 'boards/{}'.format(board_id))

    @staticmethod
    def _active_lists(board):
        # Closed lists remain visible kanban lists; archive/trash are excluded.
        return [item for item in board.get('included', {}).get('lists', [])
                if item.get('type') in ('active', 'closed')]

    def _get_list(self, board_id, name):
        board = self._board(board_id)
        if board is None:
            return None
        matches = [item for item in self._active_lists(board) if item['name'] == name]
        if len(matches) != 1:
            print('Expected one Planka list named "{}"; found {}. Run init or rename duplicates.'.format(name, len(matches)))
            return None
        return matches[0]['id']

    def lists_exist(self, names, channel, create=False):
        board_id = self._get_board(channel)
        if not board_id:
            return False
        board = self._board(board_id)
        if board is None:
            return False
        lists = self._active_lists(board)
        position = max([item.get('position') or 0 for item in lists] + [0])
        success = True
        for name in names:
            matches = [item for item in lists if item['name'] == name]
            if len(matches) == 1:
                continue
            if matches:
                print('Multiple Planka lists named "{}". Rename duplicates.'.format(name))
                return False
            if not create:
                print('Planka list "{}" does not exist. Please run init.'.format(name))
                success = False
                continue
            position += 65536
            response = self._request('POST', 'boards/{}/lists'.format(board_id),
                                     {'name': name, 'position': position, 'type': 'active'})
            if not response or 'item' not in response:
                return False
            lists.append(response['item'])
            print('Created the Planka list {}.'.format(name))
        return success

    def _get_card(self, idea):
        try:
            with open(os.path.join(idea.path, CARDFILE)) as cardfile:
                return cardfile.read().strip()
        except FileNotFoundError:
            return ''

    def save_card(self, card_id, idea):
        with open(os.path.join(idea.path, CARDFILE), 'w') as cardfile:
            cardfile.write(str(card_id))

    def _get_next_due_date(self, board_id, schedule):
        board = self._board(board_id)
        if board is None:
            raise RuntimeError('Unable to read Planka schedule; no card was created')
        list_ids = {item['id'] for item in self._active_lists(board)
                    if item['name'] not in ('Idea', 'Published')}
        dates = [parse_date(card['dueDate']) for card in board.get('included', {}).get('cards', [])
                 if card.get('dueDate') and card['listId'] in list_ids]
        if not dates or not schedule:
            return None
        next_date = max(dates) + timedelta(days=1)
        while next_date.isoweekday() not in schedule:
            next_date += timedelta(days=1)
        return next_date

    def make_card(self, idea, stage='Script'):
        if stage not in ('Idea', 'Script'):
            raise ValueError('New cards start in Idea or Script')
        board_id = self._get_board(idea.channel)
        if not board_id:
            return None, None
        list_id = self._get_list(board_id, stage)
        if not list_id:
            return None, None
        payload = {'type': 'project', 'name': idea.name, 'position': 0}
        if stage == 'Script':
            due = self._get_next_due_date(board_id, idea.channel.schedule)
            if due is None:
                due = datetime.now(timezone.utc) + timedelta(days=7)
                print('NOTE: set due date for 1 week from today')
            payload['dueDate'] = due.isoformat()
        response = self._request('POST', 'lists/{}/cards'.format(list_id), payload)
        if not response or 'item' not in response:
            return None, None
        card_id = response['item']['id']
        for pos, name in enumerate(('hashtags', 'tags'), 1):
            checklist = self._request('POST', 'cards/{}/task-lists'.format(card_id),
                                      {'name': name, 'position': pos * 65536})
            if not checklist or 'item' not in checklist:
                self.delete_card(card_id)
                return None, None
        return card_id, board_id

    def move_card(self, idea, list_name):
        board_id = self._get_board(idea.channel)
        if not board_id:
            return False
        list_id = self._get_list(board_id, list_name)
        card_id = self._get_card(idea)
        if not list_id or not card_id:
            print('Unable to determine the Planka card/list. Run sync for offline projects.')
            return False
        card = self._request('GET', 'cards/{}'.format(card_id))
        if not card or card.get('item', {}).get('boardId') != board_id:
            print('Planka card does not belong to the configured channel board.')
            return False
        response = self._request('PATCH', 'cards/{}'.format(card_id),
                                 {'listId': list_id, 'position': 0})
        return bool(response and 'item' in response)

    def ready_to_script(self, idea):
        """Commit an idea to production, preserving any manually chosen due date."""
        board_id = self._get_board(idea.channel)
        card_id = self._get_card(idea)
        if not board_id or not card_id:
            return False
        list_id = self._get_list(board_id, 'Script')
        response = self._request('GET', 'cards/{}'.format(card_id))
        if not list_id or not response or response.get('item', {}).get('boardId') != board_id:
            return False
        payload = {'listId': list_id, 'position': 0}
        if not response['item'].get('dueDate'):
            due = self._get_next_due_date(board_id, idea.channel.schedule)
            if due is None:
                due = datetime.now(timezone.utc) + timedelta(days=7)
            payload['dueDate'] = due.isoformat()
        response = self._request('PATCH', 'cards/{}'.format(card_id), payload)
        return bool(response and 'item' in response)

    def get_list(self, list_name, channel):
        board_id = self._get_board(channel)
        if not board_id:
            return []
        board = self._board(board_id)
        if board is None:
            return []
        lists = [item for item in self._active_lists(board) if item['name'] == list_name]
        if len(lists) != 1:
            print('Expected exactly one Planka list named {}. Please run init.'.format(list_name))
            return []
        included = board.get('included', {})
        cards = sorted((card for card in included.get('cards', []) if card['listId'] == lists[0]['id']),
                       key=lambda card: card.get('position') or 0)
        items = []
        for card in cards:
            if channel.find_path_for_id(card['id']) is None:
                print('Could not find local path for {}'.format(card['name']))
                return []
            # Normalize metadata to the shape consumed by upload.py.
            item = dict(card, desc=card.get('description') or '', due=format_date(card.get('dueDate')),
                        idChecklists=[lst['id'] for lst in included.get('taskLists', [])
                                      if lst['cardId'] == card['id']])
            items.append(item)
        return items

    def get_checklist(self, checklist_ids, name):
        for checklist_id in checklist_ids:
            response = self._request('GET', 'task-lists/{}'.format(checklist_id))
            if response is None:
                return None
            if response['item']['name'] == name:
                tasks = sorted(response.get('included', {}).get('tasks', []),
                               key=lambda task: task.get('position') or 0)
                return [task['name'] for task in tasks]
        return []

    def _fields(self, board_id, create=False):
        board = self._board(board_id)
        if board is None:
            return None
        included = board.get('included', {})
        groups = [group for group in included.get('customFieldGroups', [])
                  if group.get('boardId') == board_id and group.get('name') == self.GROUP_NAME]
        if len(groups) > 1:
            print('Multiple VideoFlo custom field groups. Rename duplicates.')
            return None
        if not groups:
            if not create:
                print('VideoFlo custom fields missing. Please run init.')
                return None
            response = self._request('POST', 'boards/{}/custom-field-groups'.format(board_id),
                                     {'name': self.GROUP_NAME, 'position': 65536})
            if not response or 'item' not in response:
                return None
            groups = [response['item']]
        group_id = groups[0]['id']
        fields = {field['name']: field['id'] for field in included.get('customFields', [])
                  if field.get('customFieldGroupId') == group_id}
        if create:
            for pos, name in enumerate(self.FIELD_NAMES, 1):
                if name in fields:
                    continue
                response = self._request('POST', 'custom-field-groups/{}/custom-fields'.format(group_id),
                                         {'name': name, 'position': pos * 65536,
                                          'showOnFrontOfCard': False})
                if not response or 'item' not in response:
                    return None
                fields[name] = response['item']['id']
        return group_id, fields

    def add_custom_fields(self, channel):
        board_id = self._get_board(channel)
        return bool(board_id and self._fields(board_id, create=True))

    def _set_field(self, card_id, group_id, field_id, value):
        path = 'cards/{}/custom-field-values/customFieldGroupId:{}:customFieldId:{}'.format(
            card_id, group_id, field_id)
        response = self._request('PATCH', path, {'content': str(value)})
        return bool(response and 'item' in response)

    def add_filename_to_card(self, card_id, board_id, filename):
        fields = self._fields(board_id)
        if fields is None or 'filename' not in fields[1]:
            return False
        return self._set_field(card_id, fields[0], fields[1]['filename'], filename)

    def set_render_stats(self, idea, stats):
        board_id = self._get_board(idea.channel)
        card_id = self._get_card(idea)
        if not board_id or not card_id:
            return False
        fields = self._fields(board_id)
        if fields is None:
            return False
        success = True
        for name in self.FIELD_NAMES:
            if name in stats:
                if name not in fields[1] or not self._set_field(card_id, fields[0], fields[1][name], stats[name]):
                    success = False
        return success

    def attach_links_to_card(self, card_id, video_id):
        attachments = {'YouTube Studio': 'https://studio.youtube.com/video/{}/edit',
                       'YouTube video': 'https://youtu.be/{}'}
        for name, url in attachments.items():
            response = self._request('POST', 'cards/{}/attachments'.format(card_id),
                                     {'type': 'link', 'name': name, 'url': url.format(video_id)})
            if not response or 'item' not in response:
                return False
        return True

    def delete_card(self, card_id):
        return self._request('DELETE', 'cards/{}'.format(card_id)) is not None

    def _get_list_of_card(self, card_id):
        response = self._request('GET', 'cards/{}'.format(card_id))
        if not response or 'item' not in response:
            return None
        response = self._request('GET', 'lists/{}'.format(response['item']['listId']))
        return response['item']['name'] if response and 'item' in response else None

    def sync(self, idea, stage, dry_run, verbose):
        card_id = self._get_card(idea)
        old_stage = None
        if not card_id:
            if dry_run:
                print('{} would be created in {}'.format(idea.name, stage))
                return
            start_stage = 'Idea' if stage == 'Idea' else 'Script'
            card_id, board_id = self.make_card(idea, stage=start_stage)
            if not card_id:
                return
            if not self.add_filename_to_card(card_id, board_id, idea.name):
                self.delete_card(card_id)
                return
            self.save_card(card_id, idea)
            old_stage = start_stage
            print('{} was created'.format(idea.name))
        if old_stage is None:
            old_stage = self._get_list_of_card(card_id)
        if old_stage is None:
            print('WARN: Planka card for {} could not be read'.format(idea.name))
            return
        moved = old_stage != stage
        if moved:
            if dry_run:
                print('{} would be moved from {} to {}'.format(idea.name, old_stage, stage))
                return
            success = (self.ready_to_script(idea) if old_stage == 'Idea' and stage == 'Script'
                       else self.move_card(idea, stage))
            if not success:
                print('ERROR: Unable to sync {} from {} to {}'.format(idea.name, old_stage, stage))
                return
            print('{} was moved from {} to {}'.format(idea.name, old_stage, stage))
        elif verbose:
            print('{} remains in {}'.format(idea.name, stage))
        if stage == 'Upload' and not dry_run:
            # Retry stats on subsequent syncs even if the card already moved.
            try:
                stats = idea.get_render_stats()
            except (FileNotFoundError, ValueError):
                print('WARN: No readable render stats for {}'.format(idea.name))
                return
            if not self.set_render_stats(idea, stats):
                print('WARN: Could not sync render stats for {}'.format(idea.name))
