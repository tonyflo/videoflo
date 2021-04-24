# Video idea object

import os
from flo.const import metadata
from flo.channel import Channel


class Idea():

    def __init__(self):
        self.name = None
        self.channel = None
        self.path = None

    # instantiate an idea object from command line arguments
    def read_user_input(self, flo):
        args = flo.get_idea_arguments()
        self.channel = Channel(flo.config, args.channel)
        self.name = args.name
        if self.exists:
            self.path = self._get_idea_directory()

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
    def _get_idea_directory(self):
        idea_path = os.path.join(self.channel.path, self.name)
        return idea_path

    # create the idea directory for this video
    def make_directory(self):
        idea_path = self._get_idea_directory()
        try:
            os.mkdir(idea_path)
        except FileNotFoundError:
            print('Directory {} does not exist'.format(idea_path))
            return None
        except FileExistsError:
            print('Directory {} already exist'.format(idea_path))
            return None

        self.path = idea_path
        return idea_path

    # create files for the idea
    def make_files(self):
        file_list = list(metadata.values()) + ['notes.txt']
        for f in file_list:
            new_file = os.path.join(self.path, f)
            open(new_file, 'a').close()

    # create directories for the idea
    def make_directories(self):
        for folder in ['camera', 'screen']:
            new_folder = os.path.join(self.path, folder)
            os.mkdir(new_folder)

