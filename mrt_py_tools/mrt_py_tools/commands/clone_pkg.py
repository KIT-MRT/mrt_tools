__author__ = 'bandera'
from mrt_py_tools import mrt_base_tools
from mrt_py_tools import mrt_gitlab_tools
from mrt_py_tools.commands import resolve_deps
import subprocess
import click
import sys
import os


@click.command()
@click.argument("pkg_name", type=click.STRING, required=True)
def main(pkg_name):
    """
    This tool searches for, and clones a package from the MRT Gitlab Server into the current workspace.
    Execute this script from within a catkin workspace
    """

    if not os.path.exists("src/.rosinstall"):
        subprocess.call("wstool init .")

    repository = mrt_gitlab_tools.getRepos(pkg_name)
    if len(repository) is 0:
        print "Repository could not be found."
        sys.exit(1)
    elif len(repository) > 1:
        print "More than one repo with this name found. Please choose:"
        for index, item in enumerate(repository):
            print "(" + str(index) + ") " + item
        valid_choices = {str(x) for x in range(0, len(repository))}
        while True:
            user_choice = str(raw_input("Enter number: "))
            if user_choice in valid_choices:
                break
        repository = repository[user_choice]

    #checkout repository
    subprocess.call("wstool set "+str(pkg_name)+" --git "+str(repository)+" --confirm -t ./src 2>/dev/null > /dev/null")
    click.echo(click.style( "Search for package "+str(pkg_name), fg='red'))
    click.echo(click.style( "Found in "+str(repository)+". Cloning.", fg='green'))
    subprocess.call("wstool update "+str(pkg_name)+" -t ./src > /dev/null")

    #resolve deps
    resolve_deps.main()
