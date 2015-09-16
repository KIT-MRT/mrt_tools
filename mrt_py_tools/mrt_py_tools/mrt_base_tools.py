#!/usr/bin/python
from wstool import config as wstool_config, config_yaml
import subprocess
import fnmatch
import click
import sys
import os


__author__ = 'bandera'

# Test whether ros is sourced
if "LD_LIBRARY_PATH" not in os.environ or "/opt/ros" not in os.environ["LD_LIBRARY_PATH"]:
    print "ROS_ROOT not set. Source /opt/ros/<dist>/setup.bash"
    sys.exit(1)


def get_workspace_root_folder(current_dir):
    """
    Find the root directory of a workspace, starting from current_dir
    """
    while current_dir != "/" and current_dir != "":
        if ".catkin_tools" in os.listdir(current_dir):
            break

        current_dir = os.path.dirname(current_dir)

    return current_dir


def get_script_root():
    """
    Get the path of this script.
    :return: path
    """
    return os.path.dirname(os.path.realpath(__file__))


def change_to_workspace_root_folder():
    """
    Searches for and cd's into workspace root folder.
    Throws Exeption if root can't be found.
    """
    workspace_folder = get_workspace_root_folder(os.getcwd())

    if workspace_folder == "/" or workspace_folder == "":
        raise Exception("No catkin workspace root found.")

    os.chdir(workspace_folder)
    if not os.path.exists("src/.rosinstall"):
        subprocess.call("wstool init .")


def find(pattern, path):
    """
    Searches for a file within a directory
    :param pattern: Name to search for
    :param path: Search path
    :return: List of paths
    """
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


def get_unpushed_repos():
    """
    Search current workspace for unpushed commits
    :return: List of repository names in src/
    """

    change_to_workspace_root_folder()
    ws_root = os.getcwd()
    os.chdir("src")

    rosinstall = config_yaml.get_path_specs_from_uri(".rosinstall")
    wsconfig = wstool_config.Config(rosinstall, ".")
    unpushed_repos = []

    for ps in wsconfig.get_source():
        os.chdir(ws_root + "/src/" + ps.get_local_name())
        git_process = subprocess.Popen("git log --branches --not --remotes", shell=True, stdout=subprocess.PIPE)
        result = git_process.communicate()

        if result[0] != "":
            click.secho("Unpushed commits in repo '" + ps.get_local_name() + "'", fg="yellow")
            subprocess.call("git log --branches --not --remotes --oneline", shell=True)
            unpushed_repos.append(ps.get_local_name())

    return unpushed_repos
