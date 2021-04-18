# Create a DaVinci Resolve project for a video directory

import os
from videoflo import VideoFlo

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
def get_project_path(project_name, root_dir, channel):
    project_path = os.path.join(root_dir, channel['path'], project_name)
    return project_path

# import files (video, audio, etc.) from project path
def import_files(resolve, project_path):
    storage = resolve.GetMediaStorage()
    storage.AddItemListToMediaPool(project_path)

# import intro/outro timeline
def import_timeline(project, channel):
    mediapool = project.GetMediaPool()
    try:
        timeline_path = channel['timeline']
    except KeyError:
        return # silently return if no timeline found for this channel
    if not os.path.exists(timeline_path):
        print('Timeline at {} does not exist'.format(timeline_path))
        return
    timeline = mediapool.ImportTimelineFromFile(timeline_path)
    if timeline is None:
        name = channel['name']
        print('No timeline found for {} at {}'.format(name, timeline_path))
        return
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
    args = flo.get_arguments()

    project_name = args.name
    channel = flo.get_channel(project_name, args)
    if channel is None:
        print('Could not find channel for project {}'.format(project_name))
        return
    project_path = get_project_path(project_name, flo.dir, channel)
    if project_path is None:
        print('Could not find {} at {}'.format(project_name, flo.dir))
        return

    resolve = flo.get_resolve()
    project = create_project(resolve, project_name, flo)
    if project is None:
        return

    set_render_settings(project, project_path, project_name)
    import_timeline(project, channel)
    import_files(resolve, project_path)
    setup(resolve)

go()
