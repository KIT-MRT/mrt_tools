from mrt_tools.settings import user_settings, write_settings, CONFIG_DIR
from mrt_tools.utilities import get_user_choice
from collections import OrderedDict
import subprocess
import keyring
import getpass
import click
import sys
import os


class BaseCredentialManager(object):
    credentialStorage = {}

    def get_credentials(self, quiet=False):
        username = self.get_username(quiet)
        password = self.get_password(username, quiet)
        return username, password

    def get_username(self, quiet=False):
        username = self.get("username")

        if username is None and not quiet:
            username = getpass.getuser()
            username = click.prompt("Please enter Gitlab username", default=username)
            self.store("username", username)

        return username

    def get_password(self, username, quiet=False):
        password = self.get("password")

        if password is None and not quiet:
            password = click.prompt("Please enter Gitlab password for user {}".format(username), hide_input=True)
            self.store("password", password)

        return password

    def get_token(self):
        return self.get("token")

    def store(self, key, value):
        self.credentialStorage[key] = value

    def get(self, key):
        try:
            return self.credentialStorage[key]
        except KeyError:
            return None

    def delete(self, key):
        try:
            del self.credentialStorage[key]
        except KeyError:
            pass


class DummyCredentialManager(BaseCredentialManager):
    def get_username(self, quiet=False):
        return None

    def get_password(self, username, quiet=False):
        return None

    def store(self, key, value):
        pass


class KeyringCredentialManager(BaseCredentialManager):
    SERVICE_NAME = "mrtgitlab"

    def get(self, key):
        return keyring.get_password(self.SERVICE_NAME, key)

    def store(self, key, value):
        click.secho("Storing {} in keyring.".format(key), fg="green")
        keyring.set_password(self.SERVICE_NAME, key, value)

    def delete(self, key):
        try:
            keyring.delete_password(self.SERVICE_NAME, key)
            click.secho("Removed {} from keyring".format(key), fg="green")
        except keyring.errors.PasswordDeleteError:
            pass


class GnomeCredentialManager(KeyringCredentialManager):
    def __init__(self):
        keyring.set_keyring(keyring.backends.Gnome.Keyring())


class FileCredentialManager(KeyringCredentialManager):
    def __init__(self):
        keyring.set_keyring(keyring.backends.file.PlaintextKeyring())



# Using ordered dict, so that 'get_user_choice' is displayed correctly.
CredentialManagers = OrderedDict()
CredentialManagers['DONT_SAVE_ANYTHING'] = BaseCredentialManager
CredentialManagers['GnomeCredentialManager'] = GnomeCredentialManager
CredentialManagers['FileCredentialManager'] = FileCredentialManager
CredentialManagers['BaseCredentialManager'] = BaseCredentialManager
CredentialManagers['DummyCredentialManager'] = DummyCredentialManager

# Smooth transition to new version:
if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] not in CredentialManagers.keys():
    if not sys.stdout.isatty():
        # You're NOT running in a real terminal, create DummyCredentialManager to avoid being prompted
        user_settings['Gitlab']['STORE_CREDENTIALS_IN'] = "Dummy_Manager"
        CredentialManagers['Dummy_Manager'] = DummyCredentialManager
    else:
        click.echo("")
        click.secho("Please choose a backend for saving your credentials.", fg='yellow')
        click.echo("\t- GnomeKeyring is recommended on your OWN computer only.")
        click.echo("\t- On remote servers, (via SSH) GnomeKeyring will not work!")
        click.echo("\t- You can choose to not save anything.")
        click.echo("\t- Personal data can be deleted within the subcommand 'mrt maintenance credentials'.")
        click.echo("\t- Settings can be changed with 'mrt maintenance settings'")
        click.echo("")
        _, user_choice = get_user_choice(CredentialManagers.keys()[0:3], default=0, prompt="Where do you want to save "
                                                                                           "your credentials?")
        click.echo("")
        user_settings['Gitlab']['STORE_CREDENTIALS_IN'] = user_choice
        write_settings(user_settings)

credentialManager = CredentialManagers[user_settings['Gitlab']['STORE_CREDENTIALS_IN']]()


def set_git_credentials(username, password):
    url = user_settings['Gitlab']['HOST_URL']
    if url.startswith("https://"):
        host = url[8:]
    elif url.startswith("http://"):
        host = url[7:]
    else:
        host = url
    git_process = subprocess.Popen("git credential-cache store", shell=True, stdin=subprocess.PIPE)
    git_process.communicate(
        input="protocol=https\nhost={}\nusername={}\npassword={}".format(host, username, password))
