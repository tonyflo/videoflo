# Automatically move any screen recordings to this project directory

import os
from glob import glob
from shutil import move
from flo.idea import Idea
from flo.trello import Trello
from flo.videoflo import VideoFlo
from flo.mactag import update_tag


# copy screen recordings to this video project's screen directory
def copy_screen_recordings(flo, idea):
    try:
        screen_recordings_path = flo.config['main']['screen_recordings_dir']
    except KeyError:
        # assume that the user does not have screen recordings and silently return
        return

    file_pattern = 'Screen Recording*.mov'
    screen_recordings = glob(os.path.join(screen_recordings_path, file_pattern))

    # check to see if there are even screen recordings to copy
    if len(screen_recordings) == 0:
        return

    # create the screen recordings directory if it doesn't already exist
    screens_path = os.path.join(idea.path, 'screen', '')
    if not os.path.exists(screens_path):
        os.mkdir(screens_path)

    # move the screen recordings
    for src in screen_recordings:
        move(src, screens_path)
        name = os.path.basename(src)
        print('Moved {}'.format(name))

def go():
    flo = VideoFlo()
    idea = Idea()
    idea.read_user_input(flo)
    if not idea.exists():
        print('Directory for {} not found'.format(idea.name))
        return

    copy_screen_recordings(flo, idea)

    trello = Trello()
    success = trello.move_card(idea, 'Import')
    if not success:
        return

    update_tag('Import', idea.path)

go()
