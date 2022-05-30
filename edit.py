# Create a DaVinci Resolve project

from flo.idea import Idea
from flo.davinci import Davinci
from flo.videoflo import VideoFlo
from flo.trello import Trello
from flo.mactag import update_tag


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

    is_new = davinci.open_project(idea)
    if davinci.project is None:
        return

    if is_new:
        davinci.import_timeline()
        davinci.import_files()
        davinci.workspace_setup()

    if not idea.offline:
        trello = Trello()
        if not trello.lists_exist(['Finish'], idea.channel):
            return

        success = trello.move_card(idea, 'Finish')
        if not success:
            return

    update_tag('Finish', idea.path)

go()

