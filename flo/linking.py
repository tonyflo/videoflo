"""Read-only Planka -> local folder linking and stage adoption."""
import os
import re
import unicodedata
from collections import Counter
from types import SimpleNamespace

from flo.const import STAGES
from flo.mactag import update_tag


def normalized_name(value):
    # Exact words, ignoring spacing, punctuation and case. No fuzzy matching.
    return re.sub(r'[^\w]+', '', unicodedata.normalize('NFKC', value).casefold().replace('_', ''))


def link_plans(planka, channel, board, stages):
    included = board.get('included', {})
    lists = {item['id']: item['name'] for item in planka._active_lists(board)}
    all_cards = included.get('cards', [])
    cards = {card['id']: card for card in all_cards}
    filename_fields = {field['id'] for field in included.get('customFields', [])
                       if field['name'] == 'filename'}
    filenames = {}
    for value in included.get('customFieldValues', []):
        if value['customFieldId'] in filename_fields:
            filenames.setdefault(value['cardId'], []).append(value.get('content', ''))
    plans = []
    for name in sorted(os.listdir(channel.path)):
        path = os.path.join(channel.path, name)
        if not os.path.isdir(path):
            continue
        idea = SimpleNamespace(name=name, path=path, channel=channel)
        existing_id = planka._get_card(idea)
        if existing_id:
            matches = [cards[existing_id]] if existing_id in cards else []
            if not matches:
                print('SKIP {}: linked card is unavailable on this board'.format(name))
                continue
        else:
            matches = [card for card in all_cards if name in filenames.get(card['id'], [])]
            if not matches:
                key = normalized_name(name)
                matches = [card for card in all_cards if key and normalized_name(card['name']) == key]
            if len(matches) != 1:
                if matches:
                    print('AMBIGUOUS {}: {}'.format(name, ', '.join(
                        '{} [{}; {}]'.format(card['name'], lists.get(card['listId'], '?'), card['id'])
                        for card in matches)))
                else:
                    print('UNMATCHED {}: no existing card matched; nothing created'.format(name))
                continue
        card = matches[0]
        stage = lists.get(card['listId'])
        if stage not in stages or stage not in STAGES:
            continue
        plans.append({'idea': idea, 'card': card, 'stage': stage, 'linked': bool(existing_id)})
    counts = Counter(plan['card']['id'] for plan in plans)
    unique = []
    for plan in plans:
        if counts[plan['card']['id']] != 1:
            print('AMBIGUOUS {}: multiple folders match the same card'.format(plan['idea'].name))
        else:
            unique.append(plan)
    return unique


def sync_from_planka(planka, channel, stages, dry_run):
    # Do not invoke interactive board selection, which could write settings in a dry run.
    board_id = planka.config.get(channel.id, 'planka_board_id', fallback='').strip()
    if not board_id:
        raise ValueError('Set planka_board_id in the channel settings or run init first')
    if not os.path.isdir(channel.path):
        raise ValueError('Channel folder is unavailable: {}'.format(channel.path))
    board = planka._board(board_id)
    if board is None:
        return False
    plans = link_plans(planka, channel, board, stages)
    for plan in plans:
        idea, card, stage = plan['idea'], plan['card'], plan['stage']
        print('{}{} -> "{}" [{}; {}]'.format(
            'WOULD LINK ' if dry_run else 'LINK ', idea.name, card['name'], stage, card['id']))
        if not dry_run:
            # Update tags before the ID so a tagging failure does not imply completed linking.
            update_tag(stage, idea.path)
            planka.save_card(card['id'], idea)
    print('{} existing folder(s) {}; no Planka cards created or moved.'.format(
        len(plans), 'would be linked/tagged' if dry_run else 'linked/tagged'))
    return True
