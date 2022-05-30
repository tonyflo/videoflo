# Automatically move any screen recordings to this project directory

import os
from flo.idea import Idea
from flo.trello import Trello
from flo.videoflo import VideoFlo
from flo.mactag import update_tag


def go():
    flo = VideoFlo()
    idea = Idea()
    idea.read_user_input(flo)

    if not idea.exists():
        print('Directory for {} not found'.format(idea.name))
        return

    if not idea.offline:
        trello = Trello()
        if not trello.lists_exist(['Edit'], idea.channel):
            return

        success = trello.move_card(idea, 'Edit')
        if not success:
            return

    idea.copy_screen_recordings(flo)

    update_tag('Edit', idea.path)

go()
