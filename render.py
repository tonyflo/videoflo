# Render a batch of videos with the 'Render' tag

import os
from flo.idea import Idea
from flo.planka import Planka
from flo.davinci import Davinci
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.mactag import update_tag
from datetime import datetime

# loop over videos ready to be rendered
def loop(channel, planka, args, renderable):

    davinci = Davinci()
    if davinci.resolve is None:
        return
    davinci.open_deliver_page()

    total = len(renderable)
    print('Rendering {} videos for {}'.format(total, channel.name))
    counter = 0
    finished = 0
    start_time = datetime.now()
    for path in renderable:
        counter = counter + 1
        project_name = os.path.basename(path)
        idea = Idea()
        idea.from_project(project_name, channel)
        if not idea.exists():
            print('Directory for {} not found'.format(project_name))
            return

        davinci.load_project(idea)
        print('Rendering {}/{} ({})'.format(counter, total, idea.name))
        try:
            stats = davinci.render_video()
        except (KeyboardInterrupt, SystemError, ValueError):
            print('\nTerminating renders')
            break
        success = stats['success']
        if success and not args.preview:
            idea.save_render_stats(stats)
            update_tag('Upload', idea.path)
            if not args.offline:
                success = planka.move_card(idea, 'Upload')
                planka.set_render_stats(idea, stats)
        finished = finished + 1 if success else finished

    duration = datetime.now() - start_time
    print('Rendered {}/{} videos in {}'.format(finished, total, duration))

def _get_render_list(channel, planka, args):
    renderable = []
    if args.offline:
        renderable = channel.get_list('Render')
    else:
        if not planka.lists_exist(['Render', 'Upload'], channel):
            return None
        renderable = [channel.find_path_for_id(item['id']) for item in planka.get_list('Render', channel)]

    return renderable

def go():
    flo = VideoFlo()
    args = flo.get_render_arguments()
    channel = Channel(flo.config, args.channel)

    planka = Planka()
    renderable = _get_render_list(channel, planka, args)
    if renderable is None or len(renderable) == 0:
        print('Nothing to render')
        return

    loop(channel, planka, args, renderable)

go()
