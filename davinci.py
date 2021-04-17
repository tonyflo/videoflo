import os
import argparse
from videoflo import VideoFlo

# read command line arguments
def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='Name of video project')
    args = parser.parse_args()
    return args

# create a DaVinci Resolve project
def create_project(resolve, project_name, flo):
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
        if not flo.config.has_option('video', setting):
            continue
        name = 'timeline{}'.format(setting)
        value = int(flo.config['video'][setting])
        project.SetSetting(name, value);
    return project

# return project directory
def get_project_path(project_name, root_dir, channel_dirs):
    # search all channel directories so we don't have to on command line
    for channel_dir in channel_dirs:
        project_path = os.path.join(root_dir, channel_dir, project_name)
        if os.path.exists(project_path):
            return project_path
    return None

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
def set_render_settings(project, project_path, project_name):
    render_settings = {
        "TargetDir": project_path,
        "CustomName": project_name,
    }
    project.SetRenderSettings(render_settings)

# open the Edit page in DaVinci Resolve
def setup(resolve):
    resolve.OpenPage('edit')

def go():
    flo = VideoFlo()
    args = get_arguments()

    project_name = args.name
    channel_dirs = flo.get_channel_dirs()
    project_path = get_project_path(project_name, flo.dir, channel_dirs)
    if project_path is None:
        print('Could not find {} at {}'.format(project_name, flo.dir))
        return

    resolve = flo.get_resolve()
    project = create_project(resolve, project_name, flo)
    if project is None:
        return

    set_render_settings(project, project_path, project_name)
    import_tro(project)
    import_files(resolve, project_path)
    setup(resolve)

go()
