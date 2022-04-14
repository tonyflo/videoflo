# Open the folder associated with a project

from flo.idea import Idea
from flo.videoflo import VideoFlo
from flo.mactag import open_dir


def go():
    flo = VideoFlo()
    idea = Idea()
    idea.read_user_input(flo)
    if not idea.exists():
        print('Directory for {} not found'.format(idea.name))
        return

    open_dir(idea.path)

go()
