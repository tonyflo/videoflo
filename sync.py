# Create structure for new video idea

import os
from pathlib import Path
from flo.idea import Idea
from flo.trello import Trello
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.const import STAGES, STAGEFILE


def go():
    flo = VideoFlo()
    args = flo.get_init_arguments()
    channel = Channel(flo.config, args.channel)

    channel_path = Path(channel.path)
    for stage_file in list(channel_path.rglob(STAGEFILE)):
        proj_name = os.path.basename(os.path.dirname(stage_file))
        with open(stage_file) as f:
            stage = f.read().strip()
            if stage not in STAGES:
                print("Invalid name '{}' at {}".format(stage, stage_file))
                continue

        # instantiate idea object
        idea = Idea()
        idea.from_project(proj_name, channel)
        if not idea.exists():
            print('Directory for {} not found'.format(path))
            continue
        trello = Trello()
        trello.sync(idea, stage)

go()
