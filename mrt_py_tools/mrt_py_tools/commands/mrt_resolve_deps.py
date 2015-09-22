#!/usr/bin/python
from mrt_py_tools.base import Workspace
import click


@click.command()
def main():
    """ Resolve all dependencies in this workspace."""
    ws = Workspace()
    ws.resolve_dependencies()
