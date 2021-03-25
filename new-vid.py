#!/Users/tonyflorida/.pyenv/shims/python
# Create structure for new video project

import os
import sys
import mac_tag
from subprocess import call

root_dir = '/Volumes/vid/'

new_proj = sys.argv[1] # get new of project from command line input

new_dir = os.path.join(root_dir, new_proj)
os.mkdir(new_dir)
mac_tag.add(['Script'], [new_dir])

for txt in ['yt.txt', 'notes.txt']:
    new_file = os.path.join(new_dir, txt)
    open(new_file, 'a').close()
    call(["open", new_dir])

for folder in ['gh5', 'screen']:
    new_folder = os.path.join(new_dir, folder)
    os.mkdir(new_folder)
