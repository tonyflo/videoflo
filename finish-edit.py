# Export a DaVinci Project and update the video directory tag accordingly

import os
import mac_tag # TODO not cross platform
from videoflo import VideoFlo


# export project file to project folder
def export_project(project_manager, project_path, project_name):
    drp = '{}.drp'.format(project_name)
    project_file = os.path.join(project_path, drp)
    status = project_manager.ExportProject(project_name, project_file)
    if status == False:
        print('Failed to export {} file to {}'.format(drp, project_path))

def update_tag(project_path):
    mac_tag.remove(['*'], [project_path])
    mac_tag.add(['Render'], [project_path])

def go():
    flo = VideoFlo()
    resolve = flo.get_resolve()
    project_manager = flo.get_project_manager(resolve)
    project = project_manager.GetCurrentProject()
    if project is None:
        print('Could not get current DaVinci project')
        return

    project_name = project.GetName()
    channel = flo.get_channel(project_name)
    if channel is None:
        print('Could not find channel for this project')
        return
    project_path = flo.get_project_path(project_name, channel)

    export_project(project_manager, project_path, project_name)
    update_tag(project_path)

go()
