# Create a DaVinci Resolve project

from flo.idea import Idea
from flo.trello import Trello
from flo.davinci import Davinci
from flo.videoflo import VideoFlo

def go():
    flo = VideoFlo()
    idea = Idea()
    idea.read_user_input(flo)
    if not idea.exists():
        print('Directory for {} not found'.format(idea.name))
        return

    davinci = Davinci()
    if davinci.resolve is None:
        return

    davinci.set_project_manager()
    if davinci.project_manager is None:
        return

    davinci.create_project(idea)
    if davinci.project is None:
        return

    davinci.import_timeline()
    davinci.import_files()
    davinci.workspace_setup()

    trello = Trello()
    trello.move_card(idea, 'Edit')

go()
