import os
import shutil
import mac_tag
from glob import glob
from pathlib import Path
from subprocess import call
from videoflo import VideoFlo


def prepare_uploads(tag, channel_path):
    upload_list = []
    for up in mac_tag.find([tag], [channel_path]):
        pattern = os.path.join(up, '*.mov')
        mov = glob(pattern)
        if len(mov) > 1:
            print('Multiple mov files found: {}'.format(mov))
            break
        if len(mov) == 0:
            print('No *.mov found in: {}'.format(up))
            break
        upload_list.append(mov[0])
    else: # this block only executes if we didn't break above
        if len(upload_list) == 0:
            print('No video files ready for upload')
            return
        # create temporary folder for just the mov files
        target_dir = os.path.join(channel_path, '_uploadme_')
        if os.path.exists(target_dir):
            print('The {} directory already exists'.format(target_dir))
            return
        os.mkdir(target_dir)
        for f in upload_list:
            filename = os.path.basename(f)
            print('Copying {}'.format(filename))
            shutil.copy2(f, target_dir)
        call(["open", target_dir])

def go():
    tag = 'Upload'
    flo = VideoFlo()
    args = flo.get_channel_arguments()
    channel = flo.config[args.channel]
    channel_path = Path(flo.dir, channel['path'])
    prepare_uploads(tag, channel_path)


go()
