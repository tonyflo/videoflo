# Initialize Trello and YouTube

from flo.videoflo import VideoFlo
from flo.trello import Trello
from flo.channel import Channel
from flo.const import STAGES


def go():
    flo = VideoFlo()
    args = flo.get_init_arguments()
    channel = Channel(flo.config, args.channel)

    trello = Trello()
    if not trello.lists_exist(STAGES, channel, create=True):
        return

    trello.add_custom_fields(channel)

go()
