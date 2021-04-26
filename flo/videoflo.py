import os
import argparse
import configparser
from flo.channel import Channel


class VideoFlo():

    def __init__(self):
        # read settings file
        config = configparser.ConfigParser()
        config.read('settings.ini')
        self.config = config
        self.root= config['main']['root_dir']
        self.channels = [Channel(self.config, c) for c in self._get_channels()]

    def _get_channels(self):
        return set(self.config.sections()) - set(['main', 'trello'])

    def _add_channel_arg(self, parser):
        parser.add_argument('-c', '--channel',
                            choices=[c.id for c in self.channels],
                            required=True,
                            help='Channel associated with the video')

    # command line arguments for an individual video idea
    def get_idea_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('name',
                            help='Name of video project')
        self._add_channel_arg(parser)
        args = parser.parse_args()
        return args

    # command line arguments for a batch of videos for a channel
    def get_channel_arguments(self):
        parser = argparse.ArgumentParser()
        self._add_channel_arg(parser)
        args = parser.parse_args()
        return args

    # determine the channel for this video project
    def get_channel(self, project_name):
        num_found = 0
        the_channel = None
        for channel in self.channels:
            project_path = os.path.join(channel.path, project_name)
            if not os.path.exists(project_path):
                continue

            num_found = num_found + 1
            the_channel = channel

        if num_found == 1:
            return the_channel

        print('Could not find channel for this project.')
        return None

