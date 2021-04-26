# Export a DaVinci project and update the video directory tag accordingly

from flo.idea import Idea
from flo.trello import Trello
from flo.davinci import Davinci
from flo.videoflo import VideoFlo
from flo.mactag import update_tag


def go():
    davinci = Davinci()
    if davinci.resolve is None:
        return

    davinci.get_current_project()
    if davinci.project is None:
        print('Could not get current DaVinci project')
        return

    flo = VideoFlo()
    project_name = davinci.project.GetName()
    channel = flo.get_channel(project_name)
    if channel is None:
        return

    idea = Idea()
    idea.from_project(project_name, channel)
    if not idea.exists():
        print('Directory for {} not found'.format(project_name))
        return

    davinci.export_project(idea)
    update_tag('Render', idea.path)

    trello = Trello()
    trello.move_card(idea, 'Render')

go()

