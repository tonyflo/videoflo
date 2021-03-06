# Mark this video project as ready to film

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

    idea.copy_screen_recordings(flo)

    trello = Trello()
    if not trello.lists_exist(['Film'], idea.channel):
        return

    success = trello.move_card(idea, 'Film')
    if not success:
        return

    update_tag('Film', idea.path)

go()
