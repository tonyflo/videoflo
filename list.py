# Get a list of projects for a channel

import os
from flo.channel import Channel
from flo.videoflo import VideoFlo


def go():
    flo = VideoFlo()
    args = flo.get_channel_arguments()
    channel = Channel(flo.config, args.channel)
    for item in os.listdir(channel.path):
        path = os.path.join(channel.path, item)
        if not os.path.isdir(path):
            continue
        print(item)

go()
