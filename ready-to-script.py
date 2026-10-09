"""Commit an existing idea to production: Idea -> Script."""
from flo.idea import Idea
from flo.videoflo import VideoFlo
from flo.planka import Planka
from flo.mactag import update_tag


def go():
    flo = VideoFlo()
    idea = Idea()
    idea.read_user_input(flo)
    if not idea.exists():
        print('Directory for {} not found'.format(idea.name))
        return
    if not idea.offline and not Planka().ready_to_script(idea):
        print('Unable to move the linked idea to Script')
        return
    update_tag('Script', idea.path)


if __name__ == '__main__':
    go()
