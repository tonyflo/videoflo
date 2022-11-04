# Create structure for new video idea

import os
from glob import glob
from flo.idea import Idea
from flo.trello import Trello
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.const import STAGES, STAGEFILE


def go():
    flo = VideoFlo()
    args = flo.get_sync_arguments()
    dry_run = args.dry_run
    verbose = args.verbose
    channel = Channel(flo.config, args.channel)

    if dry_run:
        print('THIS IS JUST A DRY RUN')

    stage_file_list = glob(os.path.join(channel.path, '*', STAGEFILE))
    for stage_file in stage_file_list:
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
        trello.sync(idea, stage, dry_run, verbose)

    if len(stage_file_list) == 0:
        print('No videos found for {}'.format(channel.name))
    elif dry_run:
        print('THIS WAS JUST A DRY RUN')

go()
