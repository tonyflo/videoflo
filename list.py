# Get a list of projects for a channel

import operator
import os
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.mactag import get_tags

def go():
    flo = VideoFlo()
    args = flo.get_list_arguments()
    channel = Channel(flo.config, args.channel)
    projects = []
    for item in os.listdir(channel.path):
        path = os.path.join(channel.path, item)
        if not os.path.isdir(path):
            continue
        projects.append(path)

    tags = get_tags(projects)
    count = 0
    verbose = True if type(args.tags) is list else False
    for k, v in sorted(tags.items(), key=operator.itemgetter(1, 0)):
        tag = v[0] if v else 'NOTAG'
        if tag not in args.tags:
            continue
        if verbose:
            print(tag + '\t' + os.path.basename(k))
        else:
            print(os.path.basename(k))
        count += 1

    print('Video count: {}'.format(count))

go()
