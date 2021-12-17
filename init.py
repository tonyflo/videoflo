# Initialize Trello and YouTube

from flo.videoflo import VideoFlo
from flo.trello import Trello
from flo.channel import Channel
from flo.const import TRELLO_LISTS


def go():
    flo = VideoFlo()
    args = flo.get_channel_arguments()
    channel = Channel(flo.config, args.channel)

    trello = Trello()
    if not trello.lists_exist(TRELLO_LISTS, channel, create=True):
        return

    trello.add_custom_fields(channel)

go()
