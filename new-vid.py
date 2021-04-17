# Create structure for new video project

import os
import sys
import mac_tag
from subprocess import call
from videoflo import init
config = init()

new_proj = sys.argv[1] # get new of project from command line input
root_dir = config['main']['root_dir']

new_dir = os.path.join(root_dir, new_proj)
try:
    os.mkdir(new_dir)
except FileNotFoundError:
    print('Directory {} does not exist'.format(root_dir))
    sys.exit()
mac_tag.add(['Script'], [new_dir])

for txt in ['yt.txt', 'notes.txt']:
    new_file = os.path.join(new_dir, txt)
    open(new_file, 'a').close()
    call(["open", new_dir])

for folder in ['gh5', 'screen']:
    new_folder = os.path.join(new_dir, folder)
    os.mkdir(new_folder)
