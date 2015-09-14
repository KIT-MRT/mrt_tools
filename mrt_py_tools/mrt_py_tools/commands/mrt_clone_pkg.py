__author__ = 'bandera'
from mrt_py_tools import mrt_base_tools
from mrt_py_tools import mrt_gitlab_tools
from mrt_py_tools.commands import mrt_resolve_deps
import click


@click.command()
@click.argument("pkg_name", type=click.STRING, required=True)
def main(pkg_name):
    """
    This tool searches for, and clones a package from the MRT Gitlab Server into the current workspace.
    Execute this script from within a catkin workspace
    """

    mrt_base_tools.change_to_workspace_root_folder()

    # clone pkg
    if mrt_gitlab_tools.clone_pkg(pkg_name):

        # resolve deps
        mrt_resolve_deps.resolve_dependencies()

