from pathlib import Path
from flo.video import Video
from flo.channel import Channel
from flo.videoflo import VideoFlo
from flo.mactag import get_uploadable, update_tag


# get the thumbnail file
def get_thumbnail(path):
    png_files = list(path.glob('[!.]*.png'))
    num_png = len(png_files)
    if num_png != 1:
        print('FIX: Found {} png files in {}'.format(num_png, path))
        return None
    return str(png_files[0])

# get the video file
def get_video_file(path):
    mov_files = list(path.glob('[!.]*.mov'))
    num_mov = len(mov_files)
    if num_mov != 1:
        print('FIX: Found {} mov files in {}'.format(num_mov, path))
        return None
    video_file = Path(mov_files[0]).name
    return video_file

# loop over directories tagged as ready for upload and check for required files
def get_upload_list(channel):
    print('Checking videos for {}'.format(channel.name))
    uploadable = get_uploadable(channel.path)
    upload_list = []

    count = 0
    warn = 0
    for upload in uploadable:
        path = Path(upload)
        print('Checking {}'.format(path))
        count = count + 1

        # video thumbnail
        thumbnail = get_thumbnail(path)
        warn = warn + 1 if thumbnail is None else warn

        # video file
        video_file = get_video_file(path)
        warn = warn + 1 if video_file is None else warn

        # video metadata
        video = Video(path, video_file, channel, thumbnail)
        warn = warn + 1 if not video.check_title() else warn
        warn = warn + 1 if not video.check_description() else warn
        warn = warn + 1 if not video.check_tags() else warn

        upload_list.append(video)

    if warn == 0 and count > 0:
        return upload_list
    elif count == 0:
        print('No videos ready for upload')
    else:
        print('{} problem(s) found'.format(warn))
    return []

# prepare uploads
def do_uploads(upload_list):
    for video in upload_list:
        print('Starting upload for {}'.format(video.file))
        video_id = video.upload()
        if video_id is not None:
            update_tag('Backup', video.path)
            # TODO: do something with video_id

def go():
    flo = VideoFlo()
    args = flo.get_channel_arguments()
    channel = Channel(flo.config, args.channel)

    upload_list = get_upload_list(channel)
    if len(upload_list) > 0:
        do_uploads(upload_list)

go()
