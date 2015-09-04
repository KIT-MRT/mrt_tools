__author__ = 'bandera'

import fnmatch
import sys
import os

if "LD_LIBRARY_PATH" not in os.environ or "/opt/ros" not in os.environ["LD_LIBRARY_PATH"]:
    print "ROS_ROOT not set. Source /opt/ros/<dist>/setup.bash"
    sys.exit(1)


def get_workspace_root_folder(current_dir):
    if not os.path.exists("src"):
        print "No source folder found. This must be run in a standard catkin workspace (where you ran catkin_make)"
        sys.exit(1)

    found = False
    while current_dir != "/" and current_dir != "":
        if ".catkin_tools" in os.listdir(current_dir):
            found = True
            break

        current_dir = os.path.dirname(current_dir)

    if not found:
        raise Exception("No catkin workspace root found.")

    return current_dir


def get_script_root():
    return os.path.dirname(os.path.realpath(__file__))


def change_to_workspace_root_folder():
    workspace_folder = get_workspace_root_folder(os.getcwd())
    os.chdir(workspace_folder)


def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result
