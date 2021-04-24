# Valid case-sensitive tags are:
# - Script
# - Film
# - Edit
# - Render
# - Upload
# - Backup

import mac_tag
from subprocess import call


# add tag to path
def add_tag(tag, path, do_open=False):
    mac_tag.add([tag], [path])
    if do_open:
        call(["open", path])

# update tag for path after removing all exitings tags
def update_tag(tag, path, do_open=False):
    mac_tag.remove(['*'], [path])
    add_tag(tag, path, do_open)

def get_renderable(path):
    tagged = mac_tag.find(['Render'], [path])
    return tagged

def get_uploadable(path):
    tagged = mac_tag.find(['Upload'], [path])
    return tagged

