import os
import time
from python_get_resolve import GetResolve


class Davinci():

    def __init__(self):
        self.resolve = GetResolve()
        if self.resolve is None:
            print('Is DaVinci Resolve open?')
        self.project = None
        self.project_manager = None
        self.idea = None

    # load project
    def load_project(self, idea):
        self.set_project_manager()
        self.idea = idea
        self.project = self.project_manager.LoadProject(self.idea.name)

    # get the currently open project
    def get_current_project(self):
        self.set_project_manager()
        if self.project_manager is None:
            return

        self.project = self.project_manager.GetCurrentProject()

    # instantiate the DaVinci Resole project manager
    def set_project_manager(self):
        try:
            self.project_manager = self.resolve.GetProjectManager()
        except AttributeError:
            print('DaVinci Resolve probably not open')

    # create a DaVinci Resolve project
    def create_project(self, idea):
        # create the project
        self.idea = idea
        project = self.project_manager.CreateProject(self.idea.name)
        if not project:
            print('Unable to create the project. Does it already exist?')
            return None
        self.project = project

        # set project settings
        for setting, value in self.idea.channel.settings.items():
            name = 'timeline{}'.format(setting)
            self.project.SetSetting(name, value)

    # import files (video, audio, etc.) from project path
    def import_files(self):
        storage = self.resolve.GetMediaStorage()
        storage.AddItemListToMediaPool(self.idea.path)

    # import intro/outro timeline
    def import_timeline(self):
        mediapool = self.project.GetMediaPool()
        try:
            timeline_path = self.idea.channel.timeline
        except KeyError:
            return # silently return if no timeline found for this channel

        if not os.path.exists(timeline_path):
            print('Timeline at {} does not exist'.format(timeline_path))
            return

        timeline = mediapool.ImportTimelineFromFile(timeline_path)
        if timeline is None:
            name = self.idea.channel.name
            print('No timeline found for {} at {}'.format(name, timeline_path))
            return

        folder = mediapool.GetCurrentFolder()
        clips = folder.GetClipList()
        tro = mediapool.AddSubFolder(folder, 'tro')
        mediapool.MoveClips(clips[1:], tro) # move all but timeline
        mediapool.SetCurrentFolder(folder)

    # open the Edit page in DaVinci Resolve
    def workspace_setup(self):
        self.resolve.OpenPage('edit')

    # open the Deliver page in DaVinci Resolve
    def open_deliver_page(self):
        self.resolve.OpenPage('deliver')

    # export project file to video idea folder
    def export_project(self, idea):
        drp = '{}.drp'.format(idea.name)
        project_file = os.path.join(idea.path, drp)
        status = self.project_manager.ExportProject(idea.name, project_file)
        if status == False:
            print('Failed to export {} file to {}'.format(drp, idea.path))

    # delete all render jobs
    def _delete_all_render_jobs(self):
        status = self.project.DeleteAllRenderJobs()
        if status == False:
            print('Failed to delete render jobs for')

    # set render settings
    def _set_render_settings(self):
        render_settings = {
            'TargetDir': str(self.idea.path),
            'CustomName': self.idea.name,
        }
        status = self.project.SetRenderSettings(render_settings)
        return status

    # render video
    def render_video(self):
        if self.project is None:
            print('Could not load DaVinci project {}'.format(self.idea.name))
            return False

        status = self._set_render_settings()
        if status == False:
            print('Failed to set render settings for {}'.format(self.idea.name))
            return False

        self._delete_all_render_jobs()

        status = self.project.AddRenderJob()
        if status == False:
            print('Failed to add render job for {}'.format(self.idea.name))
            return False

        status = self.project.StartRendering(isInteractiveMode=True)
        if status == False:
            print('Failed to start render for {}'.format(self.idea.name))
            self._delete_all_render_jobs()
            return False

        jobid = self.project.GetRenderJobs()[1]['JobId']
        while(self.project.IsRenderingInProgress()):
            time.sleep(10)
            render_status = self.project.GetRenderJobStatus(jobid)
            percent = render_status['CompletionPercentage']
            print('...{}% complete'.format(percent))

        render_status = self.project.GetRenderJobStatus(jobid)
        job_status = render_status['JobStatus']
        if job_status != 'Complete':
            print('Failed to render {}'.format(self.idea.name))
            self._delete_all_render_jobs()
            return False

        self._delete_all_render_jobs()

        return True
