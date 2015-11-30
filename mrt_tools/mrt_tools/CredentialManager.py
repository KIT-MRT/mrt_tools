from mrt_tools.settings import user_settings, write_settings, CONFIG_DIR
from mrt_tools.utilities import get_user_choice
import keyring
import getpass
import click
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


CredentialManagers = {
    'Use_gnome_keyring': GnomeCredentialManager,
    'Save_only_token_in_file': FileCredentialManager,
    'DONT_SAVE_ANYTHING': BaseCredentialManager,
}

# Smooth transition to new version:
if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] not in CredentialManagers.keys():
    click.echo("")
    click.secho(
        "For convenience and improved security, personal data like gitlab-password and gitlab-token can "
        "now be stored in the Gnome keyring.", fg='yellow')
    click.echo("\t- Personal data can be deleted in the subcommand 'mrt maintenance credentials'. ")
    click.echo("\t- Settings can be changed with 'mrt maintenance settings'")
    click.echo("")
    _, user_choice = get_user_choice(CredentialManagers.keys(), prompt="Where do you want to save your credentials?")
    click.echo("")
    user_settings['Gitlab']['STORE_CREDENTIALS_IN'] = user_choice
    write_settings(user_settings)

credentialManager = CredentialManagers[user_settings['Gitlab']['STORE_CREDENTIALS_IN']]()
