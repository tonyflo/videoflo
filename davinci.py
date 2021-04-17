import os
import sys
from videoflo import init
config = init()
from python_get_resolve import GetResolve

# TODO: make these configurable
project_name = sys.argv[1] # get project name from command line argument

# create a DaVinci Resolve project
def create_project(resolve):
    try:
        project_manager = resolve.GetProjectManager()
    except AttributeError:
        print('DaVinci Resolve probably not open')
        return None

    # create the project
    project = project_manager.CreateProject(project_name)
    if not project:
        print('Unable to create a project. Does it already exist?')
        return None

    # set project settings
    for setting in ['FrameRate', 'ResolutionWidth', 'ResolutionHeight']:
        if not config.has_option('video', setting):
            continue
        name = 'timeline{}'.format(setting)
        value = int(config['video'][setting])
        project.SetSetting(name, value);
    return project

# return project directory
def get_project_dir():
    root_dir = config['main']['root_dir']
    project_path = os.path.join(root_dir, project_name)
    if not os.path.exists(project_path):
        print('Folder {} does not exist'.format(project_path))
        sys.exit()
    return project_path

# import files (video, audio, etc.) from project path
def import_files(resolve, project_path):
    storage = resolve.GetMediaStorage()
    storage.AddItemListToMediaPool(project_path)

# import intro/outro timeline
def import_tro(project):
    mediapool = project.GetMediaPool()
    mediapool.ImportTimelineFromFile('/Users/tonyflorida/Movies/thrifty-tony/Timeline1.drt')
    folder = mediapool.GetCurrentFolder()
    clips = folder.GetClipList()
    tro = mediapool.AddSubFolder(folder, 'tro')
    mediapool.MoveClips(clips[1:], tro) # move all but timeline
    mediapool.SetCurrentFolder(folder)

# set render settings
def set_render_settings(project, project_path):
    render_settings = {
        "TargetDir": project_path,
        "CustomName": project_name,
    }
    project.SetRenderSettings(render_settings)

# open the Edit page in DaVinci Resolve
def setup(resolve):
    resolve.OpenPage('edit')

def go():
    project_path = get_project_dir()
    resolve = GetResolve()
    project = create_project(resolve)
    if project is not None:
        set_render_settings(project, project_path)
        import_tro(project)
        import_files(resolve, project_path)
        setup(resolve)

go()
