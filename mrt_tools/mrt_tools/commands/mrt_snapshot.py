from mrt_tools.utilities import *
from mrt_tools.base import *
import click
import time


########################################################################################################################
# Snapshot
########################################################################################################################
@click.group()
def main():
    """Save or restore the current state of the ws..."""
    pass


@main.command()
@click.argument("name", type=click.STRING, required=True)
def create(name):
    """Create a snapshot of the current workspace."""
    """
    This function creates a zip file, containing the workspace configuration '.catkin_tools' and a '.rosinstall' file.
    The workspace configuration contains build settings like whether 'install' was specified.
    The .rosinstall file pins every repository to the commit it is at right now.
    """
    suffix = "_" + time.strftime("%y%m%d")
    snapshot_name = name + suffix + FILE_ENDING
    filename = os.path.join(os.getcwd(), snapshot_name)

    # First test whether it's safe to create a snapshot
    ws = Workspace()
    ws.test_for_changes(prompt="Are you sure you want to continue? These changes won't be included in the snapshot!")

    # Create snapshot of rosinstall
    ws.cd_root()
    ws.snapshot(filename=".rosinstall")

    # Create archive
    with open(VERSION_FILE, "w") as f:
        f.write(SNAPSHOT_VERSION)
    files = [('.rosinstall', 'src/.rosinstall'), '.catkin_tools', VERSION_FILE]
    files += [os.path.join(dp, f) for dp, dn, fn in os.walk(".catkin_tools") for f in fn]
    zip_files(files, filename)
    os.remove(".rosinstall")
    os.remove(VERSION_FILE)
    click.secho("Wrote snapshot to " + filename, fg="green")


@main.command()
@click.argument("name", type=click.STRING, required=True)
def restore(name):
    """Restore a catkin workspace from a snapshot"""
    """
    This function takes a zip file as created in create_snapshot and tries to restore it.
    Therefor a new workspace is initiated, the settings and .rosinstall file are copied from the snapshot.
    Next, the specified commits are cloned into the workspace and the whole workspace is build.
    """
    org_dir = os.getcwd()
    filename = os.path.join(org_dir, name)
    workspace = os.path.join(org_dir, os.path.basename(name).split(".")[0] + "_snapshot_ws")

    # Read archive
    try:
        zf = zipfile.ZipFile(filename, "r", zipfile.ZIP_DEFLATED)
        # file_list = [f.filename for f in zf.filelist]
        version = zf.read(VERSION_FILE)
    except IOError:
        click.echo(os.getcwd())
        click.secho("Can't find file: '" + name + FILE_ENDING + "'", fg="red")
        sys.exit()

    if version == "0.1.0":
        # Create workspace folder
        try:
            os.mkdir(workspace)
            os.chdir(workspace)
            ws = Workspace(silent=True)
            ws.create()
        except OSError:
            click.secho("Directory {0} exists already".format(workspace), fg="red")
            os.chdir(org_dir)
            sys.exit(1)

        # Extract archive
        zf.extractall(path=workspace)
        os.remove(os.path.join(workspace, VERSION_FILE))

        # Clone packages
        click.secho("Cloning packages", fg="green")
        ws.update()
        ws.resolve_dependencies()

        # Build workspace
        click.secho("Building workspace", fg="green")
        subprocess.call(["catkin", "clean", "-a"])
        subprocess.call(["catkin", "build"])

    else:
        click.secho("ERROR: Snapshot version not known.", fg="red")
