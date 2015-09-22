import sys
from mrt_tools.base import Git, import_repo_names, Workspace
import click

repo_list = import_repo_names()


@click.command()
@click.argument("pkg_name", type=click.STRING, required=True, autocompletion=repo_list)

def main(pkg_name):
    """
    Clone catkin packages from gitlab.
    """
    """
    This tool searches for, and clones a package from the Gitlab Server into the current workspace.
    Execute this script from within a catkin workspace
    """

    ws = Workspace()

    # Test for package
    if ws.find(pkg_name):
        click.echo("Package {0} already present in workspace, updating:".format(pkg_name))
        ws.update_only(pkg_name)
    else:
        git = Git()
        url = git.find_repo(pkg_name) # Gives error string
        if not url:
            sys.exit(1)
        ws.add(pkg_name, url)
        ws.resolve_dependencies(git=git)
