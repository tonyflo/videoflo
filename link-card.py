"""Link an existing local project to an existing Planka card without creating one."""

import argparse
import os

from flo.idea import Idea
from flo.planka import Planka
from flo.videoflo import VideoFlo


def go():
    flo = VideoFlo()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', help='Existing local project directory name')
    parser.add_argument('card_id', help='Existing Planka card ID from its URL')
    flo._add_channel_arg(parser)
    args = parser.parse_args()
    channel = next(channel for channel in flo.channels if channel.id == args.channel)
    idea = Idea()
    idea.from_project(args.name, channel)
    if not os.path.isdir(idea.path):
        parser.error('Local project directory does not exist')
    planka = Planka()
    board_id = planka._get_board(channel)
    if not board_id:
        return
    response = planka._request('GET', 'cards/{}'.format(args.card_id))
    if not response or response.get('item', {}).get('boardId') != board_id:
        parser.error('Card is not on the configured Planka board or could not be read')
    existing_id = planka._get_card(idea)
    if existing_id and existing_id != args.card_id:
        parser.error('Project is already linked to another Planka card')
    planka.save_card(args.card_id, idea)
    print('Linked {} to Planka card "{}"'.format(args.name, response['item']['name']))


if __name__ == '__main__':
    go()
