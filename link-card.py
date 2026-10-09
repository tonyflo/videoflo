"""Link an existing local project to an existing Planka card without creating one."""

import argparse
import os

from flo.idea import Idea
from flo.const import STAGES
from flo.mactag import update_tag
from flo.planka import Planka
from flo.videoflo import VideoFlo


def go():
    flo = VideoFlo()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', help='Existing local project directory name')
    parser.add_argument('card_id', help='Existing Planka card ID from its URL')
    parser.add_argument('--adopt-stage', action='store_true',
                        help='Set the local stage and Finder tag to the existing card list')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing local files/tags')
    flo._add_channel_arg(parser)
    args = parser.parse_args()
    channel = next(channel for channel in flo.channels if channel.id == args.channel)
    idea = Idea()
    idea.from_project(args.name, channel)
    if not os.path.isdir(idea.path):
        parser.error('Local project directory does not exist')
    planka = Planka()
    board_id = planka.config.get(channel.id, 'planka_board_id', fallback='').strip()
    if not board_id:
        parser.error('Set planka_board_id in channel settings or run init first')
    if not board_id:
        return
    response = planka._request('GET', 'cards/{}'.format(args.card_id))
    if not response or response.get('item', {}).get('boardId') != board_id:
        parser.error('Card is not on the configured Planka board or could not be read')
    existing_id = planka._get_card(idea)
    if existing_id and existing_id != args.card_id:
        parser.error('Project is already linked to another Planka card')
    if args.adopt_stage:
        list_response = planka._request('GET', 'lists/{}'.format(response['item']['listId']))
        if not list_response or list_response.get('item', {}).get('name') not in STAGES:
            parser.error('Card list is not a supported VideoFlo stage')
        stage = list_response['item']['name']
        print('{}local stage/Finder tag: {}'.format('Would set ' if args.dry_run else 'Set ', stage))
        if not args.dry_run:
            update_tag(stage, idea.path)
    if args.dry_run:
        print('Would link {} to Planka card "{}"'.format(args.name, response['item']['name']))
        return
    planka.save_card(args.card_id, idea)
    print('Linked {} to Planka card "{}"'.format(args.name, response['item']['name']))


if __name__ == '__main__':
    go()
