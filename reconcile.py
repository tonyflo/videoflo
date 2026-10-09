"""Reconcile existing local folders with Planka; preview unless --apply is supplied."""
import argparse
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from flo.const import CARDFILE, STAGES
from flo.linking import normalized_name
from flo.mactag import update_tag
from flo.planka import Planka


def child_name(value):
    if not value or value in ('.', '..') or Path(value).name != value:
        raise ValueError('Expected a folder name, not a path: {}'.format(value))
    return value


def slug(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')[:120] or 'video'


def build_plan(root, board, matches=(), trash=(), ignore=()):
    root = Path(root)
    if not root.is_dir():
        raise ValueError('Channel folder is unavailable: {}'.format(root))
    included = board.get('included', {})
    stage_by_list = {item['id']: item['name'] for item in included.get('lists', [])
                     if item.get('type') in ('active', 'closed') and item['name'] in STAGES}
    cards = {card['id']: card for card in included.get('cards', [])
             if card['listId'] in stage_by_list}
    trash = {child_name(name) for name in trash}
    ignore = {child_name(name) for name in ignore}
    if trash & ignore:
        raise ValueError('A folder cannot be both ignored and trashed')
    explicit = {}
    for match in matches:
        name, sep, target = match.partition('=')
        child_name(name)
        if not sep or not target or name in explicit or name in trash or name in ignore:
            raise ValueError('Invalid or duplicate --match: {}'.format(match))
        candidates = [card for card in cards.values()
                      if card['id'] == target or normalized_name(card['name']) == normalized_name(target)]
        if len(candidates) != 1:
            raise ValueError('--match {} resolved to {} cards; use the card ID for duplicates'.format(match, len(candidates)))
        if not (root / name).is_dir() or (root / name).is_symlink():
            raise ValueError('Confirmed folder is unavailable: {}'.format(name))
        explicit[name] = candidates[0]

    filenames = {}
    field_ids = {field['id'] for field in included.get('customFields', [])
                 if field['name'] == 'filename'}
    for value in included.get('customFieldValues', []):
        if value['customFieldId'] in field_ids:
            filenames.setdefault(value['cardId'], []).append(value.get('content', ''))

    actions, notes, claimed = [], [], {}
    for path in sorted(root.iterdir()):
        name = path.name
        if name in ignore:
            notes.append('IGNORE {}'.format(name))
            continue
        if name in trash:
            if not path.is_dir() or path.is_symlink():
                raise ValueError('Refusing to trash a non-folder or symlink: {}'.format(name))
            actions.append({'kind': 'TRASH', 'name': name})
            continue
        if not path.is_dir() or path.is_symlink():
            continue
        id_file = path / CARDFILE
        old_id = id_file.read_text().strip() if id_file.exists() else ''
        if name in explicit:
            card = explicit[name]
            if old_id and old_id != card['id']:
                raise ValueError('{} is already linked to another card; refusing to overwrite'.format(name))
        elif old_id:
            card = cards.get(old_id)
            if card is None:
                notes.append('KEEP {}: linked card unavailable or unsupported stage'.format(name))
                continue
        else:
            candidates = [card for card in cards.values() if name in filenames.get(card['id'], [])]
            if not candidates:
                candidates = [card for card in cards.values()
                              if normalized_name(name) == normalized_name(card['name'])]
            if len(candidates) > 1:
                raise ValueError('Ambiguous folder {}: use --match folder=CARD_ID'.format(name))
            if not candidates:
                notes.append('KEEP {}: no matching card'.format(name))
                continue
            card = candidates[0]
        if card['id'] in claimed:
            raise ValueError('Folders {} and {} both claim card {}'.format(claimed[card['id']], name, card['id']))
        claimed[card['id']] = name
        actions.append({'kind': 'LINK', 'name': name, 'card': card,
                        'stage': stage_by_list[card['listId']]})

    # Reserve all current folder names, including ignored and discarded folders.
    # Never reuse an unrelated folder merely because its slug matches a title.
    used_names = {path.name.casefold() for path in root.iterdir()}
    for card in sorted(cards.values(), key=lambda card: (stage_by_list[card['listId']], card['name'], card['id'])):
        if card['id'] in claimed:
            continue
        name = slug(card['name'])
        if name.casefold() in used_names:
            name = '{}-{}'.format(name, card['id'])
        while name.casefold() in used_names:
            name += '-new'
        used_names.add(name.casefold())
        actions.append({'kind': 'CREATE', 'name': name, 'card': card,
                        'stage': stage_by_list[card['listId']]})
    for name in sorted(trash):
        if not (root / name).exists():
            notes.append('ALREADY ABSENT {}'.format(name))
    return actions, notes


def apply_plan(root, actions, planka):
    root = Path(root)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    for action in actions:
        path = root / action['name']
        if action['kind'] == 'TRASH':
            trash_dir = Path.home() / '.Trash'
            trash_dir.mkdir(exist_ok=True)
            target = trash_dir / '{}-videoflo-{}'.format(path.name, stamp)
            number = 1
            while target.exists():
                target = trash_dir / '{}-videoflo-{}-{}'.format(path.name, stamp, number)
                number += 1
            shutil.move(str(path), str(target))
            print('Moved to Trash: {}'.format(target))
            continue
        if action['kind'] == 'CREATE':
            path.mkdir()
            (path / 'camera').mkdir()
            (path / 'notes.txt').touch()
        # Save the validated ID first so rerunning after a tag failure cannot create duplicates.
        planka.save_card(action['card']['id'], SimpleNamespace(path=str(path)))
        update_tag(action['stage'], str(path))


def go():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-c', '--channel', required=True)
    parser.add_argument('--match', action='append', default=[], metavar='FOLDER=CARD_TITLE_OR_ID')
    parser.add_argument('--trash', nargs='+', default=[], metavar='FOLDER')
    parser.add_argument('--ignore', nargs='+', default=[], metavar='FOLDER')
    parser.add_argument('--apply', action='store_true', help='Apply the preview to local folders only')
    args = parser.parse_args()
    planka = Planka()
    try:
        board_id = planka.config.get(args.channel, 'planka_board_id', fallback='').strip()
        if not board_id:
            raise ValueError('Set planka_board_id in your channel settings first')
        root = Path(os.path.expanduser(planka.config['main']['root_dir'])) / planka.config[args.channel]['path']
        board = planka._board(board_id)
        if board is None:
            return 1
        actions, notes = build_plan(root, board, args.match, args.trash, args.ignore)
        print('Channel folder: {}'.format(root))
        print('APPLY' if args.apply else 'PREVIEW ONLY')
        for note in notes:
            print(note)
        for action in actions:
            if action['kind'] == 'TRASH':
                print('TRASH {}'.format(action['name']))
            else:
                print('{} {} -> "{}" [{}; {}]'.format(
                    action['kind'], action['name'], action['card']['name'],
                    action['stage'], action['card']['id']))
        print('{} trash, {} existing links, {} new folders. No Planka writes.'.format(
            sum(a['kind'] == 'TRASH' for a in actions),
            sum(a['kind'] == 'LINK' for a in actions),
            sum(a['kind'] == 'CREATE' for a in actions)))
        if args.apply:
            if sys.platform != 'darwin':
                raise ValueError('--apply is intended for the Mac workstation')
            apply_plan(root, actions, planka)
            print('Done. Media in linked folders was not changed; discarded folders are in Trash.')
        else:
            print('Review the plan, then rerun the same command with --apply.')
    except (ValueError, KeyError, OSError) as error:
        print('ERROR: {}'.format(error))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(go())
