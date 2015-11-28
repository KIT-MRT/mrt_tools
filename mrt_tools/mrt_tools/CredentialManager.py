from mrt_tools.settings import user_settings
import keyring
import click
import getpass

keyring.set_keyring(keyring.backends.Gnome.Keyring())
SERVICE_NAME = "mrtgitlab"


def get_credentials(quiet=False):
    username = get_username(quiet)
    password = get_password(username, quiet)
    return username, password


def get_username(quiet=False):
    username = keyring.get_password(SERVICE_NAME, "username")
    if username is None and not quiet:
        username = getpass.getuser()
        username = click.prompt("Please enter Gitlab username", default=username)
        store_credentials("username", username)
    return username


def get_password(username, quiet=False):
    password = keyring.get_password(SERVICE_NAME, "password")
    if password is None and not quiet:
        password = click.prompt("Please enter Gitlab password for user {}".format(username), hide_input=True)
        store_credentials("password", password)
    return password


def get_token():
    token = keyring.get_password(SERVICE_NAME, "token")
    return token


def store_credentials(key, value):
    if user_settings['Gitlab']['STORE_CREDENTIALS_IN_KEYRING']:
        click.echo("Storing {} in keyring.".format(key))
        keyring.set_password(SERVICE_NAME, key, value)


def delete_credential(key):
    keyring.delete_password(SERVICE_NAME, key)
    click.echo("Removed {} from keyring".format(key))
