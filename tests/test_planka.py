import configparser
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from flo.channel import Channel
from flo.const import CARDFILE
from flo.planka import Planka, format_date, parse_date
from flo.videoflo import VideoFlo


REPO = Path(__file__).resolve().parents[1]


def run_cli(script, *args):
    # Exercise the real CLI in a child process, but never touch Finder or open UI.
    bootstrap = """import sys, runpy
from pathlib import Path
from unittest.mock import patch
script = sys.argv.pop(1)
sys.path.insert(0, str(Path(script).parent))
with patch('flo.mactag.USING_MAC', False), patch('flo.mactag.call', side_effect=AssertionError('Native UI commands must not run in tests')):
    runpy.run_path(script, run_name='__main__')
"""
    return subprocess.run([sys.executable, '-c', bootstrap, str(REPO / script), *args],
                          capture_output=True, text=True)


class PlankaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp.name)
        Path('settings.ini').write_text('''[main]
root_dir = {root}
[planka]
url = https://planka.example.test/team/
token = test-token
[ttt]
name = Tony Teaches Tech
path = videos
framerate = 30
width = 1920
height = 1080
schedule = 1,3,5
planka_board_id = b1
'''.format(root=self.temp.name))
        self.env_patch = patch.dict(os.environ, {'PLANKA_API_KEY': '', 'PLANKA_TOKEN': ''})
        self.env_patch.start()
        self.finder_patch = patch('flo.mactag.USING_MAC', False)
        self.finder_patch.start()
        self.planka = Planka()
        self.channel = Channel(self.planka.config, 'ttt')
        Path('videos/project').mkdir(parents=True)
        self.idea = SimpleNamespace(path=str(Path('videos/project').resolve()),
                                    name='project', channel=self.channel,
                                    get_render_stats=lambda: {'Length': 10, 'Size': 20})
        self.planka.save_card('c1', self.idea)
        self.board = {'item': {'id': 'b1'}, 'included': {
            'lists': [{'id': 'l1', 'name': 'Script', 'type': 'active', 'position': 65536},
                      {'id': 'l2', 'name': 'Upload', 'type': 'active', 'position': 131072},
                      {'id': 'l3', 'name': 'Scheduled', 'type': 'closed', 'position': 196608},
                      {'id': 'archive', 'name': 'Archive', 'type': 'archive'}],
            'cards': [], 'taskLists': [], 'customFieldGroups': [
                {'id': 'g1', 'boardId': 'b1', 'name': 'VideoFlo'}],
            'customFields': [{'id': 'f1', 'name': 'filename', 'customFieldGroupId': 'g1'},
                             {'id': 'f2', 'name': 'Length', 'customFieldGroupId': 'g1'},
                             {'id': 'f3', 'name': 'Size', 'customFieldGroupId': 'g1'}]}}

    def tearDown(self):
        self.finder_patch.stop()
        self.env_patch.stop()
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def response(self, payload, status=200):
        return Mock(ok=status < 400, status_code=status, reason='test', json=lambda: payload)

    def test_authenticated_request_uses_subpath_json_and_timeout(self):
        with patch('flo.planka.requests.request', return_value=self.response({'item': {}})) as request:
            self.planka._request('PATCH', 'cards/c1', {'listId': 'l2'})
        request.assert_called_once_with('PATCH', 'https://planka.example.test/team/api/cards/c1',
            json={'listId': 'l2'}, headers={'Accept': 'application/json', 'Authorization': 'Bearer test-token'}, timeout=30)

    def test_api_key_and_url_already_ending_in_api(self):
        self.planka.url = 'https://planka.example.test/api'
        self.planka.api_key = 'key'
        with patch('flo.planka.requests.request', return_value=self.response({})) as request:
            self.planka._request('GET', 'projects')
        self.assertEqual(request.call_args.args[1], 'https://planka.example.test/api/projects')
        self.assertEqual(request.call_args.kwargs['headers']['X-API-Key'], 'key')
        self.assertNotIn('Authorization', request.call_args.kwargs['headers'])

    def test_errors_do_not_leak_credentials(self):
        with patch('flo.planka.requests.request', return_value=self.response({}, 401)), patch('builtins.print') as output:
            self.assertIsNone(self.planka._request('GET', 'projects'))
        self.assertNotIn('test-token', str(output.call_args_list))
        with patch('flo.planka.requests.request', side_effect=requests.exceptions.Timeout('secret')), patch('builtins.print'):
            self.assertIsNone(self.planka._request('GET', 'projects'))
        with patch('flo.planka.requests.request', return_value=Mock(ok=True, status_code=200, json=Mock(side_effect=ValueError))), patch('builtins.print'):
            self.assertIsNone(self.planka._request('GET', 'projects'))

    def test_empty_credentials_fail_only_on_network_use(self):
        self.planka.token = ''
        with self.assertRaisesRegex(ValueError, 'PLANKA_API_KEY'):
            self.planka._request('GET', 'projects')

    def test_config_does_not_treat_planka_as_channel(self):
        self.assertEqual([c.id for c in VideoFlo().channels], ['ttt'])

    def test_select_board_preserves_percent_characters_and_ignores_trello_id(self):
        self.planka.config.remove_option('ttt', 'planka_board_id')
        self.planka.config.set('ttt', 'board_id', 'old-trello-id')
        self.planka.config.set('ttt', 'description', '100% ready.txt')
        payload = {'items': [{'id': 'p1', 'name': 'Videos'}],
                   'included': {'boards': [{'id': 'b2', 'projectId': 'p1', 'name': 'Production'}]}}
        with patch.object(self.planka, '_request', return_value=payload), patch('builtins.input', return_value='1'), patch('builtins.print'):
            self.assertEqual(self.planka._get_board(self.channel), 'b2')
        config = configparser.ConfigParser(interpolation=None)
        config.read('settings.ini')
        self.assertEqual(config['ttt']['planka_board_id'], 'b2')
        self.assertEqual(config['ttt']['description'], '100% ready.txt')

    def test_stage_initialization_is_idempotent_and_appends_missing_lists(self):
        with patch.object(self.planka, '_request', side_effect=[self.board, {'item': {'id': 'l4', 'name': 'Film'}}]) as request:
            self.assertTrue(self.planka.lists_exist(['Script', 'Film'], self.channel, create=True))
        self.assertEqual(request.call_args.args, ('POST', 'boards/b1/lists',
            {'name': 'Film', 'position': 262144, 'type': 'active'}))
        with patch.object(self.planka, '_request', return_value=self.board) as request:
            self.assertTrue(self.planka.lists_exist(['Script', 'Upload'], self.channel, create=True))
        self.assertEqual(request.call_count, 1)

    def test_duplicate_stage_lists_fail(self):
        self.board['included']['lists'].append(dict(self.board['included']['lists'][0], id='dup'))
        with patch.object(self.planka, '_request', return_value=self.board), patch('builtins.print'):
            self.assertFalse(self.planka.lists_exist(['Script'], self.channel, create=True))

    def test_scheduling_uses_utc_and_excludes_archived_cards(self):
        self.board['included']['cards'] = [
            {'dueDate': '2026-10-09T12:00:00-06:00', 'listId': 'l3'},
            {'dueDate': '2030-01-01T00:00:00Z', 'listId': 'archive'}]
        with patch.object(self.planka, '_board', return_value=self.board):
            due = self.planka._get_next_due_date('b1', [1, 3, 5])
        self.assertEqual(due, datetime(2026, 10, 12, 18, tzinfo=timezone.utc))
        self.assertEqual(format_date('2026-10-09T12:00:00-06:00'), '2026-10-09T18:00:00.000000Z')
        self.assertEqual(parse_date('2026-10-09T18:00:00Z'), parse_date('2026-10-09T18:00:00.000Z'))

    def test_schedule_read_failure_does_not_create_card(self):
        with patch.object(self.planka, '_board', return_value=None), patch.object(self.planka, '_request') as request:
            with self.assertRaises(RuntimeError):
                self.planka._get_next_due_date('b1', [1])
        request.assert_not_called()

    def test_create_card_and_both_tag_task_lists(self):
        due = datetime(2026, 10, 12, 18, tzinfo=timezone.utc)
        with patch.object(self.planka, '_get_list', return_value='l1'), patch.object(self.planka, '_get_next_due_date', return_value=due), patch.object(self.planka, '_request', side_effect=[{'item': {'id': 'c2'}}, {'item': {'id': 't1'}}, {'item': {'id': 't2'}}]) as request:
            self.assertEqual(self.planka.make_card(self.idea), ('c2', 'b1'))
        self.assertEqual(request.call_args_list[0].args, ('POST', 'lists/l1/cards',
            {'type': 'project', 'name': 'project', 'position': 0, 'dueDate': due.isoformat()}))
        self.assertEqual([c.args[2]['name'] for c in request.call_args_list[1:]], ['hashtags', 'tags'])

    def test_failed_checklist_creation_cleans_up_card(self):
        with patch.object(self.planka, '_get_list', return_value='l1'), patch.object(self.planka, '_get_next_due_date', return_value=None), patch.object(self.planka, '_request', side_effect=[{'item': {'id': 'c2'}}, None, {'item': {'id': 'c2'}}]) as request, patch('builtins.print'):
            self.assertEqual(self.planka.make_card(self.idea), (None, None))
        self.assertEqual(request.call_args.args, ('DELETE', 'cards/c2'))

    def test_move_checks_board_and_uses_patch(self):
        with patch.object(self.planka, '_get_list', return_value='l2'), patch.object(self.planka, '_request', side_effect=[{'item': {'boardId': 'b1'}}, {'item': {'id': 'c1'}}]) as request:
            self.assertTrue(self.planka.move_card(self.idea, 'Upload'))
        self.assertEqual(request.call_args.args, ('PATCH', 'cards/c1', {'listId': 'l2', 'position': 0}))
        with patch.object(self.planka, '_get_list', return_value='l2'), patch.object(self.planka, '_request', return_value={'item': {'boardId': 'other'}}) as request, patch('builtins.print'):
            self.assertFalse(self.planka.move_card(self.idea, 'Upload'))
        self.assertEqual(request.call_count, 1)

    def test_upload_metadata_and_matching_named_task_list(self):
        self.board['included']['cards'] = [{'id': 'c1', 'listId': 'l2', 'name': 'Title', 'description': None,
                                           'dueDate': '2026-10-09T18:00:00Z', 'position': 1}]
        self.board['included']['taskLists'] = [{'id': 't1', 'cardId': 'c1', 'name': 'tags'}]
        with patch.object(self.planka, '_board', return_value=self.board):
            card = self.planka.get_list('Upload', self.channel)[0]
        self.assertEqual(card['desc'], '')
        self.assertEqual(card['due'], '2026-10-09T18:00:00.000000Z')
        self.assertEqual(card['idChecklists'], ['t1'])
        with patch.object(self.planka, '_request', return_value={'item': {'name': 'tags'}, 'included': {'tasks': [
                {'name': 'second', 'position': 2, 'isCompleted': True}, {'name': 'first', 'position': 1}]}}):
            self.assertEqual(self.planka.get_checklist(['t1'], 'tags'), ['first', 'second'])
            self.assertEqual(self.planka.get_checklist(['t1'], 'hashtags'), [])

    def test_custom_field_creation_reuses_group_and_existing_fields(self):
        with patch.object(self.planka, '_request', side_effect=[self.board, {'item': {'id': 'f4'}}, {'item': {'id': 'f5'}}]) as request:
            self.assertTrue(self.planka.add_custom_fields(self.channel))
        self.assertEqual([call.args[2]['name'] for call in request.call_args_list[1:]], ['ProjectSize', 'RenderTime'])
        self.assertTrue(all(call.args[1] == 'custom-field-groups/g1/custom-fields' for call in request.call_args_list[1:]))

    def test_filename_and_stats_use_string_field_values(self):
        with patch.object(self.planka, '_board', return_value=self.board), patch.object(self.planka, '_request', return_value={'item': {}}) as request:
            self.assertTrue(self.planka.add_filename_to_card('c1', 'b1', 'project'))
            self.assertTrue(self.planka.set_render_stats(self.idea, {'Length': 10, 'success': True}))
        self.assertEqual(request.call_args_list[0].args, ('PATCH', 'cards/c1/custom-field-values/customFieldGroupId:g1:customFieldId:f1', {'content': 'project'}))
        self.assertEqual(request.call_args.args[2], {'content': '10'})
        self.assertEqual(request.call_count, 2)
        with patch.object(self.planka, '_board', return_value=self.board), patch.object(self.planka, '_request', return_value=None):
            self.assertFalse(self.planka.add_filename_to_card('c1', 'b1', 'project'))

    def test_youtube_links_are_link_attachments(self):
        with patch.object(self.planka, '_request', return_value={'item': {}}) as request:
            self.assertTrue(self.planka.attach_links_to_card('c1', 'video123'))
        self.assertEqual(request.call_args_list[0].args[2], {'type': 'link', 'name': 'YouTube Studio', 'url': 'https://studio.youtube.com/video/video123/edit'})
        self.assertEqual(request.call_args.args[2]['url'], 'https://youtu.be/video123')

    def test_unlinked_dry_run_never_reads_or_writes_remote(self):
        Path(self.idea.path, CARDFILE).unlink()
        before = Path('settings.ini').read_bytes()
        with patch.object(self.planka, '_request') as request, patch('builtins.print'):
            self.planka.sync(self.idea, 'Upload', dry_run=True, verbose=True)
        request.assert_not_called()
        self.assertFalse(Path(self.idea.path, CARDFILE).exists())
        self.assertEqual(Path('settings.ini').read_bytes(), before)

    def test_linked_dry_run_only_reads_and_does_not_move(self):
        with patch.object(self.planka, '_get_list_of_card', return_value='Script'), patch.object(self.planka, 'move_card') as move, patch.object(self.planka, 'set_render_stats') as stats, patch('builtins.print'):
            self.planka.sync(self.idea, 'Upload', dry_run=True, verbose=True)
        move.assert_not_called()
        stats.assert_not_called()

    def test_offline_sync_creates_saves_moves_and_retries_stats(self):
        Path(self.idea.path, CARDFILE).unlink()
        with patch.object(self.planka, 'make_card', return_value=('c2', 'b1')), patch.object(self.planka, 'add_filename_to_card', return_value=True), patch.object(self.planka, 'move_card', return_value=True) as move, patch.object(self.planka, 'set_render_stats', return_value=True) as stats, patch('builtins.print'):
            self.planka.sync(self.idea, 'Upload', dry_run=False, verbose=False)
        self.assertEqual(Path(self.idea.path, CARDFILE).read_text(), 'c2')
        move.assert_called_once_with(self.idea, 'Upload')
        stats.assert_called_once_with(self.idea, {'Length': 10, 'Size': 20})
        with patch.object(self.planka, '_get_list_of_card', return_value='Upload'), patch.object(self.planka, 'set_render_stats', return_value=True) as stats:
            self.planka.sync(self.idea, 'Upload', dry_run=False, verbose=False)
        stats.assert_called_once()

    def test_offline_cli_works_without_planka_settings_or_credentials(self):
        Path('settings.ini').write_text(Path('settings.ini').read_text().replace('url = https://planka.example.test/team/', 'url =').replace('token = test-token', 'token ='))
        result = run_cli('new-video.py', 'offline-project', '-c', 'ttt', '--offline')
        self.assertEqual(result.returncode, 0, result.stderr)
        project = Path('videos/offline-project')
        self.assertEqual((project / '.stage').read_text(), 'Script')
        self.assertTrue((project / CARDFILE).exists())
        self.assertTrue((project / 'camera').is_dir())

    def test_trello_card_files_are_never_used(self):
        Path(self.idea.path, CARDFILE).unlink()
        Path(self.idea.path, '.card').write_text('old-trello-id')
        self.assertEqual(self.planka._get_card(self.idea), '')
        self.assertEqual(Path(self.idea.path, '.card').read_text(), 'old-trello-id')


if __name__ == '__main__':
    unittest.main()
