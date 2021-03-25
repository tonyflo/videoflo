#!/Users/tonyflorida/.pyenv/shims/python

import os
import sys

# TODO: these are not cross-platform and this is hacky
RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Examples"
MODULE="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
sys.path.append(RESOLVE_SCRIPT_API)
sys.path.append(MODULE)

from python_get_resolve import GetResolve

# TODO: make these configurable
root_dir = '/Volumes/vid/'
fps = 24
width = 3840
height = 2160
project_name = sys.argv[1] # get project name from command line argument

# create a DaVinci Resolve project
def create_project(resolve):
    try:
        project_manager = resolve.GetProjectManager()
    except AttributeError:
        print('DaVinci Resolve probably not open')

    # create the project
    project = project_manager.CreateProject(project_name)
    if not project:
        print('Unable to create a project. Does it already exist?')
        sys.exit()

    # set project settings
    project.SetSetting("timelineFrameRate", fps)
    project.SetSetting("timelineResolutionWidth", width)
    project.SetSetting("timelineResolutionHeight", height)
    return project

# return project directory
def get_project_dir():
    project_path = os.path.join(root_dir, project_name)
    if not os.path.exists(project_path):
        print('Folder {} does not exist at {}'.format(project_name, root_dir))
        sys.exit()
    return project_path

# import files (video, audio, etc.) from project path
def import_files(resolve, project_path):
    storage = resolve.GetMediaStorage()
    storage.AddItemListToMediaPool(project_path)

# open the Edit page in DaVinci Resolve
def setup(resolve):
    resolve.OpenPage('edit')

def go():
    project_path = get_project_dir()
    resolve = GetResolve()
    project = create_project(resolve)
    import_files(resolve, project_path)
    setup(resolve)

go()
