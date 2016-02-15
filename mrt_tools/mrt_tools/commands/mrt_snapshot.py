from mrt_tools.Workspace import Workspace
from mrt_tools.settings import user_settings
from mrt_tools.utilities import *
import time


########################################################################################################################
# Snapshot
########################################################################################################################
@click.group()
def main():
    """Save or restore the current state of the ws..."""
    pass


@main.command(short_help="Create a snapshot of the current workspace.",
              help="This command creates a zip file, containing the catkin configuration of the current "
                   "workspace the rosinstall file with the version of the repos pinned to the current commit. Before "
                   "doing so, the workspace is tested for uncommited and unpushed changes. Of course this only works, "
                   "if every package in your workspace is a repository and has a remote on the gitlab server. Please "
                   "note, that no other files, than those commited in the repo can be restored.")
@click.argument("name", type=click.STRING, required=True)
def create(name):
    """Create a snapshot of the current workspace."""
    suffix = "_" + time.strftime("%y%m%d")
    snapshot_name = name + suffix + user_settings['Snapshot']['FILE_ENDING']
    filename = os.path.join(os.getcwd(), snapshot_name)

    # First test whether it's safe to create a snapshot
    ws = Workspace()
    ws.test_for_changes(prompt="Are you sure you want to continue? These changes won't be included in the snapshot!")

    # Create snapshot of rosinstall
    ws.cd_root()
    ws.snapshot(filename=".rosinstall")

    # Create archive
    with open(user_settings['Snapshot']['VERSION_FILE'], "w") as f:
        f.write(user_settings['Snapshot']['SNAPSHOT_VERSION'])
    files = [('.rosinstall', 'src/.rosinstall'), '.catkin_tools', user_settings['Snapshot']['VERSION_FILE']]
    files += [os.path.join(dp, f) for dp, dn, fn in os.walk(".catkin_tools") for f in fn]
    zip_files(files, filename)
    os.remove(".rosinstall")
    os.remove(user_settings['Snapshot']['VERSION_FILE'])
    click.secho("Wrote snapshot to " + filename, fg="green")


@main.command(short_help="Restore a catkin workspace from a snapshot.",
              help="This command creates a new workspace with the name of the given snapshot file, initializes it, "
                   "copies the config files and then uses wstool update functionality to clone all repos with the "
                   "specified commit into the workspace. Finally, catkin build is called, in order to compile the "
                   "workspace. NOTE: Packages in this workspace are pinned to the specified commit. Therefor wstool "
                   "update will always reset the repo to this commit!")
@click.argument("name", type=click.STRING, required=True)
def restore(name):
    """Restore a catkin workspace from a snapshot"""
    org_dir = os.getcwd()
    filename = os.path.join(org_dir, name)
    workspace = os.path.join(org_dir, os.path.basename(name).split(".")[0] + "_snapshot_ws")

    # Read archive
    try:
        zf = zipfile.ZipFile(filename, "r", zipfile.ZIP_DEFLATED)
        # file_list = [f.filename for f in zf.filelist]
        version = zf.read(user_settings['Snapshot']['VERSION_FILE'])
    except IOError:
        click.echo(os.getcwd())
        click.secho("Can't find file: '" + name + user_settings['Snapshot']['FILE_ENDING'] + "'", fg="red")
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
        os.remove(os.path.join(workspace, user_settings['Snapshot']['VERSION_FILE']))

        # Clone packages
        click.secho("Cloning packages", fg="green")
        ws.load()
        ws.update()
        ws.resolve_dependencies()

        # Build workspace
        click.secho("Building workspace", fg="green")
        subprocess.call(["catkin", "clean", "-a"])
        subprocess.call(["catkin", "build"])

    else:
        click.secho("ERROR: Snapshot version not known.", fg="red")
