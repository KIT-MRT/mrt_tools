#!/usr/bin/python
from mrt_tools.base import Workspace
import subprocess
import click
import os


@click.command(context_settings=dict(ignore_unknown_options=True, ))
@click.argument('action', type=click.STRING)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def main(action, args):
    """
    A wrapper for wstool.
    """
    ws = Workspace()
    ws.cd_src()

    if action == "init":
        click.secho("Removing wstool database src/.rosinstall", fg="yellow")
        os.remove(".rosinstall")
        click.echo("Initializing wstool...")
        ws.scan()
        return

    # Need to init wstool?
    if not os.path.exists(".rosinstall"):
        ws.write()

    if action == "update":

        # Search for unpushed commits
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

    if action == "status" or action == "info":
        # Show untracked files as well
        if not ("--untracked" in args or "-u" in args):
            args += ("--untracked",)
    
    # Pass the rest to wstool
    ws.cd_src()
    if len(args) == 0:
        subprocess.call(["wstool", action])
    else:
        subprocess.call(["wstool", action] + list(args))

    if action == "status":
        ws.unpushed_repos()
