# Automatically move any screen recordings to this project directory

import os
from flo.idea import Idea
from flo.planka import Planka
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
        planka = Planka()
        if not planka.lists_exist(['Edit'], idea.channel):
            return

        success = planka.move_card(idea, 'Edit')
        if not success:
            return

    idea.copy_screen_recordings(flo)

    update_tag('Edit', idea.path)

go()
