from mrt_tools.Git import test_git_credentials
from mrt_tools.Workspace import Workspace
from mrt_tools.utilities import *


########################################################################################################################
# Workspace
########################################################################################################################
@click.group()
@click.pass_context
def main(ctx):
    """A collection of tools to perform on a catkin workspace"""
    if ctx.invoked_subcommand == "init":
        ctx.obj = Workspace(quiet=True)
    else:
        ctx.obj = Workspace()


@main.command(short_help="Initialize a catkin workspace.",
              help="This command initializes a new catkin workspace in the current directory or the one (optionally) "
                   "specified.")
@click.argument('ws_name', required=False, type=click.STRING)
@click.pass_obj
def init(ws, ws_name):
    """ Initialize a catkin workspace. """
    if ws_name:
        try:
            os.makedirs(ws_name)
            os.chdir(ws_name)
        except:
            click.secho("Can not initialize new ws, directory exists already.", fg="red")
            sys.exit(1)
    ws.create()


@main.command(short_help="Delete everything in current workspace.",
              help="ATTENTION!: This command deletes everything within the current workspace. This is intended for "
                   "development use, when test workspaces are often initialized and removed again. PS: Of course it "
                   "is first tested for uncommited and unpushed changes.")
@click.pass_obj
def remove(ws):
    """Delete everything in current workspace."""
    ws.clean()


@main.command(short_help="Delete compiled code.",
              help="This is a convenient wrapper around 'mrt catkin clean -a' and removes all build files and "
                   "binaries.")
@click.pass_obj
def clean(ws):
    """Delete compiled code."""
    ws.cd_root()
    catkin_args = ("-y",)
    process = subprocess.Popen(["catkin", "clean"] + list(catkin_args))
    process.wait()
    sys.exit(process.returncode)


@main.command(short_help="Print the git status of files in workspace.",
              help="This is a convenient wrapper around 'mrt wstool status', which tells you which files are modified "
                   "or untracked in your current workspace. Additionally it checks for unpushed commits.")
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def status(ws, args):
    """Print the git status of files in workspace"""
    ws.cd_src()

    # Show untracked files as well
    if not ("--untracked" in args or "-u" in args):
        args += ("--untracked",)

    # Pass the rest to wstool
    if len(args) == 0:
        process = subprocess.Popen("wstool status")
    else:
        process = subprocess.Popen(["wstool", "status"] + list(args))
    process.wait()

    ws.unpushed_repos()

    sys.exit(process.returncode)


@main.command(short_help="List all git repos and their status.",
              help="This is a convenient wrapper around 'mrt wstool info', which gives you a nice overview over "
                   "repos, their status, current commit and url.")
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def info(ws, args):
    """List all git repos and their status."""
    process = subprocess.Popen(['mrt wstool info'], shell=True)
    process.wait()
    sys.exit(process.returncode)


@main.command(short_help="Perform a git push & pull on every repo.",
              help="This is a convenient wrapper around 'mrt wstool update', which performs a git pull in 10 "
                   "parallel threads on every repo within your workspace. Additionally it checks for unpushed commits "
                   "and asks you whether to push them.")
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def update(ws, args):
    """Perform a git push & pull on every repo"""

    process = subprocess.Popen(['mrt wstool update'], shell=True)
    process.wait()
    sys.exit(process.returncode)


@main.command(short_help="Resolve dependencies for packages.",
              help="This command resolves all dependencies specified in the packages manifest files (package.xml) by "
                   "installing or cloning them into your current workspace. NOTE!: This fails, if you have already "
                   "sourced a different workspace containing one of the dependencies in your current terminal before "
                   "(e.g. in you bashrc).")
@click.option('-y', '--default_yes', is_flag=True, help='Default to yes when asked to install dependencies.')
@click.pass_obj
def resolve_deps(ws, default_yes):
    """Resolve dependencies for packages"""
    test_git_credentials()
    ws.resolve_dependencies(default_yes=default_yes)
