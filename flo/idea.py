# Video idea object

import os
import json
from glob import glob
from shutil import move
from flo.channel import Channel
from flo.const import CARDFILE, STATSFILE


class Idea():

    def __init__(self):
        self.name = None
        self.channel = None
        self.path = None
        self.offline = False

    # instantiate an idea object from command line arguments
    def read_user_input(self, flo):
        args = flo.get_idea_arguments()
        self.channel = Channel(flo.config, args.channel)
        self.name = args.name
        self.path = self._get_idea_directory(args.path)
        self.offline = args.offline

    # instantiate an idea object given a name and channel
    def from_project(self, project_name, channel):
        self.name = project_name
        self.channel = channel
        if self.exists:
            self.path = self._get_idea_directory()

    def exists(self):
        idea_path = self._get_idea_directory()
        return os.path.exists(idea_path)

    # get the path to the root of the idea directory
    def _get_idea_directory(self, path=None):
        root = self.channel.path if path is None else path
        idea_path = os.path.join(root, self.name)
        return idea_path

    # create the idea directory for this video
    def make_directory(self):
        idea_path = self.path
        try:
            os.mkdir(idea_path)
        except FileNotFoundError:
            dirname = os.path.dirname(idea_path)
            print('Directory {} does not exist'.format(dirname))
            return None
        except FileExistsError:
            print('Directory {} already exist'.format(idea_path))
            return None

        return idea_path

    # create files for the idea
    def make_files(self):
        file_list = ['notes.txt', CARDFILE]
        for f in file_list:
            new_file = os.path.join(self.path, f)
            open(new_file, 'a').close()

    # create directories for the idea
    def make_directories(self):
        for folder in ['camera']:
            new_folder = os.path.join(self.path, folder)
            os.mkdir(new_folder)

    # copy screen recordings to this video project's screen directory
    def copy_screen_recordings(self, flo):
        try:
            screen_recordings = flo.config['main']['screens']
        except KeyError:
            # assume the user does not have screen recordings and silently return
            return

        # check to see if there are even screen recordings to copy
        screen_recordings = glob(screen_recordings)
        if len(screen_recordings) == 0:
            return

        # create the screen recordings directory if it doesn't already exist
        screens_path = os.path.join(self.path, 'screen', '')
        if not os.path.exists(screens_path):
            os.mkdir(screens_path)

        # move the screen recordings
        for src in screen_recordings:
            move(src, screens_path)
            name = os.path.basename(src)
            print('Moved {}'.format(name))

    def save_render_stats(self, stats):
        stats_file = os.path.join(self.path, STATSFILE)
        with open(stats_file, 'w') as f:
            f.write(json.dumps(stats))

    def get_render_stats(self):
        stats = {}
        stats_file = os.path.join(self.path, STATSFILE)
        with open(stats_file) as f:
            stats = json.load(f)

        return stats

