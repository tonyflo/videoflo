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
    def get_channel(self, project_name, channel_arg=None):
        # first check to see if the channel argument was passed int
        if channel_arg is not None:
            channel = self.config[args.channel]
            return channel

        # search all channel directories for the video
        for channel in self.channels:
            channel_path = self.config[channel]['path']
            project_path = os.path.join(self.dir, channel_path, project_name)
            if os.path.exists(project_path):
                return self.config[channel]
                # TODO: wrong return if multiple channels have same video name
        return None

    def _add_channel_arg(self, parser, channel_required=True):
        parser.add_argument('-c', '--channel',
                            choices=self.channels,
                            required=channel_required,
                            help='Channel associated with the video')

    # command line arguments for individual video
    def get_video_arguments(self, channel_required=True):
        parser = argparse.ArgumentParser()
        parser.add_argument('name',
                            help='Name of video project')
        self._add_channel_arg(parser, channel_required)
        args = parser.parse_args()
        return args

    # command line arguments for a batch of videos for a channel
    def get_channel_arguments(self):
        parser = argparse.ArgumentParser()
        self._add_channel_arg(parser)
        args = parser.parse_args()
        return args

    # return project directory
    def get_project_path(self, project_name, channel):
        project_path = os.path.join(self.dir, channel['path'], project_name)
        return project_path

