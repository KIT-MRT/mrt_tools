#!/usr/bin/python
from mrt_py_tools import mrt_base_tools, mrt_gitlab_tools
import subprocess
import click
import sys
import os
import re


def update_apt_and_ros_packages():
    f_null = open(os.devnull, 'w')
    subprocess.call(["sudo", "apt-get", "update", "-o", "Dir::Etc::sourcelist=", "sources.list.d/mrt.list",
                     "-o", "Dir::Etc::sourceparts=", "-", "-o", "APT::Get::List-Cleanup=", "0"], stdout=f_null,
                    stderr=f_null)
    subprocess.check_call(["sudo", "apt-get", "install", "--only-upgrade", "mrt-cmake-modules", "--yes"], stdout=f_null)
    subprocess.check_call(["rosdep", "update"], stdout=f_null)


def resolve_dependencies():
    regex_rosdep_resolve = re.compile("ERROR\[([^\]]*)\]: Cannot locate rosdep definition for \[([^\]]*)\]")

    first_missing_dep = True

    while True:
        rosdep_process = subprocess.Popen(['rosdep', 'check', '--from-paths', 'src', '--ignore-src'],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rosdep_output, rosdep_err = rosdep_process.communicate()

        if not rosdep_err:
            break

        missing_packages = dict()
        for match in regex_rosdep_resolve.finditer(rosdep_err):
            missing_packages[match.group(2)] = match.group(1)

        if not missing_packages:
            print rosdep_output
            print rosdep_err
            sys.exit(1)

        for missing_package, package_dep_specified in missing_packages.iteritems():

            # Clone pkg
            if not mrt_gitlab_tools.clone_pkg(missing_package):
                # no Gitlab project found
                if first_missing_dep:
                    # first not found package. Update apt-get and ros.
                    first_missing_dep = False
                    click.secho("Updating mrt apt-get and rosdep and resolve again. This might take a while ...",
                                fg='green')
                    update_apt_and_ros_packages()
                    break
                else:
                    click.secho(
                        "Package " + missing_package + " (requested from: " + package_dep_specified + ") could not be found.",
                        fg='red')
                    sys.exit(1)

    # install missing system dependencies
    subprocess.check_call(["rosdep", "install", "--from-paths", "src", "--ignore-src"])


@click.command()
def main():
    """ Resolve all dependencies in this workspace."""

    mrt_base_tools.change_to_workspace_root_folder()

    resolve_dependencies()
