from mrt_py_tools.mrt_base_tools import cd_to_ws_root_folder
from mrt_py_tools.mrt_gitlab_tools import Git, import_repo_names
from mrt_py_tools.commands.mrt_resolve_deps import resolve_dependencies
import click


@click.command()
@click.argument("pkg_name", type=click.STRING, required=True)
def main(pkg_name):
    """
    Clone catkin packages from gitlab.
    """
    """
    This tool searches for, and clones a package from the Gitlab Server into the current workspace.
    Execute this script from within a catkin workspace
    """

    cd_to_ws_root_folder()
    git = Git()

    # clone pkg
    if git.clone_pkg(pkg_name):
        # resolve deps
        resolve_dependencies()
