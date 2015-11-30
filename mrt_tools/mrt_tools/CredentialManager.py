from mrt_tools.settings import user_settings, write_settings
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
    # Smooth transition to new version:
    if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] == "":
        click.secho("For convenience and improved security, personal data like gitlab-password and gitlab-token will "
                    "be stored in the Gnome keyring from now on.", fg='yellow')
        click.echo("\t- Personal data can be deleted in the subcommand 'mrt maintenance credentials'. ")
        click.echo("\t- Settings can be changed with 'mrt maintenance settings'")
        if click.confirm("Do you confirm to saving your data in the keyring?"):
            user_settings['Gitlab']['STORE_CREDENTIALS_IN'] = 'keyring'
        else:
            user_settings['Gitlab']['STORE_CREDENTIALS_IN'] = 'None'
        write_settings(user_settings)

    if user_settings['Gitlab']['STORE_CREDENTIALS_IN'] == 'keyring':
        click.echo("Storing {} in keyring.".format(key))
        keyring.set_password(SERVICE_NAME, key, value)


def delete_credential(key):
    keyring.delete_password(SERVICE_NAME, key)
    click.echo("Removed {} from keyring".format(key))
