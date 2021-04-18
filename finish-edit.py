# Export a DaVinci Project and update the video directory tag accordingly

import os
import mac_tag # TODO not cross platform
from videoflo import VideoFlo


def get_project_manager(resolve):
    try:
        project_manager = resolve.GetProjectManager()
        return project_manager
    except AttributeError:
        print('DaVinci Resolve probably not open')
        return None

# set render settings
def set_render_settings(project, project_path):
    render_settings = {
        "TargetDir": project_path,
        "CustomName": project.GetName(),
    }
    project.SetRenderSettings(render_settings)

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
    project_manager = get_project_manager(resolve)
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

    resolve.OpenPage('deliver')
    set_render_settings(project, project_path)
    export_project(project_manager, project_path, project_name)
    update_tag(project_path)

go()
