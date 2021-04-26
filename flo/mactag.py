# Valid case-sensitive tags are:
# - Script
# - Film
# - Edit
# - Render
# - Upload
# - Backup

from subprocess import call

# determine if we are on MacOS
USING_MAC = False
import platform
if platform.system() == 'Darwin':
    USING_MAC = True
    import mac_tag


# add tag to path
def add_tag(tag, path, do_open=False):
    if not USING_MAC:
        return

    mac_tag.add([tag], [path])
    if do_open:
        call(["open", path])

# update tag for path after removing all exitings tags
def update_tag(tag, path, do_open=False):
    if not USING_MAC:
        return

    mac_tag.remove(['*'], [path])
    add_tag(tag, path, do_open)

