# Check that a thumbnail and DaVinci Resolve project file exists for each
# video project directory that's tagged as 'Upload'

import mac_tag  # TODO: not cross platform
from pathlib import Path
from videoflo import VideoFlo


# count png files under this directory to ensure a thumbnail has been made
def count_pngs(child):
    png_files = list(child.glob('*.png'))
    num_png = len([i for i in png_files if not str(i).startswith('.')])
    return num_png

# count DaVainci Resolve Project files in this directory
def count_drps(child):
    drp_files = list(child.glob('*.drp'))
    num_drp = len(drp_files)
    return num_drp

# loop over directories tagged as ready for upload and check for required files
def check_vids(tag, channel_path):
    count = 0
    warn = 0
    for up in mac_tag.find([tag], [channel_path]):
        child = Path(up)
        print('Checking {}'.format(child))
        count = count + 1

        num_drp = count_drps(child)
        if num_drp != 1:
            warn += 1
            print('  WARNING: Found {} drp files in {}'.format(num_drp, child))

        num_png = count_pngs(child)
        if num_png < 1:
            warn += 1
            print('  WARNING: Found {} png files in {}'.format(num_png, child))

    if warn == 0 and count > 0:
        print('All "{}" videos have a .drp and .png files'.format(tag))
    if count == 0:
        print('Nothing to check')
    else:
        print('{} problem(s) found in {} projects'.format(warn, count))

def go():
    tag = 'Upload'
    flo = VideoFlo()
    args = flo.get_channel_arguments()
    channel = flo.config[args.channel]
    channel_path = Path(flo.dir, channel['path'])
    print('Checking videos for {}'.format(channel['name']))
    check_vids(tag, channel_path)

go()
