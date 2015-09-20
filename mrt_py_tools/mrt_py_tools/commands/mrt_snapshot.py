#!/usr/bin/python
from mrt_py_tools.mrt_base_tools import cd_to_ws_root_folder, get_unpushed_repos
from mrt_py_tools.commands import mrt_init_workspace, mrt_resolve_deps
from wstool import multiproject_cli, multiproject_cmd
import subprocess
import zipfile
import shutil
import click
import yaml
import sys
import os

fileending = ".snapshot"


def zip_files(files, archive):
    zf = zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED)
    for filename in files:
        absname = filename
        zf.write(absname)
    zf.close()


def test_for_changes(wsconfig):
    """ Test workspace for any changes that are not yet pushed to the server """

    # Parse git status messages
    statuslist = multiproject_cmd.cmd_status(wsconfig, untracked=True)
    statuslist = [{k["entry"].get_local_name(): k["status"]} for k in statuslist if k["status"] != ""]

    # Check for unpushed commits
    unpushed_repos = get_unpushed_repos()

    # Prompt user if changes detected
    if len(unpushed_repos) > 0 or len(statuslist) > 0:
        if len(statuslist) > 0:
            click.secho("\nYou have the following uncommited changes:", fg="red")
            for e in statuslist:
                click.echo(e.keys()[0])
                click.echo(e.values()[0])

        click.confirm("Are you sure you want to continue to create a snapshot?" +
                      " These changes won't be included in the snapshot!", abort=True)


def create_snapshot(name):
    """
    This function creates a zip file, containing the workspace configuration '.catkin_tools' and a '.rosinstall' file.
    The workspace configuration contains build settings like whether 'install' was specified.
    The .rosinstall file pins every repository to the commit it is at right now.
    """
    # Change to root of ws
    cd_to_ws_root_folder()

    # Read in .rosinstall
    wsconfig = multiproject_cli.multiproject_cmd.get_config("src", config_filename=".rosinstall")

    # First test whether it's safe to create a snapshot
    test_for_changes(wsconfig)

    # Create snapshot of rosinstall
    cd_to_ws_root_folder()
    source_aggregate = multiproject_cmd.cmd_snapshot(wsconfig)
    with open('.rosinstall', 'w') as f:
        f.writelines(yaml.safe_dump(source_aggregate))

    # Create archive
    files = ['.rosinstall', '.catkin_tools']
    zip_files(files, name + fileending)
    os.remove(".rosinstall")
    click.secho("Wrote snapshot to " + os.path.abspath(name + fileending), fg="green")


def restore_snapshot(name):
    """
    This function takes a zip file as created in create_snapshot and tries to restore it.
    Therefor a new workspace is initiated, the settings and .rosinstall file are copied from the snapshot.
    Next, the specified commits are cloned into the workspace and the whole workspace is build.
    """

    # Create workspace folder
    try:
        os.mkdir(name + "_snapshot_ws")
    except OSError:
        click.secho("Directory " + name + "_snapshot exists already", fg="red")
        sys.exit(1)
    os.chdir(name + "_snapshot_ws")

    # Init catkin workspace
    try:
        click.secho("Creating workspace", fg="green")
        mrt_init_workspace.init_workspace()
    except:
        os.chdir("../..")
        shutil.rmtree(name + "_snapshot_ws")
        sys.exit(1)

    # Extract archive and copy files
    os.chdir("..")
    try:
        zf = zipfile.ZipFile("../" + name + fileending, "r", zipfile.ZIP_DEFLATED)
        zf.extractall() # .catkin_tools is already at the right spot
        shutil.copy(".rosinstall", "src")
        os.remove(".rosinstall")
    except IOError:
        print os.getcwd()
        click.secho("Can't find file: '" + name + fileending + "'", fg="red")
        shutil.rmtree(name + "_snapshot_ws")
        sys.exit(1)

    # Clone packages
    os.chdir("src")
    click.secho("Cloning packages", fg="green")
    subprocess.call(["wstool", "update"])
    mrt_resolve_deps.resolve_dependencies()

    # Build workspace
    click.secho("Building workspace", fg="green")
    subprocess.call(["catkin", "clean", "-a"])
    subprocess.call(["catkin", "build"])


@click.command()
@click.argument('action', type=click.STRING, required=True)
@click.argument("name", type=click.STRING, required=True)
def main(action, name):
    """Create a snapshot of the current workspace.\n
    :param ACTION: Can be 'create' or 'restore' \n
    :param NAME: Name of the snapshot to create or restore
    """

    if name.endswith(fileending):
        name = name[:-len(fileending)]
    if action == "create":
        create_snapshot(name)
    elif action == "restore":
        restore_snapshot(name)
    else:
        click.secho("Action must be one of [create|restore]", fg="red")
        sys.exit()
