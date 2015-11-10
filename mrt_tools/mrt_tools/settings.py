#!/usr/bin/python
import ConfigParser
import os

CONFIG_FILE = os.path.expanduser("~/.mrtgitlab/mrt.cfg")

# Default settings
settings = {
    'Token': {
        'TOKEN_PATH': os.path.expanduser("~/.mrtgitlab/.token"),
        'SAVE_TOKEN': True
    },
    'SSH': {
        'USE_SSH': False,
        'SSH_PATH': os.path.expanduser("~/.ssh"),
        'SSH_KEY_NAME': "mrtgitlab"
    },
    'Cache': {
        'CACHE_FILE': os.path.expanduser("~/.mrtgitlab/repo_cache"),
        'CACHE_LOCK_FILE': os.path.expanduser("~/.mrtgitlab/.repo_cache_lock"),
        'CACHE_DECAY_TIME': 300,  # in seconds
        'CACHE_LOCK_DECAY_TIME': 30  # in seconds
    },
    'Gitlab': {
        'HOST_URL': "https://gitlab.mrt.uni-karlsruhe.de",
        'GIT_CACHE_TIMEOUT': 900,  # in seconds
        'USE_GIT_CREDENTIAL_CACHE': True
    },
    'Snapshot': {
        'FILE_ENDING': ".snapshot",
        'SNAPSHOT_VERSION': "0.1.0",
        'VERSION_FILE': "snapshot.version"
    }
}

config = ConfigParser.SafeConfigParser()

# Read in config file
config.read(CONFIG_FILE)

# Test for sections
for section, section_dict in settings.iteritems():
    # Test for section
    if not config.has_section(section):
        config.add_section(section)
    # Go through keys
    for key, value in section_dict.iteritems():
        if config.has_option(section, key):
            # Update our default settings dict with loaded data
            if isinstance(value, bool):
                settings[section][key] = config.getboolean(section, key)
            elif isinstance(value, int):
                settings[section][key] = config.getint(section, key)
            else:
                settings[section][key] = config.get(section, key)
        else:
            # click.echo("Key '{}' in section '{}' not found. Adding it to config file.".format(key, section))
            config.set(section, key, str(value))

# Writing our configuration file
if not os.path.exists(os.path.dirname(CONFIG_FILE)):
    os.makedirs(os.path.dirname(CONFIG_FILE))
with open(CONFIG_FILE, 'wb') as configfile:
    config.write(configfile)

TOKEN_PATH = settings['Token']['TOKEN_PATH']
SAVE_TOKEN = settings['Token']['SAVE_TOKEN']
USE_SSH = settings['SSH']['USE_SSH']
SSH_PATH = settings['SSH']['SSH_PATH']
SSH_KEY_NAME = settings['SSH']['SSH_KEY_NAME']
CACHE_FILE = settings['Cache']['CACHE_FILE']
CACHE_LOCK_FILE = settings['Cache']['CACHE_LOCK_FILE']
CACHE_DECAY_TIME = settings['Cache']['CACHE_DECAY_TIME']
CACHE_LOCK_DECAY_TIME = settings['Cache']['CACHE_LOCK_DECAY_TIME']
HOST_URL = settings['Gitlab']['HOST_URL']
GIT_CACHE_TIMEOUT = settings['Gitlab']['GIT_CACHE_TIMEOUT']
USE_GIT_CREDENTIAL_CACHE = settings['Gitlab']['USE_GIT_CREDENTIAL_CACHE']
FILE_ENDING = settings['Snapshot']['FILE_ENDING']
SNAPSHOT_VERSION = settings['Snapshot']['SNAPSHOT_VERSION']
VERSION_FILE = settings['Snapshot']['VERSION_FILE']
