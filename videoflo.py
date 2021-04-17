import os
import sys
import configparser

def init():
    # read settings file
    config = configparser.ConfigParser()
    config.read('settings.ini')

    # pull out settings
    api = config['main']['api']
    examples = os.path.join(api, 'Examples')
    modules = os.path.join(api, 'Modules')

    # append to system path
    sys.path.append(examples)
    sys.path.append(modules)

    return config

