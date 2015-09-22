#!/usr/bin/python
from mrt_py_tools.base import Workspace
from mrt_py_tools.commands import mrt_resolve_deps
import subprocess
import zipfile
import shutil
import click
import sys
import os

file_ending = ".snapshot"


def zip_files(files, archive):
    zf = zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED)
    for filename in files:
        zf.write(filename)
    zf.close()


def create_snapshot(name):
    """
    This function creates a zip file, containing the workspace configuration '.catkin_tools' and a '.rosinstall' file.
    The workspace configuration contains build settings like whether 'install' was specified.
    The .rosinstall file pins every repository to the commit it is at right now.
    """
    ws = Workspace()

    # First test whether it's safe to create a snapshot
    ws.test_for_changes()

    # Create snapshot of rosinstall
    ws.cd_root()
    ws.snapshot(filename=".rosinstall")

    # Create archive
    files = ['.rosinstall', '.catkin_tools']
    zip_files(files, name + file_ending)
    os.remove(".rosinstall")
    click.secho("Wrote snapshot to " + os.path.abspath(name + file_ending), fg="green")


def restore_snapshot(name):
    """
    This function takes a zip file as created in create_snapshot and tries to restore it.
    Therefor a new workspace is initiated, the settings and .rosinstall file are copied from the snapshot.
    Next, the specified commits are cloned into the workspace and the whole workspace is build.
    """
    org_dir = os.getcwd()
    # Create workspace folder
    try:
        os.mkdir(name + "_snapshot_ws")
    except OSError:
        click.secho("Directory " + name + "_snapshot exists already", fg="red")
        sys.exit(1)

    # Init catkin workspace
    os.chdir(name + "_snapshot_ws")
    try:
        Workspace(init=True)
    except:
        os.chdir(org_dir)
        shutil.rmtree(name + "_snapshot_ws")
        sys.exit(1)

    # Extract archive and copy files
    try:
        zf = zipfile.ZipFile("../" + name + file_ending, "r", zipfile.ZIP_DEFLATED)
        zf.extractall()  # .catkin_tools is already at the right spot
        shutil.copy(".rosinstall", "src")
        os.remove(".rosinstall")
        # Recreate Workspace
        ws = Workspace()
    except IOError:
        print os.getcwd()
        click.secho("Can't find file: '" + name + file_ending + "'", fg="red")
        os.chdir(org_dir)
        shutil.rmtree(name + "_snapshot_ws")
        sys.exit(1)

    # Clone packages
    click.secho("Cloning packages", fg="green")
    ws.update()
    ws.resolve_dependencies()

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

    if name.endswith(file_ending):
        name = name[:-len(file_ending)]
    if action == "create":
        create_snapshot(name)
    elif action == "restore":
        restore_snapshot(name)
    else:
        click.secho("Action must be one of [create|restore]", fg="red")
        sys.exit()
