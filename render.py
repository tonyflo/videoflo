# Render a batch of videos with the 'Render' tag

import os
from flo.idea import Idea
from flo.trello import Trello
from flo.davinci import Davinci
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.mactag import update_tag
from datetime import datetime

# loop over videos ready to be rendered
def loop(channel, trello, args, renderable):

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
        stats = davinci.render_video()
        success = stats['success']
        if success and not args.preview:
            update_tag('Upload', idea.path)
            if args.offline:
                pass# TODO: save render stats locally
            else:
                success = trello.move_card(idea, 'Upload')
                trello.set_render_stats(idea, stats)
        finished = finished + 1 if success else finished

    duration = datetime.now() - start_time
    print('Rendered {}/{} videos in {}'.format(finished, total, duration))

def _get_render_list(channel, trello, args):
    renderable = []
    if args.offline:
        renderable = channel.get_list('Render')
    else:
        if not trello.lists_exist(['Render', 'Upload'], channel):
            return None
        renderable = trello.get_list('Render', channel)

    return renderable

def go():
    flo = VideoFlo()
    args = flo.get_render_arguments()
    channel = Channel(flo.config, args.channel)

    trello = Trello()
    renderable = _get_render_list(channel, trello, args)
    if renderable is None or len(renderable) == 0:
        print('Nothing to render')
        return

    loop(channel, trello, args, renderable)

go()
