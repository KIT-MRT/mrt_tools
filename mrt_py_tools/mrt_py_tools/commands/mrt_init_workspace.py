#!/bin/python
from mrt_py_tools.mrt_base_tools import get_ws_root_folder
import distutils.util
import subprocess
import click
import sys
import os


def init_workspace():
    """
    Initialise a catkin workspace by creating the required directory tree, rosinstall file and running catkin build.
    """
    init_repo = True

    workspace_folder = get_ws_root_folder(os.getcwd())
    print workspace_folder
    if not (workspace_folder == "/" or  workspace_folder == ""):
        click.secho("Already inside a catkin workspace. Can't create new.", fg="red")
        sys.exit(1)

    # Test whether directory is empty
    if os.listdir("."):
        choice_str = raw_input("The repository folder is not empty. Would you like to continue? [y/N] ")
        if choice_str == "":
            choice_str = "n"
        init_repo = distutils.util.strtobool(choice_str)

    if init_repo:
        os.mkdir("src")
        subprocess.call("catkin init", shell=True)
        os.chdir("src")
        subprocess.call("wstool init", shell=True)
        subprocess.call("catkin build", shell=True)

@click.command()
def main():
    """ Initialize a catkin workspace. """
    init_workspace()