from mrt_tools.settings import user_settings, write_settings
from mrt_tools.utilities import get_user_choice
import keyring
import getpass
import click

available_storage_options = ['gnome_keyring']
keyring.set_keyring(keyring.backends.Gnome.Keyring())
SERVICE_NAME = "mrtgitlab"


def get_credentials(quiet=False):
    username = get_username(quiet)
    password = get_password(username, quiet)
    return username, password


def get_username(quiet=False):
    if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] == 'gnome_keyring':
        username = keyring.get_password(SERVICE_NAME, "username")
    else:
        username = None

    if username is None and not quiet:
        username = getpass.getuser()
        username = click.prompt("Please enter Gitlab username", default=username)
        store_credentials("username", username)

    return username


def get_password(username, quiet=False):
    if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] == 'gnome_keyring':
        password = keyring.get_password(SERVICE_NAME, "password")
    else:
        password = None

    if password is None and not quiet:
        password = click.prompt("Please enter Gitlab password for user {}".format(username), hide_input=True)
        store_credentials("password", password)

    return password


def get_token():
    if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] == 'gnome_keyring':
        token = keyring.get_password(SERVICE_NAME, "token")
    else:
        token = ""

    return token


def store_credentials(key, value):
    # Smooth transition to new version:
    if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] not in available_storage_options:
        click.echo("")
        click.secho("For convenience and improved security, personal data like gitlab-password and gitlab-token can "
                    "now be stored in the Gnome keyring.", fg='yellow')
        click.echo("\t- Personal data can be deleted in the subcommand 'mrt maintenance credentials'. ")
        click.echo("\t- Settings can be changed with 'mrt maintenance settings'")
        click.echo("")
        _, user_choice = get_user_choice(available_storage_options, 'DONT_SAVE',
                                         "Where do you want to save your credentials?")
        click.echo("")
        user_settings['Gitlab']['STORE_CREDENTIALS_IN'] = user_choice
        write_settings(user_settings)

    if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] == 'gnome_keyring':
        click.echo("Storing {} in keyring.".format(key))
        keyring.set_password(SERVICE_NAME, key, value)


def delete_credential(key):
    if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] == 'gnome_keyring':
        keyring.delete_password(SERVICE_NAME, key)
        click.echo("Removed {} from keyring".format(key))
