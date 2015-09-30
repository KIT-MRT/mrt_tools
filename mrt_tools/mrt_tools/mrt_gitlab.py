from mrt_tools.utilities import *
from mrt_tools.base import *
import click


########################################################################################################################
### Gitlab
########################################################################################################################
@click.group()
def main():
    """Gitlab related tools"""
    pass

@main.command()
def create_token():
    """Create new gitlab token"""
    Token(allow_creation=True)


@main.command()
def create_ssh_key():
    """Create new ssh key"""
    SSHkey().create()

########################################################################################################################
### Permissions
########################################################################################################################
@main.group()
def permissions():
    pass

@permissions.command()
def add_user():
    pass

@permissions.command()
def add_group():
    pass


########################################################################################################################
### List
########################################################################################################################
@main.group()
def show():
    pass

@show.command()
def users():
    pass

@show.command()
def repos():
    pass

@show.command()
def groups():
    pass

