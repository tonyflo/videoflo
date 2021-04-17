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

    def get_channel_dirs(self):
        return [self.config[channel]['path'] for channel in self.channels]

    def get(self, key, value):
        return self.config[key][value]

