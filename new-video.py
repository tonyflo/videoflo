# Create structure for new video idea

from flo.idea import Idea
from flo.videoflo import VideoFlo
from flo.trello import Trello
from flo.mactag import add_tag


def go():
    flo = VideoFlo()
    idea = Idea()
    idea.read_user_input(flo)

    trello = Trello()
    if not trello.lists_exist(['Script'], idea.channel):
        return
    card_id = trello.make_card(idea)

    idea_directory = idea.make_directory()
    if idea_directory is None:
        trello.delete_card(card_id)
        return
    idea.make_files()
    idea.make_directories()

    trello.save_card(card_id, idea)

    add_tag('Script', idea.path, do_open=True)

go()
