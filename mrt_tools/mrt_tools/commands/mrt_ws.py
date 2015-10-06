from mrt_tools.utilities import *
from mrt_tools.base import *
import click


########################################################################################################################
# Workspace
########################################################################################################################
@click.group()
@click.pass_context
def main(ctx):
    """A collection of tools to perform on a catkin workspace"""
    ctx.obj = Workspace(silent=True)

    if not ctx.obj.exists() and ctx.invoked_subcommand != "init":
        click.secho("No catkin workspace root found.", fg="red")
        click.echo("This command must be invoked from within a workspace")
        sys.exit(1)

    # For caching
    import time
    now = time.time()
    try:
        # Read in last modification time
        last_mod_lock = os.path.getmtime(os.path.expanduser(default_cache_lock))
    except OSError:
        # Set modification time to 2 * default_repo_cache_time ago
        last_mod_lock = now - 2 * default_cache_lock_decay_time
        touch(os.path.expanduser(default_cache_lock))

    # Keep caching process from spawning several times
    if (now - last_mod_lock) > default_cache_lock_decay_time:
        touch(os.path.expanduser(default_cache_lock))
        devnull = open(os.devnull, 'wb')  # use this in python < 3.3; python >= 3.3 has subprocess.DEVNULL
        subprocess.Popen(['mrt fix update_repo_cache'], shell=True, stdout=devnull, stderr=devnull)



@main.command()
@click.pass_obj
def init(ws):
    """ Initialize a catkin workspace. """
    ws.create()


@main.command()
@click.pass_obj
def remove(ws):
    """Delete everything in current workspace."""
    ws.clean()


@main.command()
@click.argument('catkin_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def clean(ws, catkin_args):
    """Delete compiled code."""
    ws.cd_root()
    if not catkin_args:
        catkin_args = ("-a",)

    if len(catkin_args) == 0:
        subprocess.call(["catkin", "clean"])
    else:
        subprocess.call(["catkin", "clean"] + list(catkin_args))


@main.command()
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
        subprocess.call("wstool status")
    else:
        subprocess.call(["wstool", "status"] + list(args))

    ws.unpushed_repos()


@main.command()
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def info(ws, args):
    """List all git repos and their status."""
    ws.cd_src()

    # Show untracked files as well
    if not ("--untracked" in args or "-u" in args):
        args += ("--untracked",)

    # Pass the rest to wstool
    if len(args) == 0:
        subprocess.call(["wstool", "info"])
    else:
        subprocess.call(["wstool", "info"] + list(args))


@main.command()
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def update(ws, args):
    """Perform a git push & pull on every repo"""
    ws.cd_src()
    # Search for unpushed commits
    ws.recreate_index()  # Rebuild .rosinstall in case a package was deletetd manually
    unpushed_repos = ws.unpushed_repos()

    if len(unpushed_repos) > 0:
        if click.confirm("Push them now?"):
            for x in unpushed_repos:
                ws.cd_src()
                os.chdir(x)
                subprocess.call("git push", shell=True)

    # Speedup the pull process by parallelization
    if not [a for a in args if a.startswith("-j")]:
        args += ("-j10",)

    # Pass the rest to wstool
    subprocess.call(["wstool", "update", "-t", ws.src] + list(args))





