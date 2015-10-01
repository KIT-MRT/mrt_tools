#!/bin/python
from mrt_tools.base import Workspace
import click


@click.command()
def main():
    """ Initialize a catkin workspace. """
    Workspace(silent=True).create()

