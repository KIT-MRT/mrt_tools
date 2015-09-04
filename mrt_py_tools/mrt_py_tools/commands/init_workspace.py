#!/bin/python
from mrt_py_tools import mrt_base_tools
import os
import distutils.util
import subprocess
from mrt_py_tools.commands import catkin
import click


@click.command()
def main():
    """ This script initializes a catkin workspace in the current folder. """
    init_repo = True

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
        catkin.main()
