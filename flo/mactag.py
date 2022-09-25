import os
from flo.const import STAGES, STAGEFILE
from subprocess import call

# determine if we are on MacOS
USING_MAC = False
import platform
if platform.system() == 'Darwin':
    USING_MAC = True
    import mac_tag

# add tag to path
def add_tag(tag, path, do_open=False):
    tag_file = os.path.join(path, STAGEFILE)
    with open(tag_file, 'w') as f:
        f.write(tag)

    if not USING_MAC:
        return

    mac_tag.add(tag, path)
    if do_open:
        open_dir(path)

# open directory at path
# TODO: test on Windows
def open_dir(path):
    call(["open", path])

# update tag for path after removing all exitings tags
def update_tag(tag, path, do_open=False):
    if not USING_MAC:
        return

    mac_tag.remove(['*'], [path])
    add_tag(tag, path, do_open)

# get tags for path
def get_tags(paths):
    return mac_tag.get(paths)
