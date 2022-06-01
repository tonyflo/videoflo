# Channel object

import os
from pathlib import Path
from flo.const import SETTINGSFILE, CARDFILE, STAGEFILE, STAGES


class Channel:

    def __init__(self, config, identifier):
        self.id = identifier # originates from config file channel section name
        self.name = config[self.id]['name'] # proper name of channel
        self.path_name = config[self.id]['path'] # subdirectory for this channel
        self.schedule = self._get_schedule(config)
        self.config = config
        try:
            self.timeline = config[self.id]['timeline'] # path to timeline
        except KeyError:
            self.timeline = None # timeline is optional
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

    # get the release schedule defined in the config file as a list of ints,
    # otherwise or if error, assume release schedule is daily
    def _get_schedule(self, config):
        msg_error = '''NOTE: Please define a valid release schedule for your
      channel in your settings.ini file where Monday is 1 and Sunday is 7.
      As an example, this would define your release schedule as Monday,
      Wednesday, and Friday:

         schedule = 1,3,5

      If you publish every Saturday, it would be:

         schedule = 6

      Defaulting to an every day release schedule. Please adjust your
      settings.ini file according to your release schedule as instructed above.       You are always free to change the due date on the Trello card.'''

        schedule = [1, 2, 3, 4, 5, 6, 7]
        default_schedule = ','.join([str(dow) for dow in schedule])
        msg_invalid = 'ERROR: Invalid ' + self.name + ' release day: {}'

        # read config file for release schedule
        try:
            config_schedule = config[self.id]['schedule']
        except KeyError:
            self._save_release_schedule(config, default_schedule)
            config_schedule = default_schedule
            print(msg_error)

        # parse days of week as integers
        raw_days = schedule
        try:
            raw_days = [int(dow) for dow in config_schedule.split(',')]
        except ValueError:
            print(msg_invalid.format(config_schedule))

        # validate release schedule list of days
        valid_days = [dow for dow in raw_days if 1 <= dow <= 7]
        if len(valid_days) != len(raw_days):
            invalid_days = set(raw_days) - set(valid_days)
            invalid_days_str = ','.join([str(day) for day in invalid_days])
            print(msg_invalid.format(invalid_days_str))
            valid_days = schedule

        return valid_days

    def _save_release_schedule(self, config, schedule):
        config.set(self.id, 'schedule', schedule)
        with open(SETTINGSFILE, 'w') as configfile:
            config.write(configfile)

    # get the channel's default description from the file as specified in the config
    def get_default_description(self):
        description = ''
        try:
            description_file = self.config[self.id]['description']
        except KeyError:
            return description
        try:
            with open(description_file) as f:
                description = f.read().strip()
        except FileNotFoundError:
            pass

        return description

    def find_path_for_id(self, card_id):
        channel_path = Path(self.path)
        for card_file in list(channel_path.rglob(CARDFILE)):
            with open(card_file) as f:
                if card_id != f.read().strip():
                    continue
                path = os.path.dirname(card_file)
                return path

        return None

    def get_list(self, stage_name):
        items = []
        channel_path = Path(self.path)
        for stage_file in list(channel_path.rglob(STAGEFILE)):
            with open(stage_file) as f:
                stage = f.read().strip()
                if stage == stage_name:
                    path = os.path.dirname(stage_file)
                    items.append(path)
        return items

