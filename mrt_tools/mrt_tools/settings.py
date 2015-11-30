#!/usr/bin/python
import ConfigParser
import os

CONFIG_FILE = os.path.expanduser("~/.mrtgitlab/mrt.cfg")

# Default settings
default_settings = {
    'SSH': {
        'USE_SSH': False,
        'SSH_PATH': os.path.expanduser("~/.ssh"),
        'SSH_KEY_NAME': "mrtgitlab"
    },
    'Cache': {
        'CACHE_FILE': os.path.expanduser("~/.mrtgitlab/repo_cache"),
        'CACHE_LOCK_FILE': os.path.expanduser("~/.mrtgitlab/.repo_cache_lock"),
        'CACHE_LOCK_DECAY_TIME': 30  # in seconds
    },
    'Gitlab': {
        'HOST_URL': "https://gitlab.mrt.uni-karlsruhe.de",
        'GIT_CACHE_TIMEOUT': 900,  # in seconds
        'USE_GIT_CREDENTIAL_CACHE': True,
        'STORE_CREDENTIALS_IN': ""
    },
    'Snapshot': {
        'FILE_ENDING': ".snapshot",
        'SNAPSHOT_VERSION': "0.1.0",
        'VERSION_FILE': "snapshot.version"
    },
    'Other': {
        'BASE_YAML_FILE': "/mrtsoftware/pkg/share/ros/base.yaml",
        'BASE_YAML_HASH_FILE': os.path.expanduser("~/.mrtgitlab/base_yaml_hash"),
    }
}


def read_settings(settings, config_file=CONFIG_FILE):
    # Read in config file
    config = ConfigParser.SafeConfigParser()
    config.read(config_file)

    # Test for sections
    for section, section_dict in settings.iteritems():
        # Test for section
        if not config.has_section(section):
            # Default values will be taken
            continue
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
                # Default values will be taken
                continue
    return settings


def write_settings(settings, config_file=CONFIG_FILE):
    # Create new config
    config = ConfigParser.SafeConfigParser()

    # Test for sections
    for section, section_dict in settings.iteritems():
        config.add_section(section)

        # Go through keys
        for key, value in section_dict.iteritems():
            config.set(section, key, str(value))

    # Writing our configuration file
    if not os.path.exists(os.path.dirname(config_file)):
        os.makedirs(os.path.dirname(config_file))
    with open(config_file, 'wb') as f:
        config.write(f)

# Read user settings
user_settings = read_settings(default_settings, CONFIG_FILE)
write_settings(user_settings, CONFIG_FILE)
