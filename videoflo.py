import os
import argparse
import configparser
from python_get_resolve import GetResolve


class VideoFlo():

    def __init__(self):
        # read settings file
        config = configparser.ConfigParser()
        config.read('settings.ini')
        self.config = config
        self.dir = config['main']['root_dir']
        self.channels = self._get_channels()

    def get_resolve(self):
        api = self.config['main']['api']
        return GetResolve()

    def _get_channels(self):
        return set(self.config.sections()) - set(['main', 'video'])

    # determine the channel for this video
    def get_channel(self, project, args):
        # first check to see if the channel argument was passed int
        if args.channel is not None:
            channel = self.config[args.channel]
            return channel

        # search all channel directories for the video
        for channel in self.channels:
            channel_path = self.config[channel]['path']
            project_path = os.path.join(self.dir, channel_path, project)
            print(project_path)
            if os.path.exists(project_path):
                return self.config[channel]
        return None

    # read command line arguments
    def get_arguments(self, channel_required=False):
        parser = argparse.ArgumentParser()
        parser.add_argument('name',
                            help='Name of video project')
        parser.add_argument('-c', '--channel',
                            choices=self.channels,
                            required=channel_required,
                            help='Channel associated with the video')
        args = parser.parse_args()
        return args
