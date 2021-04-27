# Create structure for new video idea

from flo.idea import Idea
from flo.videoflo import VideoFlo
from flo.trello import Trello
from flo.mactag import add_tag


def go():
    flo = VideoFlo()
    idea = Idea()
    idea.read_user_input(flo)
    idea_directory = idea.make_directory()
    if idea_directory is None:
        return

    trello = Trello()
    success = trello.make_card(idea)
    if not success:
        return

    idea.make_files()
    idea.make_directories()

    add_tag('Script', idea.path, do_open=True)

go()
