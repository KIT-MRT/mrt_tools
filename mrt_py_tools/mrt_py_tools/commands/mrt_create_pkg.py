#!/usr/bin/python
import shutil
import subprocess
from mrt_py_tools import mrt_base_tools
from mrt_py_tools import mrt_gitlab_tools
import click
import re
import os
import sys

self_dir = mrt_base_tools.get_script_root()
mrt_base_tools.change_to_workspace_root_folder()
user = mrt_gitlab_tools.get_userinfo()


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def check_naming(pkg_name):
    while re.match("^[a-z][a-z_]+$", pkg_name) is None:
        pkg_name = str(
            raw_input("Please enter a package name containing only [a-z] and _ (First char must be a letter): "))

    # Fail safe
    if pkg_name[-4:] == "_ros":
        pkg_name = pkg_name[:-4]
    if pkg_name[-5:] == "_tool":
        pkg_name = pkg_name[:-5]
    if pkg_name[-4:] == "_ros":
        pkg_name = pkg_name[:-4]

    return pkg_name


def create_directories(pkg_name, pkg_type, ros, create_git_repo):
    # Check for already existing folder
    if os.path.exists("src/" + pkg_name):
        click.secho(
            "ERROR: The folder with the name ./src/" + pkg_name + " exists already. Please move it or choose a different package name.",
            fg="red")
        sys.exit(1)

    # Create folders
    os.makedirs("src/" + pkg_name)
    os.chdir("src/" + pkg_name)

    if pkg_type == "exec":
        os.makedirs("include/" + pkg_name + "/internal")
        touch("include/" + pkg_name + "/internal/.gitignore")

    os.mkdir("test")
    os.mkdir("src")
    touch("src/.gitignore")

    if ros is True and pkg_type == "exec":
        os.mkdir("res")
        os.makedirs("launch/params")
        touch("launch/params/.gitignore")


def create_files(pkg_name, pkg_type, ros, create_git_repo):
    # Create files and replace with user info
    # Readme and test file
    shutil.copyfile(self_dir + "/templates/README.md", "README.md")
    shutil.copyfile(self_dir + "/templates/test.cpp", "./test/test_" + pkg_name + ".cpp")

    # Package.xml
    if ros:
        shutil.copyfile(self_dir + "/templates/package_ros.xml", "./package.xml")
    else:
        shutil.copyfile(self_dir + "/templates/package.xml", "./package.xml")

    subprocess.call("sed -i " +
                    "-e 's/\${PACKAGE_NAME}/" + pkg_name + "/g' " +
                    "-e 's/\${CMAKE_PACKAGE_NAME}/" + pkg_name.upper() + "/g' " +
                    "-e 's/\${USER_NAME}/" + user['name'] + "/g' " +
                    "-e 's/\${USER_EMAIL}/" + user['mail'] + "/g' " +
                    "package.xml", shell=True)

    # CMakeLists.txt
    # build mask @12|34@
    # pos1: non ros package
    # pos2: ros package
    # pos3: library
    # pos4: executable
    pattern = "@"
    if ros:
        pattern += ".x"
    else:
        pattern += "x."
    pattern += "|"

    if pkg_type == "lib":
        pattern += "x.@"
    elif pkg_type == "exec":
        pattern += ".x@"

    shutil.copyfile(self_dir + "/templates/CMakeLists.txt", "./CMakeLists.txt")
    subprocess.call("sed -i " +
                    "-e 's/^" + pattern + " //g' " +
                    "-e '/^@..|..@/d' " +
                    "-e 's/\${CMAKE_PACKAGE_NAME}/" + pkg_name + "/g' " +
                    "CMakeLists.txt", shell=True)


@click.command()
@click.argument("pkg_name", type=click.STRING, required=True)
@click.option('-t', 'pkg_type', type=click.Choice(['lib', 'exec']), help="Type: Choose between library or executable",
              prompt="Please choose package type [lib|exec]")
@click.option('-r', 'ros', is_flag=True, help="Make ROS package", prompt="Should this be a ROS package?")
@click.option('-g', 'create_git_repo', is_flag=True, help="Create Git repository", prompt="Create a git repository?")
def main(pkg_name, pkg_type, ros, create_git_repo):
    """ Create a new catkin package """

    pkg_name = check_naming(pkg_name)

    if ros:
        pkg_name += "_ros"
    if pkg_type == "exec":
        pkg_name += "_tool"

    click.echo("Creating package with name.... " + pkg_name)
    click.echo("     --> Package type.... " + pkg_type)
    if ros:
        click.echo("     --> Create ROS Package.... YES")
    else:
        click.echo("     --> Create ROS Package.... NO")
    if create_git_repo:
        click.echo("     --> Create  gitlab repository.... YES")
    else:
        click.echo("     --> Create  gitlab repository.... NO")
    click.echo("     --> Package Maintainer.... " + user['name'] + " <" + user['mail'] + ">")

    create_directories(pkg_name, pkg_type, ros, create_git_repo)
    create_files(pkg_name, pkg_type, ros, create_git_repo)

    if create_git_repo:
        ssh_url = mrt_gitlab_tools.create_repo(pkg_name)
        subprocess.call("sed -i " +
                        "-e 's#\${PACKAGE_REPOSITORY_URL}#" + ssh_url + "#g' " +
                        "package.xml", shell=True)
        # Initialize repository
        mrt_base_tools.change_to_workspace_root_folder()
        os.chdir("src/" + pkg_name)
        subprocess.call("git init", shell=True)
        subprocess.call("git remote add origin " + ssh_url + " >/dev/null 2>&1", shell=True)
        with open('.gitignore', 'w') as f:
            f.write("*~")
        subprocess.call("git add . >/dev/null 2>&1", shell=True)
        subprocess.call("git commit -m 'Initial commit' >/dev/null 2>&1", shell=True)
        subprocess.call("git push -u origin master >/dev/null 2>&1", shell=True)
        os.chdir("..")

        # Register with rosdep
        if not os.path.exists(".rosinstall"):
            click.echo("Initializing wstool")
            subprocess.call("wstool init . >/dev/null 2>&1", shell=True)

        subprocess.call("wstool set " + pkg_name + " --git "+ssh_url+" --confirm -t . >/dev/null", shell=True)
