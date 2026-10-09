# Initialize Planka and YouTube

from flo.videoflo import VideoFlo
from flo.planka import Planka
from flo.channel import Channel
from flo.const import STAGES


def go():
    flo = VideoFlo()
    args = flo.get_init_arguments()
    channel = Channel(flo.config, args.channel)

    planka = Planka()
    if not planka.lists_exist(STAGES, channel, create=True):
        return

    if not planka.add_custom_fields(channel):
        print('Unable to initialize Planka custom fields. Check board editor permissions.')

go()
