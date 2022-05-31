# Class to help with command line arguments and reading the config file

import os
import argparse
import configparser
from flo.channel import Channel
from flo.const import SETTINGSFILE, STAGES


def dir_path(string):
    if os.path.isdir(string):
        return string
    raise argparse.ArgumentTypeError('Not a valid path: {}'.format(string))

class VideoFlo():

    def __init__(self):
        # read settings file
        config = configparser.ConfigParser()
        config.read(SETTINGSFILE)
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

    def _add_offline_arg(self, parser):
        parser.add_argument('--offline',
                            action='store_true',
                            required=False,
                            help='Work offline with no internet access')

    def _add_upload_args(self, parser):
        parser.add_argument('--dry-run',
                            action='store_true',
                            required=False,
                            help="Do checks only. Don't upload")
        parser.add_argument('--limit',
                            type=int,
                            default=0,
                            required=False,
                            help="Only upload this many videos")

    def _add_list_args(self, parser):
        parser.add_argument('-t', '--tags',
                            choices=STAGES,
                            default=STAGES,
                            required=False,
                            help='Tag associated with the video''s state')

    # command line arguments for an individual video idea
    def get_idea_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('name',
                            help='Name of video project')
        parser.add_argument('-p', '--path', type=dir_path,
                            help='Destination directory')
        self._add_channel_arg(parser)
        self._add_offline_arg(parser)
        args = parser.parse_args()
        return args

    def get_channel_arguments(self):
        parser = argparse.ArgumentParser()
        self._add_channel_arg(parser)
        self._add_offline_arg(parser)
        args = parser.parse_args()
        return args

    def get_render_arguments(self):
        parser = argparse.ArgumentParser()
        self._add_channel_arg(parser)
        parser.add_argument('--preview',
                            action='store_true',
                            required=False,
                            help='Render a non-final version of the video')
        self._add_offline_arg(parser)
        args = parser.parse_args()
        return args

    def get_init_arguments(self):
        parser = argparse.ArgumentParser()
        self._add_channel_arg(parser)
        args = parser.parse_args()
        return args

    def get_list_arguments(self):
        parser = argparse.ArgumentParser()
        self._add_channel_arg(parser)
        self._add_list_args(parser)
        self._add_offline_arg(parser)
        args = parser.parse_args()
        return args

    def get_upload_arguments(self):
        parser = argparse.ArgumentParser()
        self._add_channel_arg(parser)
        self._add_upload_args(parser)
        args = parser.parse_args()
        return args

    def get_finish_edit_arguments(self):
        parser = argparse.ArgumentParser()
        self._add_offline_arg(parser)
        args = parser.parse_args()
        return args

    # determine the channel for this video project
    def get_channel(self, project_name):
        num_found = 0
        the_channel = None
        for channel in self.channels:
            project_path = os.path.join(channel.path, project_name, '')
            if not os.path.exists(project_path):
                continue

            num_found = num_found + 1
            the_channel = channel

        if num_found == 1:
            return the_channel

        print('Found {} projects with name {}'.format(num_found, project_name))
        return None

