# YouTube video class

import os
from flo import youtube
from flo.const import metadata


class Video():

    def __init__(self, path, filename, channel, thumbnail):
        self.path = path
        self.file = filename
        self.video = os.path.join(self.path, self.file)
        self.thumbnail = thumbnail
        self.channel = channel
        self.category = 26 # TODO: hardcoded as How To & Style
        self.set_title()
        self.set_description()
        self.set_tags()

    # set the title of the video (only reads first line of file)
    def set_title(self):
        title_file = metadata['title']
        title_path = os.path.join(self.path, title_file)
        with open(title_path) as f:
            title = f.readline().strip()
            self.title = title

    # set the description of the video
    def set_description(self):
        description_file = metadata['description']
        description_path = os.path.join(self.path, description_file)
        with open(description_path) as f:
            description = f.read().strip()
            self.description = description

    # set the tags for the video
    def set_tags(self):
        tags_file = metadata['tags']
        tags_path = os.path.join(self.path, tags_file)
        with open(tags_path) as f:
            # read each line into a list element
            values = f.read().splitlines()
            # remove extra whitespace between characters and drop tags less
            # than 2 and greater than 100 characters
            tags = [' '.join(v.split()).strip(',') for v in values if 2 <= len(v) <= 100]
            self.tags = tags

    # get the lenght of the tags
    def get_tags_len(self):
            tags = self.tags
            # each tag over 1 has a hidden comma and any tag with whitespace
            # has hidden quotes, so count these too
            length = sum([len(t)+3 if ' ' in t else len(t)+1 for t in tags])-1
            return length

    # check for a good title
    # TODO: check for title longer than 70 due to truncation?
    def check_title(self):
        if self.title is None or len(self.title) == 0:
            print('FIX: No title found for {}'.format(self.file))
            return False

        if len(self.title) > 100:
            print('FIX: Title over 100 characters for {}'.format(self.title))
            return False

        return True

    # check tags against YouTube limits
    # TODO: check for duplicate tags
    def check_tags(self):
        if self.tags is None or len(self.tags) == 0:
            print('FIX: No tags found for {}'.format(self.file))
            return False

        if self.get_tags_len() > 500:
            print('FIX: Tags for {} over 500 characters.'.format(self.file))
            return False

        return True

    # check for description
    def check_description(self):
        if self.description is None or len(self.description) == 0:
            print('FIX: No description found for {}'.format(self.file))
            return False

        return True

    # upload video to YouTube and if successful, return the video id
    def upload(self):
        video_id = youtube.upload(self)
        return video_id

