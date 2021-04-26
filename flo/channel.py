# Channel object

import os


class Channel:

    def __init__(self, config, identifier):
        self.id = identifier # originates from config file channel section name
        self.name = config[self.id]['name'] # proper name of channel
        self.path_name = config[self.id]['path'] # subdirectory for this channel
        self.timeline = config[self.id]['timeline'] # path to template timeline
        self.path = os.path.join(config['main']['root_dir'], self.path_name)
        self.settings = {
            'FrameRate': config[self.id]['framerate'],
            'ResolutionWidth': config[self.id]['width'],
            'ResolutionHeight': config[self.id]['height'],
        }
        self._oauth2_setup(config)

    # oauth2 file for the YouTube API which won't exist until login
    def _oauth2_setup(self, config):
        root_dir = config['main']['root_dir']
        oauth2_file = '.oauth2-{}.json'.format(self.path_name)
        self.oauth = os.path.join(root_dir, oauth2_file)

