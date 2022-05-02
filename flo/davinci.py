import os
import sys
import time
from pathlib import Path
from datetime import datetime


class Davinci():

    def __init__(self):
        self.resolve = self._get_resolve()
        if self.resolve is None:
            print('Is DaVinci Resolve open?')
        self.project = None
        self.project_manager = None
        self.idea = None

    def _get_resolve(self):
        try:
        # PYTHONPATH needs to be set correctly for this import statement to work
            import DaVinciResolveScript as bmd
        except ImportError:
            if sys.platform.startswith("darwin"):
                expectedPath="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
            elif sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
                import os
                expectedPath=os.getenv('PROGRAMDATA') + "\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\"
            elif sys.platform.startswith("linux"):
                expectedPath="/opt/resolve/libs/Fusion/Modules/"

            # check if the default path has it...
            try:
                import imp
                bmd = imp.load_source('DaVinciResolveScript', expectedPath+"DaVinciResolveScript.py")
            except ImportError:
                # No fallbacks ... report error:
                print("Unable to find module DaVinciResolveScript - please ensure that the module DaVinciResolveScript is discoverable by python")
                print("For a default DaVinci Resolve installation, the module is expected to be located in: "+expectedPath)
                sys.exit()

        return bmd.scriptapp("Resolve")

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
    def open_project(self, idea):
        # create the project
        self.idea = idea
        name = self.idea.name
        is_new = True

        # first try to create project
        project = self.project_manager.CreateProject(name)
        if not project:
            # then try to load the project
            project = self.project_manager.LoadProject(name)
            if not project:
                print('Unable to create or load project: {}'.format(name))
                return None
            is_new = False
        self.project = project

        if is_new:
            # set project settings
            for setting, value in self.idea.channel.settings.items():
                name = 'timeline{}'.format(setting)
                self.project.SetSetting(name, value)

        return is_new

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

        if timeline_path is None:
            return # silently return

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
        stats = {'success': False}
        start_time = datetime.now()

        if self.project is None:
            print('Could not load DaVinci project {}'.format(self.idea.name))
            return stats

        status = self._set_render_settings()
        if status == False:
            print('Failed to set render settings for {}'.format(self.idea.name))
            return stats

        self._delete_all_render_jobs()

        status = self.project.AddRenderJob()
        if status == False:
            print('Failed to add render job for {}'.format(self.idea.name))
            return stats

        status = self.project.StartRendering(isInteractiveMode=True)
        if status == False:
            print('Failed to start render for {}'.format(self.idea.name))
            self._delete_all_render_jobs()
            return stats

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
            return stats

        difference = datetime.now() - start_time
        print('Render time was {}'.format(difference))

        stats['RenderTime'] = round(difference.total_seconds(), 2)
        stats = self._set_stats(stats)

        self._delete_all_render_jobs()

        stats['success'] = True
        return stats

    # statistics associated with the successful render job
    def _set_stats(self, stats):
        project = Path(self.idea.path)
        project_size = sum(f.stat().st_size for f in project.glob('**/*') if f.is_file())
        stats['ProjectSize'] = round(project_size/1000/1000/1000, 2)

        video = os.path.join(self.idea.path, self.idea.name + '.mov')
        size = os.path.getsize(video)
        stats['Size'] = round(size/1000/1000/1000, 2)

        timeline = self.project.GetTimelineByIndex(1)
        frames = timeline.GetEndFrame() - timeline.GetStartFrame()
        seconds = frames / 24 # TODO: don't hardcode
        stats['Length'] = round(seconds, 2)

        return stats
