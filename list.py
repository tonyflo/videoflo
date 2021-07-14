# Get a list of projects for a channel

import os
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.mactag import get_tags

def go():
    flo = VideoFlo()
    args = flo.get_channel_arguments()
    channel = Channel(flo.config, args.channel)
    projects = []
    for item in os.listdir(channel.path):
        path = os.path.join(channel.path, item)
        if not os.path.isdir(path):
            continue
        projects.append(path)

    tags = get_tags(projects)
    for k, v in sorted(tags.items(), key=lambda item: item[1]):
        print(v[0] + '\t' + os.path.basename(k))
go()
