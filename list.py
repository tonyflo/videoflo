# Get a list of projects for a channel

import operator
import os
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.mactag import get_tags
from flo.const import STAGES

def go():
    flo = VideoFlo()
    args = flo.get_list_arguments()
    channel = Channel(flo.config, args.channel)
    projects = []
    try:
        plist = os.listdir(channel.path)
    except FileNotFoundError:
        print("The path {} is not accessible".format(channel.path))
        return

    for item in plist:
        path = os.path.join(channel.path, item)
        if not os.path.isdir(path):
            continue
        projects.append(path)

    tags = get_tags(projects)
    count = 0
    counts = {key: 0 for key in STAGES}
    verbose = True if type(args.tags) is list else False
    for k, v in sorted(tags.items(), key=operator.itemgetter(1, 0)):
        tag = v[0] if v else 'NOTAG'
        if tag not in args.tags:
            continue
        if verbose:
            print(tag + '\t' + os.path.basename(k))
            counts[tag] = counts[tag] + 1
        else:
            print(os.path.basename(k))
        count += 1

    print('--------------------')
    if verbose:
        for k, v in counts.items():
            print("   {}:\t{}".format(k,v ))
        print('--------------------')
    print('   Total:\t{}'.format(count))

go()
