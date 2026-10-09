import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from reconcile import build_plan, apply_plan
from flo.const import CARDFILE


class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.board = {'included': {
            'lists': [{'id': 'i', 'name': 'Idea', 'type': 'active'},
                      {'id': 'p', 'name': 'Published', 'type': 'active'}],
            'cards': [{'id': 'one', 'name': 'My Idea', 'listId': 'i'},
                      {'id': 'two', 'name': 'Cpanel vs Spanel', 'listId': 'p'}]}}
    def tearDown(self):
        self.temp.cleanup()
    def test_confirmed_mapping_reuses_media_folder_and_creates_leftover(self):
        (self.root / 'cpanel-alternatives-2026').mkdir()
        (self.root / 'cpanel-alternatives-2026' / 'video.mov').write_text('media')
        actions, notes = build_plan(self.root, self.board,
            ['cpanel-alternatives-2026=Cpanel vs Spanel'])
        self.assertEqual([(a['kind'], a['name']) for a in actions],
            [('LINK', 'cpanel-alternatives-2026'), ('CREATE', 'my-idea')])
        self.assertEqual((self.root / 'cpanel-alternatives-2026' / 'video.mov').read_text(), 'media')
        self.assertFalse((self.root / 'my-idea').exists())
    def test_trash_and_ignored_folders_preview_is_read_only(self):
        for name in ('Planka Test', '108_PANA'):
            (self.root / name).mkdir()
        actions, notes = build_plan(self.root, self.board, trash=['Planka Test'], ignore=['108_PANA'])
        self.assertEqual(sum(a['kind'] == 'TRASH' for a in actions), 1)
        self.assertIn('IGNORE 108_PANA', notes)
        self.assertTrue((self.root / 'Planka Test').is_dir())
        self.assertTrue((self.root / '108_PANA').is_dir())
    def test_id_links_are_idempotent_and_do_not_create_duplicate_folder(self):
        (self.root / 'my-idea').mkdir()
        (self.root / 'my-idea' / CARDFILE).write_text('one')
        actions, _ = build_plan(self.root, self.board)
        self.assertEqual(sum(a['kind'] == 'CREATE' and a['card']['id'] == 'one' for a in actions), 0)
    def test_duplicate_cards_require_explicit_id(self):
        (self.root / 'my-idea').mkdir()
        self.board['included']['cards'].append({'id': 'three', 'name': 'My Idea', 'listId': 'i'})
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            build_plan(self.root, self.board)
        actions, _ = build_plan(self.root, self.board, ['my-idea=one'])
        self.assertEqual(actions[0]['card']['id'], 'one')
        self.assertTrue(any(a['kind'] == 'CREATE' and a['card']['id'] == 'three' for a in actions))
    def test_existing_wrong_link_is_never_overwritten(self):
        (self.root / 'custom').mkdir()
        (self.root / 'custom' / CARDFILE).write_text('other')
        with self.assertRaisesRegex(ValueError, 'another card'):
            build_plan(self.root, self.board, ['custom=one'])
    def test_traversal_and_symlink_trashing_rejected(self):
        with self.assertRaises(ValueError):
            build_plan(self.root, self.board, trash=['../other'])
        (self.root / 'link').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            build_plan(self.root, self.board, trash=['link'])
    def test_apply_creates_structure_and_only_local_link_and_tag(self):
        actions = [{'kind': 'CREATE', 'name': 'my-idea',
                    'card': self.board['included']['cards'][0], 'stage': 'Idea'}]
        planka = Mock()
        with patch('reconcile.update_tag') as tag:
            apply_plan(self.root, actions, planka)
        self.assertTrue((self.root / 'my-idea' / 'camera').is_dir())
        self.assertTrue((self.root / 'my-idea' / 'notes.txt').exists())
        tag.assert_called_once_with('Idea', str(self.root / 'my-idea'))
        planka.save_card.assert_called_once()
        planka._request.assert_not_called()

    def test_apply_moves_to_trash_and_keeps_ignored_media(self):
        (self.root / 'old').mkdir()
        (self.root / 'old' / 'clip.mov').write_text('old media')
        (self.root / '108_PANA').mkdir()
        (self.root / '108_PANA' / 'clip.mov').write_text('keep')
        home = self.root / 'home'
        home.mkdir()
        with patch('reconcile.Path.home', return_value=home):
            apply_plan(self.root, [{'kind': 'TRASH', 'name': 'old'}], Mock())
        self.assertFalse((self.root / 'old').exists())
        moved = list((home / '.Trash').iterdir())
        self.assertEqual(len(moved), 1)
        self.assertEqual((moved[0] / 'clip.mov').read_text(), 'old media')
        self.assertEqual((self.root / '108_PANA' / 'clip.mov').read_text(), 'keep')
