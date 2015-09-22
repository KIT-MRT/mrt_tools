#!/bin/python
from mrt_py_tools.base import Workspace
import click


@click.command()
def main():
    """ Initialize a catkin workspace. """
    Workspace(init=True)
