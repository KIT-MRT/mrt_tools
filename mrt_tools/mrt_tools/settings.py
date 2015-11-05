#!/usr/bin/python
import ConfigParser
import click
import sys
import os

CONFIG_FILE = os.path.expanduser("~/.mrtgitlab/mrt.cfg")
config = ConfigParser.ConfigParser()


def create_default_config():
    click.echo("Creating new config file with default values.")

    # Create config file with default settings
    config.add_section('Token')
    config.set('Token', 'TOKEN_PATH', os.path.expanduser("~/.mrtgitlab/.token"))
    config.set('Token', 'SAVE_TOKEN', "True")

    config.add_section('SSH')
    config.set('SSH', 'USE_SSH', "False")
    config.set('SSH', 'SSH_PATH', os.path.expanduser("~/.ssh"))
    config.set('SSH', 'SSH_KEY_NAME', "mrtgitlab")

    config.add_section('Cache')
    config.set('Cache', 'CACHE_FILE', os.path.expanduser("~/.mrtgitlab/repo_cache"))
    config.set('Cache', 'CACHE_LOCK_FILE', os.path.expanduser("~/.mrtgitlab/.repo_cache_lock"))
    config.set('Cache', 'CACHE_DECAY_TIME', "300")  # in seconds
    config.set('Cache', 'CACHE_LOCK_DECAY_TIME', "30")  # in seconds

    config.add_section('Gitlab')
    config.set('Gitlab', 'HOST_URL', "https://gitlab.mrt.uni-karlsruhe.de")
    config.set('Gitlab', 'GIT_CACHE_TIMEOUT', "900")  # in seconds

    config.add_section('Snapshot')
    config.set('Snapshot', 'FILE_ENDING', ".snapshot")
    config.set('Snapshot', 'SNAPSHOT_VERSION', "0.1.0")
    config.set('Snapshot', 'VERSION_FILE', "snapshot.version")

    # Writing our configuration file
    if not os.path.exists(os.path.dirname(CONFIG_FILE)):
        os.makedirs(os.path.dirname(CONFIG_FILE))
    with open(CONFIG_FILE, 'wb') as configfile:
        config.write(configfile)


try:
    if not os.path.exists(CONFIG_FILE):
        create_default_config()

    # Read in config file
    config.read(CONFIG_FILE)

    # Token
    TOKEN_PATH = config.get('Token', 'TOKEN_PATH')
    SAVE_TOKEN = config.getboolean('Token', 'SAVE_TOKEN')

    # SSH Keys
    USE_SSH = config.getboolean('SSH', 'USE_SSH')
    SSH_PATH = config.get('SSH', 'SSH_PATH')
    SSH_KEY_NAME = config.get('SSH', 'SSH_KEY_NAME')
    # Cache
    CACHE_FILE = config.get('Cache', 'CACHE_FILE')
    CACHE_LOCK_FILE = config.get('Cache', 'CACHE_LOCK_FILE')
    CACHE_DECAY_TIME = config.getint('Cache', 'CACHE_DECAY_TIME')
    CACHE_LOCK_DECAY_TIME = config.getint('Cache', 'CACHE_LOCK_DECAY_TIME')

    # Gitlab
    HOST_URL = config.get('Gitlab', 'HOST_URL')
    GIT_CACHE_TIMEOUT = config.getint('Gitlab', 'GIT_CACHE_TIMEOUT')

    # Snapshot
    FILE_ENDING = config.get('Snapshot', 'FILE_ENDING')
    SNAPSHOT_VERSION = config.get('Snapshot', 'SNAPSHOT_VERSION')
    VERSION_FILE = config.get('Snapshot', 'VERSION_FILE')

except ConfigParser.Error:
    if click.confirm("There was an error reading the config. Recreate with default values?"):
        click.echo("Removing config file. Please try again now.")
        os.remove(CONFIG_FILE)
    sys.exit(1)