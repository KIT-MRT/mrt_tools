#!/usr/bin/python
from mrt_py_tools import mrt_base_tools
import click


@click.command()
@click.argument("pkg_name", type=click.STRING, required=False)
@click.option('-t','type', type=click.Choice(['lib', 'exec']), help="Type: Choose between library or executable", prompt="Please choose package type [lib|exec]")
@click.option('-r','ros', is_flag=True, help="Make ROS package", prompt="Should this be a ROS package?")
@click.option('-g','git', is_flag=True, help="Create Git repository", prompt="Create a git repository?")

def main(pkg_name, type, ros, git):
    """ Create a new catkin package """
    mrt_base_tools.change_to_workspace_root_folder()
