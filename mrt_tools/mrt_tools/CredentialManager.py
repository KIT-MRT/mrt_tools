from mrt_tools.settings import STORE_CREDENTIALS_IN_KEYRING
import keyring
import click
import getpass

keyring.set_keyring(keyring.backends.Gnome.Keyring())
SERVICE_NAME = "mrtgitlab"


def get_credentials():
    username = get_username()
    password = get_password(username)
    return username, password


def get_username():
    username = keyring.get_password(SERVICE_NAME, "username")
    if username is None:
        click.echo("Username not stored.")
        username = getpass.getuser()
        username = click.prompt("Please enter Gitlab username", default=username)
        store_credentials("username", username)
    return username


def get_password(username):
    password = keyring.get_password(SERVICE_NAME, "password")
    if password is None:
        click.echo("Password not stored.")
        password = click.prompt("Please enter Gitlab password for user {}".format(username), hide_input=True)
        store_credentials("password", password)
    return password


def store_credentials(key, value):
    if STORE_CREDENTIALS_IN_KEYRING:
        keyring.set_password(SERVICE_NAME, key, value)
