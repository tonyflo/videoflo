import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import unittest
import test_planka as fixtures

REPO = fixtures.REPO
from flo.linking import link_plans, sync_from_planka
from flo.const import CARDFILE
from flo import mactag


class LinkingTests(unittest.TestCase):
    setUp = fixtures.PlankaTests.setUp
    tearDown = fixtures.PlankaTests.tearDown
    def test_idea_is_created_without_due_date_or_schedule_lookup(self):
        with patch.object(self.planka, '_get_list', return_value='idea-list') as stage, patch.object(self.planka, '_get_next_due_date') as schedule, patch.object(self.planka, '_request', side_effect=[{'item': {'id': 'c2'}}, {'item': {'id': 't1'}}, {'item': {'id': 't2'}}]) as request:
            self.assertEqual(self.planka.make_card(self.idea, stage='Idea'), ('c2', 'b1'))
        stage.assert_called_once_with('b1', 'Idea')
        schedule.assert_not_called()
        self.assertNotIn('dueDate', request.call_args_list[0].args[2])

    def test_promotion_preserves_existing_due_date(self):
        with patch.object(self.planka, '_get_list', return_value='l1'), patch.object(self.planka, '_get_next_due_date') as schedule, patch.object(self.planka, '_request', side_effect=[{'item': {'boardId': 'b1', 'dueDate': '2026-11-01T12:00:00Z'}}, {'item': {}}]) as request:
            self.assertTrue(self.planka.ready_to_script(self.idea))
        schedule.assert_not_called()
        self.assertNotIn('dueDate', request.call_args.args[2])

    def test_idea_and_published_dates_do_not_extend_schedule(self):
        self.board['included']['lists'] += [
            {'id': 'ideas', 'name': 'Idea', 'type': 'active'},
            {'id': 'pub', 'name': 'Published', 'type': 'active'}]
        self.board['included']['cards'] = [
            {'dueDate': '2030-01-01T00:00:00Z', 'listId': 'ideas'},
            {'dueDate': '2030-01-01T00:00:00Z', 'listId': 'pub'}]
        with patch.object(self.planka, '_board', return_value=self.board):
            self.assertIsNone(self.planka._get_next_due_date('b1', [1, 3, 5]))

    def test_slug_matching_pulls_film_not_old_local_stage(self):
        Path(self.idea.path, CARDFILE).unlink()
        Path(self.idea.path, '.stage').write_text('Script')
        self.board['included']['lists'].append({'id': 'film', 'name': 'Film', 'type': 'active'})
        self.board['included']['cards'] = [{'id': 'immich', 'name': 'Self-Host Immich', 'listId': 'film'}]
        Path('videos/self-host-immich').mkdir()
        with patch('builtins.print'):
            plans = link_plans(self.planka, self.channel, self.board, ['Idea', 'Script', 'Film'])
        self.assertEqual([(p['idea'].name, p['stage']) for p in plans], [('self-host-immich', 'Film')])

    def test_duplicate_immich_cards_are_not_guessed(self):
        Path('videos/self-host-immich').mkdir()
        self.board['included']['lists'] += [{'id': 'ideas', 'name': 'Idea', 'type': 'active'},
                                           {'id': 'film', 'name': 'Film', 'type': 'active'}]
        self.board['included']['cards'] = [{'id': 'one', 'name': 'Self-Host Immich', 'listId': 'ideas'},
                                          {'id': 'two', 'name': 'Self-Host Immich', 'listId': 'film'}]
        with patch('builtins.print') as output:
            plans = link_plans(self.planka, self.channel, self.board, ['Film'])
        self.assertEqual(plans, [])
        self.assertIn('AMBIGUOUS self-host-immich', str(output.call_args_list))
        self.assertFalse(Path('videos/self-host-immich', CARDFILE).exists())

    def test_existing_id_beats_duplicate_name(self):
        self.board['included']['cards'] = [{'id': 'c1', 'name': 'project', 'listId': 'l1'},
                                          {'id': 'c2', 'name': 'project', 'listId': 'l2'}]
        plans = link_plans(self.planka, self.channel, self.board, ['Script'])
        self.assertEqual(plans[0]['card']['id'], 'c1')

    def test_different_title_matches_explicit_filename_field(self):
        Path(self.idea.path, CARDFILE).unlink()
        self.board['included']['cards'] = [{'id': 'c2', 'name': 'New YouTube title', 'listId': 'l1'}]
        self.board['included']['customFieldValues'] = [{'cardId': 'c2', 'customFieldId': 'f1', 'content': 'project'}]
        plans = link_plans(self.planka, self.channel, self.board, ['Script'])
        self.assertEqual(plans[0]['card']['id'], 'c2')

    def test_two_folders_cannot_claim_same_card(self):
        Path(self.idea.path, CARDFILE).unlink()
        # Different filesystem names with the same normalized card-title match.
        # A case-only difference cannot coexist on typical macOS volumes.
        Path('videos/pro-ject').mkdir()
        self.board['included']['cards'] = [{'id': 'c2', 'name': 'PROJECT', 'listId': 'l1'}]
        with patch('builtins.print'):
            self.assertEqual(link_plans(self.planka, self.channel, self.board, ['Script']), [])

    def test_pull_dry_run_never_changes_files_tags_or_planka(self):
        Path(self.idea.path, CARDFILE).unlink()
        self.board['included']['cards'] = [{'id': 'c2', 'name': 'project', 'listId': 'l1'}]
        before = Path('settings.ini').read_bytes()
        with patch.object(self.planka, '_request', return_value=self.board) as request, patch('flo.linking.update_tag') as tag, patch('builtins.print'):
            self.assertTrue(sync_from_planka(self.planka, self.channel, ['Script'], True))
        request.assert_called_once_with('GET', 'boards/b1')
        tag.assert_not_called()
        self.assertFalse(Path(self.idea.path, CARDFILE).exists())
        self.assertFalse(Path(self.idea.path, '.stage').exists())
        self.assertEqual(Path('settings.ini').read_bytes(), before)

    def test_pull_only_gets_board_and_updates_local_link_and_stage(self):
        self.board['included']['cards'] = [{'id': 'c1', 'name': 'Renamed project', 'listId': 'l2'}]
        with patch.object(self.planka, '_request', return_value=self.board) as request, patch('builtins.print'):
            self.assertTrue(sync_from_planka(self.planka, self.channel, ['Upload'], False))
        request.assert_called_once_with('GET', 'boards/b1')
        self.assertEqual(Path(self.idea.path, '.stage').read_text(), 'Upload')
        self.assertEqual(Path(self.idea.path, CARDFILE).read_text(), 'c1')

    def test_stage_tags_preserve_unrelated_finder_tags(self):
        fake_tags = type('Tags', (), {'remove': lambda *args: None, 'add': lambda *args: None})()
        with patch.object(mactag, 'USING_MAC', True), patch.object(mactag, 'mac_tag', fake_tags, create=True), patch.object(fake_tags, 'remove') as remove, patch.object(fake_tags, 'add') as add:
            mactag.update_tag('Idea', self.idea.path)
        remove.assert_called_once_with(mactag.STAGES, [self.idea.path])
        add.assert_called_once_with('Idea', self.idea.path)
        self.assertEqual(Path(self.idea.path, '.stage').read_text(), 'Idea')

    def test_new_idea_offline_cli(self):
        result = subprocess.run([sys.executable, str(REPO / 'new-idea.py'), 'possible-video', '-c', 'ttt', '--offline'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path('videos/possible-video/.stage').read_text(), 'Idea')

    def test_offline_idea_sync_creates_in_idea_without_moving(self):
        Path(self.idea.path, CARDFILE).unlink()
        with patch.object(self.planka, 'make_card', return_value=('c2', 'b1')) as create, patch.object(self.planka, 'add_filename_to_card', return_value=True), patch.object(self.planka, 'move_card') as move, patch('builtins.print'):
            self.planka.sync(self.idea, 'Idea', False, False)
        create.assert_called_once_with(self.idea, stage='Idea')
        move.assert_not_called()

