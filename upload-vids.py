import os
import shutil
import mac_tag
from glob import glob
from pathlib import Path
from subprocess import call
from videoflo import init
config = init()

root_dir = Path(config['main']['root_dir'])
upload = mac_tag.find(['Upload'])

upload_list = []
for up in upload:
    pattern = os.path.join(up, '*.mov')
    mov = glob(pattern)
    if len(mov) > 1:
        print('Multiple mov files found: {}'.format(mov))
        break
    if len(mov) == 0:
        print('No *.mov found in: {}'.format(up))
        break
    upload_list.append(mov[0])
else:
    # create temp folder for mov files
    target_dir = os.path.join(root_dir, 'uploadme')
    os.mkdir(target_dir)
    for f in upload_list:
        filename = os.path.basename(f)
        print('Copying {}'.format(filename))
        shutil.copy2(f, target_dir)

    call(["open", target_dir])


