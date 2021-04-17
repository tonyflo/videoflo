# Create structure for new video project

import mac_tag
from pathlib import Path
from videoflo import init
config = init()

tag = 'Upload'
root_dir = Path(config['main']['root_dir'])
upload = mac_tag.find([tag])

count = 0
warn = 0
for up in upload:
    count = count + 1
    child = Path(up)
    print('Checking {}'.format(child))
    if not root_dir in child.parents:
        warn += 1
        print('  WARNING: Path {} not in {}'.format(child, root_dir))
        continue
    num_drp = len(list(child.glob('*.drp')))
    if num_drp != 1:
        warn += 1
        print('  WARNING: Found {} drp files in {}'.format(num_drp, child))
    num_png = len([i for i in list(child.glob('*.png')) if not str(i).startswith('.')])
    if num_png < 1:
        warn += 1
        print('  WARNING: Found {} png files in {}'.format(num_png, child))

if warn == 0 and count > 0:
    print('All "{}" videos have a .drp and .png files'.format(tag))
if count == 0:
    print('Nothing to check')
else:
    print('{} problem(s) found in {} projects'.format(warn, count))
