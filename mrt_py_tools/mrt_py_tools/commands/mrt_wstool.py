#!/usr/bin/python
from wstool import config_yaml, config as wstool_config
from mrt_py_tools.mrt_base_tools import cd_to_ws_src_folder, get_unpushed_repos
from catkin_pkg import packages
import distutils.util
import subprocess
import click
import os


def update_rosinstall():
    """
    Goes through all directories within the workspace and checks whether the rosinstall file is up to date.
    """
    # Use catking to get all packages
    all_pkgs = packages.find_packages(".")
    pathspecs = []
    for pkg in all_pkgs.keys():
        try:
            # Try to read it from package xml
            if len(all_pkgs[pkg].urls) > 1:
                raise IndexError
            ssh_url = all_pkgs[pkg].urls[0].url
        except IndexError:
            click.secho("Warning: No URL (or multiple) defined in " + pkg + "/package.xml!", fg="yellow")
            try:
                # Try reading it from git repo
                with open(pkg + "/.git/config", 'r') as f:
                    ssh_url = next(line[7:-1] for line in f if line.startswith("\turl"))
            except StopIteration:
                click.secho("Warning: Could not figure out any URL for " + pkg, fg="red")
                ssh_url = None
        pathspecs.append(config_yaml.PathSpec(pkg, "git", ssh_url))

    # Create ws config object
    wsconfig = wstool_config.Config(pathspecs, ".")

    # Create rosinstall file from config
    config_yaml.generate_config_yaml(wsconfig, ".rosinstall", "")


@click.command(context_settings=dict(ignore_unknown_options=True, ))
@click.argument('action', type=click.STRING)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def main(action, args):
    """
    A wrapper for wstool.
    """

    cd_to_ws_src_folder()
    ws_src = os.getcwd()

    if action == "init":
        click.secho("Removing wstool database src/.rosinstall", fg="yellow")
        os.remove(".rosinstall")

    # Need to init wstool?
    if not os.path.exists(".rosinstall"):
        click.echo("Initializing wstool...")
        subprocess.call("wstool init . > /dev/null", shell=True)

    update_rosinstall()

    if action == "update":

        # Search for unpushed commits
        unpushed_repos = get_unpushed_repos()

        if len(unpushed_repos) > 0:
            choice_str = raw_input("Push them now? [y/N]")
            if choice_str == "":
                choice_str = "n"
            push_now = distutils.util.strtobool(choice_str)

            if push_now:
                for x in unpushed_repos:
                    os.chdir(ws_src + x)
                    subprocess.call("git push", shell=True)

        # Speedup the pull process by parallelization
        if not [a for a in args if a.startswith("-j")]:
            args += ("-j10",)

    # Pass the rest to wstool
    os.chdir(ws_src)
    if len(args) == 0:
        subprocess.call(["wstool", action])
    else:
        subprocess.call(["wstool", action] + list(args))
