from builtins import str
from builtins import range
#!/usr/bin/python
from mrt_tools.settings import *
import subprocess
import fnmatch
import click
import os


def get_script_root():
    """
    Get the path of this script.
    :return: path
    """
    return os.path.dirname(os.path.realpath(__file__))


def find_by_pattern(pattern, path):
    """
    Searches for a file within a directory
    :param pattern: Name to search for
    :param path: Search path
    :return: List of paths
    """
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


def get_userinfo():
    """Read in git user infos."""

    # Check whether git is installed
    (__, dpkg_err) = subprocess.Popen("dpkg -s git", shell=True, stdout=subprocess.PIPE).communicate()

    # Read out username and email
    (name, name_err) = subprocess.Popen("git config --get user.name", shell=True,
                                        stdout=subprocess.PIPE).communicate()
    (email, mail_err) = subprocess.Popen("git config --get user.email", shell=True,
                                         stdout=subprocess.PIPE).communicate()

    # Check wether git is configured
    if dpkg_err is not None:
        click.echo("Git not found, installing...")
        subprocess.call("sudo apt-get install git", shell=True)
    if name_err is not None or name == "":
        name = click.prompt("Git user name not configured. Please enter name")
        while not click.confirm("Use '" + name + "'as git user name?"):
            name = click.prompt("Please enter new name:")
        subprocess.call("git config --global user.name '" + name + "'", shell=True)
    if mail_err is not None or email == "":
        email = click.prompt("Git user email not configured. Please enter email")
        while not click.confirm("Use '" + email + "'as git user email?"):
            name = click.prompt("Please enter new email:")
        subprocess.call("git config --global user.email '" + email + "'", shell=True)

    return {'name': name[:-1], 'mail': email[:-1]}


def get_user_choice(items, extra=None, prompt="Please choose a number", default=None):
    # Print choices
    valid_choices = []
    for index, item in enumerate(items):
        valid_choices.append(index)
        click.echo("(" + str(valid_choices[-1]) + ") " + item)
    valid_choices = list(range(0, len(items)))

    # Add default choice
    if extra:
        valid_choices.append(len(items))
        click.echo("(" + str(valid_choices[-1]) + ") " + str(extra))
    while True:
        user_choice = click.prompt(prompt + ' [0-' + str(valid_choices[-1]) + ']', type=int, default=default)
        if user_choice in valid_choices:
            if extra is not None and user_choice is valid_choices[-1]:
                # Return None if default was chosen
                return None
            else:
                return user_choice


def touch(filename, times=None):
    with open(filename, 'a'):
        os.utime(filename, times)


def update_apt_and_ros_packages():
    f_null = open(os.devnull, 'w')
    subprocess.call(["sudo", "apt-get", "update", "-o", "Dir::Etc::sourcelist=", "sources.list.d/mrt.list",
                     "-o", "Dir::Etc::sourceparts=", "-", "-o", "APT::Get::List-Cleanup=", "0"], stdout=f_null,
                    stderr=f_null)
    subprocess.check_call(["sudo", "apt-get", "install", "--only-upgrade", "mrt-cmake-modules", "--yes"], stdout=f_null)
    subprocess.check_call(["rosdep", "update"], stdout=f_null)
