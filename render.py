# Render a batch of videos with the 'Render' tag

import time
import mac_tag
from pathlib import Path
from videoflo import VideoFlo


# delete all render jobs
def delete_all_render_jobs(project):
    status = project.DeleteAllRenderJobs()
    if status == False:
        print('Failed to delete render job for {}'.format(project_name))

# set render settings
def set_render_settings(project, project_name, project_path):
    render_settings = {
        "TargetDir": str(project_path),
        "CustomName": project_name,
    }
    status = project.SetRenderSettings(render_settings)
    return status

# loop over videos ready to be rendered and render them
def render_vids(tag, channel, project_manager, flo):
    channel_path = Path(flo.dir, channel['path'])
    videos = mac_tag.find([tag], [channel_path])
    num_videos = len(videos)

    print('Rendering {} videos for {}'.format(num_videos, channel['name']))
    success = 0
    for vid in videos:
        project_path = Path(vid)
        project_name = project_path.name

        project = project_manager.LoadProject(project_name)
        if project is None:
            print('Could not load DaVinci project named {}'.format(project_name))
            continue

        status = set_render_settings(project, project_name, project_path)
        if status == False:
            print('Failed to set render settings for {}'.format(project_name))
            continue

        delete_all_render_jobs(project)

        status = project.AddRenderJob()
        if status == False:
            print('Failed to add render job for {}'.format(project_name))
            continue

        status = project.StartRendering(isInteractiveMode=True)
        if status == False:
            print('Failed to start render for {}'.format(project_name))
            delete_all_render_jobs(project)
            continue

        jobid = project.GetRenderJobs()[1]['JobId']
        print('Rendering {}'.format(project_name))
        while(project.IsRenderingInProgress()):
            time.sleep(10)
            render_status = project.GetRenderJobStatus(jobid)
            percent = render_status['CompletionPercentage']
            print('...{}% complete'.format(percent))

        render_status = project.GetRenderJobStatus(jobid)
        job_status = render_status['JobStatus']
        if job_status != 'Complete':
            print('Failed to render {}'.format(project_name))
            delete_all_render_jobs(project)
            continue

        delete_all_render_jobs(project)

        # update tag from Render to Upload
        mac_tag.remove(['*'], [project_path])
        mac_tag.add(['Upload'], [project_path])

        success = success + 1

    if num_videos == 0:
        print('Nothing to render')
    else:
        print('Rendered {}/{} videos'.format(success, num_videos))

def go():
    tag = 'Render'
    flo = VideoFlo()
    args = flo.get_channel_arguments()
    channel = flo.config[args.channel]

    resolve = flo.get_resolve()
    if resolve is None:
        print('Is DaVinci Resolve open?')
        return
    resolve.OpenPage('deliver')
    project_manager = flo.get_project_manager(resolve)

    render_vids(tag, channel, project_manager, flo)

go()
