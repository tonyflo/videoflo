# YouTube video class

import os
from datetime import datetime
from flo import youtube
from flo.const import DATE_FORMAT


class Video():

    def __init__(self, path, filename, channel, metadata, thumbnail, idea):
        self.path = path
        self.file = filename
        self.video = os.path.join(self.path, self.file)
        self.thumbnail = thumbnail
        self.channel = channel
        self.idea = idea
        self.category = 26 # TODO: hardcoded as How To & Style
        self.title = metadata['title']
        self.description = metadata['description']
        self.publish_at = self._set_publish_time(metadata['scheduled'])
        self.tags = metadata['tags']

    def _set_publish_time(self, publish_at):
        if publish_at is None:
            return None

        dt = datetime.strptime(publish_at, DATE_FORMAT)
        return dt

    # get the length of the tags according to how YouTube counts them
    def _get_tags_len(self, tags):
            # each tag over 1 has a hidden comma and any tag with whitespace
            # has hidden quotes, so count these too
            length = sum([len(t)+3 if ' ' in t else len(t)+1 for t in tags])-1
            return length

    # check for a good title
    # TODO: check for title longer than 70 due to truncation?
    def check_title(self):
        status = True
        title_len = len(self.title)
        if self.title is None or title_len < 0:
            status = False
            print('FIX: No title found')
        elif ' ' not in self.title:
            status = False
            print('FIX: No spaces found in title: {}'.format(self.title))
        elif title_len < 10:
            status = False
            print('FIX: Very short title: {}'.format(self.title))
        elif title_len > 100:
            status = False
            print('FIX: Title over 100 characters for {}'.format(self.title))

        return status

    # check tags against YouTube limits
    # TODO: check for duplicate tags
    def check_tags(self):
        if self.tags is None or len(self.tags) == 0:
            print('FIX: No tags found')
            return False

        # filter out tags that are too long or short
        tags = [t for t in self.tags if 2 <= len(t) <= 100]
        diff = set(self.tags) - set(tags)
        if len(diff) > 0:
            removed = ','.join(diff)
            print('WARN: The following tags were removed: {}'.format(removed))

        # check again in case the filter removed them all
        if tags is None or len(tags) == 0:
            print('FIX: No tags found')
            return False

        if self._get_tags_len(tags) > 500:
            print('FIX: Tags over 500 characters')
            return False

        self.tags = tags
        return True

    # check for description
    def check_description(self):
        status = True
        description_len = len(self.description)
        if self.description is None or description_len == 0:
            status = False
            print('FIX: No description found')
        elif description_len < 10:
            status = False
            print('FIX: Very short description: {}'.format(self.description))

        return status

    # check for a valid scheduled date and time
    def check_date(self):
        if self.publish_at is None:
            print('FIX: No scheduled date')
            return False

        if datetime.now() > self.publish_at:
            print('FIX: Scheduled date {} is past'.format(self.publish_at))
            return False

        self.publish_at = self.publish_at.isoformat()
        return True

    # upload video to YouTube and if successful, return the video id
    def upload(self):
        video_id = youtube.upload(self)
        return video_id

