import os
from pathlib import Path
from flo.idea import Idea
from flo.video import Video
from flo.trello import Trello
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.mactag import update_tag
from datetime import datetime


# get the thumbnail file
def get_thumbnail(path):
    png_files = list(path.glob('[!.]*.png'))
    num_png = len(png_files)
    if num_png != 1:
        print('FIX: Found {} png files'.format(num_png, path))
        return None
    return str(png_files[0])

# get the video file
def get_video_file(path):
    mov_files = list(path.glob('[!.]*.mov'))
    num_mov = len(mov_files)
    if num_mov != 1:
        print('FIX: Found {} mov files'.format(num_mov, path))
        return None
    video_file = Path(mov_files[0]).name
    return video_file

# loop over directories tagged as ready for upload and check for required files
def get_upload_dict(channel, trello):
    print('Checking videos for {}'.format(channel.name))
    uploadable = trello.get_list('Upload', channel)
    upload_dict = {}

    total_upload_size = 0
    count = 0
    warn = 0
    for item in uploadable:
        metadata = {
            'title': item['name'],
            'description': item['desc'],
            'scheduled': item['due'],
            'tags': trello.get_checklist(item['idChecklists'], 'tags'),
            'hashtags': trello.get_checklist(item['idChecklists'], 'hashtags'),
        }

        card_id = item['id']
        path = trello.find_path_for_id(card_id, channel)
        if path is None:
            print('Could not find local path for {}'.format(name))
            continue

        path = Path(path)
        project_name = os.path.basename(path)

        idea = Idea()
        idea.from_project(project_name, channel)
        if not idea.exists():
            print('Directory for {} not found'.format(path))
            return

        print('Checking {}'.format(path))
        count = count + 1

        # video thumbnail
        thumbnail = get_thumbnail(path)
        warn = warn + 1 if thumbnail is None else warn

        # video file
        video_file = get_video_file(path)
        if video_file is None:
            warn = warn + 1
            continue

        video = Video(path, video_file, channel, metadata, thumbnail, idea)
        warn = warn + 1 if not video.check_title() else warn
        warn = warn + 1 if not video.check_description() else warn
        warn = warn + 1 if not video.check_date() else warn
        warn = warn + 1 if not video.check_tags() else warn
        warn = warn + 1 if not video.check_hashtags() else warn
        video.format_description()

        total_upload_size += video.video_size

        upload_dict[card_id] = video


    total_upload_gb = round(total_upload_size / (1024 * 1024 * 1024), 3)
    print('Total size of upload: {} GB'.format(total_upload_gb))

    if warn == 0 and count > 0:
        return upload_dict
    elif count == 0:
        print('No videos ready for upload')
    else:
        print('{} problem(s) found'.format(warn))

    return {}

# prepare uploads
def do_uploads(upload_dict, trello):
    upload_count = 0
    upload_total = len(upload_dict)
    start_time = datetime.now()
    for card_id, video in upload_dict.items():
        print('Starting upload for {}'.format(video.file))
        video_id = video.upload()
        if video_id is not None:
            upload_count += 1
            update_tag('Backup', video.path)
            trello.move_card(video.idea, 'Scheduled')
            trello.attach_links_to_card(card_id, video_id)
    duration = datetime.now() - start_time
    print('Uploaded {}/{} videos in {}'.format(upload_count, upload_total, duration))

def go():
    flo = VideoFlo()
    args = flo.get_upload_arguments()
    channel = Channel(flo.config, args.channel)
    dry_run = args.dry_run

    trello = Trello()
    if not trello.lists_exist(['Upload', 'Scheduled'], channel):
        return

    upload_dict = get_upload_dict(channel, trello)
    if not dry_run and len(upload_dict) > 0:
        do_uploads(upload_dict, trello)

go()
