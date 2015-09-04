#!/usr/bin/python
from mrt_py_tools import mrt_base_tools
from mrt_py_tools import mrt_gitlab_tools
import os
import sys
import subprocess
from subprocess import Popen, PIPE
import re
import colorama
import click
import gitlab

colorama.init()


def update_apt_and_ros_packages():
    f_null = open(os.devnull, 'w')
    subprocess.call(["sudo", "apt-get", "update", "-o", "Dir::Etc::sourcelist=", "sources.list.d/mrt.list",
                     "-o", "Dir::Etc::sourceparts=", "-", "-o", "APT::Get::List-Cleanup=", "0"], stdout=f_null,
                    stderr=f_null)
    subprocess.check_call(["sudo", "apt-get", "install", "--only-upgrade", "mrt-cmake-modules", "--yes"], stdout=f_null)
    subprocess.check_call(["rosdep", "update"], stdout=f_null)


@click.command()
def main():
    """ Resolve all dependencies in this workspace."""
    regex_rosdep_resolve = re.compile("ERROR\[([^\]]*)\]: Cannot locate rosdep definition for \[([^\]]*)\]")

    first_missing_dep = True

    mrt_base_tools.change_to_workspace_root_folder()

    while True:
        rosdep_process = Popen(['rosdep', 'check', '--from-paths', 'src', '--ignore-src'], stdout=PIPE, stderr=PIPE)
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

        projects = mrt_gitlab_tools.getRepos()
        for missing_package, package_dep_specified in missing_packages.iteritems():
            print colorama.Fore.RED + "Search for package " + missing_package + " (requested from: " + package_dep_specified + ")" + colorama.Fore.RESET

            # search for a gitlab projects
            gitlab_projects = list()
            for project in projects:
                if project["name"] == missing_package:
                    gitlab_projects.append(project)

            ssh_url = ""
            if len(gitlab_projects) == 0:
                # no gitlab project found
                if first_missing_dep:
                    # first not found package. Update apt-get and ros.
                    first_missing_dep = False
                    print colorama.Fore.GREEN + "Updating mrt apt-get and rosdep and resolve again. This might take a while ..." + colorama.Fore.RESET
                    update_apt_and_ros_packages()
                    break

                while True:
                    # gitlab project not found. Prompt user to specify git uri for repository
                    ssh_url = raw_input("Enter git url: ")

                    # check if valid git repositry is specified
                    git_process = Popen(['git', 'ls-remote', ssh_url], stdout=PIPE, stderr=PIPE)
                    git_output, git_err = git_process.communicate()

                    # git repository found
                    if git_err:
                        print "Invalid git repository specified. Try again."
                        continue

                    break

            # TODO move this into the find routine
            elif len(gitlab_projects) == 1:
                # only one project found select this on.
                ssh_url = gitlab_projects[0]["ssh_url_to_repo"]
            else:
                # multiple gitlab projects found. Prompt user.
                print "Multiple gitlab projects found:"
                for idx, gitlabProject in enumerate(gitlab_projects):
                    print "[" + str(idx) + "]: " + gitlabProject["ssh_url_to_repo"]

                selectionInt = -1
                while True:
                    selectionStr = raw_input("Select repository: ")
                    try:
                        selectionInt = int(selectionStr)
                        if selectionInt < 0 or selectionInt >= len(gitlab_projects):
                            raise ValueError()
                        break;
                    except ValueError:
                        print "Invalid input. Try again."

                ssh_url = gitlab_projects[idx]["ssh_url_to_repo"]

            # add specified git repository (ignore errors because repository could be added but not checked out)
            f_null = open(os.devnull, 'w')
            print colorama.Fore.GREEN + "Found in " + ssh_url + ". Cloning." + colorama.Fore.RESET
            subprocess.call(["wstool", "set", missing_package, "--git", ssh_url, "--confirm", "-t", "src"],
                            stdout=f_null,
                            stderr=f_null)
            subprocess.call(["wstool", "update", missing_package, "-t", "src"], stdout=f_null)

    # install missing system dependencies
    subprocess.check_call(["rosdep", "install", "--from-paths", "src", "--ignore-src"])
