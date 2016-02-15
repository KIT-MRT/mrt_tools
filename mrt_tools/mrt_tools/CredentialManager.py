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
    def get_credentials(self, quiet=False):
        username = self.get_username(quiet)
        password = self.get_password(username, quiet)
        return username, password

    def get_username(self, quiet=False):
        username = getpass.getuser()
        username = click.prompt("Please enter Gitlab username", default=username)
        return username

    def get_password(self, username, quiet=False):
        password = click.prompt("Please enter Gitlab password for user {}".format(username), hide_input=True)
        return password

    def get_token(self):
        return ""

    def store(self, key, value):
        pass

    def delete(self, key):
        pass


class GnomeCredentialManager(BaseCredentialManager):
    keyring.set_keyring(keyring.backends.Gnome.Keyring())
    SERVICE_NAME = "mrtgitlab"

    def get_username(self, quiet=False):
        username = keyring.get_password(self.SERVICE_NAME, "username")

        if username is None and not quiet:
            username = super(GnomeCredentialManager, self).get_username()
            self.store("username", username)

        return username

    def get_password(self, username, quiet=False):
        password = keyring.get_password(self.SERVICE_NAME, "password")

        if password is None and not quiet:
            password = super(GnomeCredentialManager, self).get_password(username)
            self.store("password", password)

        return password

    def get_token(self):
        token = keyring.get_password(self.SERVICE_NAME, "token")
        return token

    def store(self, key, value):
        click.echo("Storing {} in keyring.".format(key))
        keyring.set_password(self.SERVICE_NAME, key, value)

    def delete(self, key):
        try:
            keyring.delete_password(self.SERVICE_NAME, key)
            click.echo("Removed {} from keyring".format(key))
        except keyring.errors.PasswordDeleteError:
            pass


class FileCredentialManager(BaseCredentialManager):
    TOKEN_FILE = os.path.join(CONFIG_DIR, ".token")

    def get_username(self, quiet=False):
        username = None
        if not quiet:
            username = super(FileCredentialManager, self).get_username()

        return username

    def get_password(self, username, quiet=False):
        password = None

        if not quiet:
            password = super(FileCredentialManager, self).get_password(username)

        return password

    def get_token(self):
        try:
            token = open(self.TOKEN_FILE, 'r').read()
        except (IOError, OSError):
            token = ""

        return token

    def store(self, key, value):
        """Write to file"""
        if key == "token":
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
            with open(self.TOKEN_FILE, 'w') as f:
                f.write(value)

    def delete(self, key):
        if key == "token":
            try:
                os.remove(self.TOKEN_FILE)
                click.echo("Removed token file")
            except OSError:
                pass


class DummyCredentialManager(BaseCredentialManager):
    def get_username(self, quiet=False):
        return None

    def get_password(self, username, quiet=False):
        return None


# Using ordered dict, so that 'get_user_choice' is displayed correctly.
CredentialManagers = OrderedDict()
CredentialManagers['Use_gnome_keyring'] = GnomeCredentialManager
CredentialManagers['Save_only_token_in_file'] = FileCredentialManager
CredentialManagers['DONT_SAVE_ANYTHING'] = BaseCredentialManager

# Smooth transition to new version:
if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] not in CredentialManagers.keys():
    if not sys.stdout.isatty():
        # You're NOT running in a real terminal, create DummyCredentialManager to avoid being prompted
        user_settings['Gitlab']['STORE_CREDENTIALS_IN'] = "Dummy_Manager"
        CredentialManagers['Dummy_Manager'] = DummyCredentialManager
    else:
        click.echo("")
        click.secho(
            "For convenience and improved security, personal data like gitlab-password and gitlab-token can "
            "now be stored in the Gnome keyring.", fg='yellow')
        click.echo("\t- Personal data can be deleted within the subcommand 'mrt maintenance credentials'. ")
        click.echo("\t- Settings can be changed with 'mrt maintenance settings'")
        click.echo("")
        options = ['Use_gnome_keyring', 'Save_only_token_in_file', 'DONT_SAVE_ANYTHING']
        _, user_choice = get_user_choice(CredentialManagers.keys(), default=1, prompt="Where do you want to save your "
                                                                                      "credentials?")
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

