# Create structure for new video project

import os
import sys
import mac_tag # TODO not cross platform
import argparse
from subprocess import call
from videoflo import init
config = init()

# read command line arguments
def get_arguments(channels):
    parser = argparse.ArgumentParser()
    parser.add_argument('name',
                        help='Name of video project')
    parser.add_argument('-c', '--channel',
                        choices=channels,
                        required=True,
                        help='Channel associated with the video')
    args = parser.parse_args()
    return args

# create the project directory for this video
def make_project_directory(name, channel, root_dir):
    channel_dir = config[channel]['path']
    proj_dir = os.path.join(root_dir, channel_dir, name)
    try:
        os.mkdir(proj_dir)
    except FileNotFoundError:
        print('Directory {} does not exist'.format(proj_dir))
        return None
    return proj_dir

# create files for the project
def make_files(proj_dir):
    for txt in ['yt.txt', 'notes.txt']:
        new_file = os.path.join(proj_dir, txt)
        open(new_file, 'a').close()

# create directories for the project
def make_directories(proj_dir):
    for folder in ['gh5', 'screen']:
        new_folder = os.path.join(proj_dir, folder)
        os.mkdir(new_folder)

def go():
    channels = set(config.sections()) - set(['main', 'video'])
    args = get_arguments(channels)

    name = args.name
    channel = args.channel
    root_dir = config['main']['root_dir']

    proj_dir = make_project_directory(name, channel, root_dir)
    if proj_dir is not None:
        make_files(proj_dir)
        make_directories(proj_dir)
        mac_tag.add(['Script'], [proj_dir])
        call(["open", proj_dir])

go()
