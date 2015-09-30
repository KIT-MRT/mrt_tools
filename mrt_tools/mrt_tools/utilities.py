from mrt_tools.settings import *
from builtins import range
from builtins import str
import subprocess
import zipfile
import shutil
import fnmatch
import click
import sys
import os
import re


def get_script_root():
    """
    Get the path of this script.
    :return: path
    """
    return os.path.dirname(os.path.realpath(__file__))


def find_by_pattern(pattern, path):
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


def get_userinfo():
    """Read in git user infos."""

    # Check whether git is installed
    (__, dpkg_err) = subprocess.Popen("dpkg -s git", shell=True, stdout=subprocess.PIPE).communicate()

    # Read out username and email
    (name, name_err) = subprocess.Popen("git config --get user.name", shell=True,
                                        stdout=subprocess.PIPE).communicate()
    (email, mail_err) = subprocess.Popen("git config --get user.email", shell=True,
                                         stdout=subprocess.PIPE).communicate()

    # Check wether git is configured
    if dpkg_err is not None:
        click.echo("Git not found, installing...")
        subprocess.call("sudo apt-get install git", shell=True)
    if name_err is not None or name == "":
        name = click.prompt("Git user name not configured. Please enter name")
        while not click.confirm("Use '" + name + "'as git user name?"):
            name = click.prompt("Please enter new name:")
        subprocess.call("git config --global user.name '" + name + "'", shell=True)
    if mail_err is not None or email == "":
        email = click.prompt("Git user email not configured. Please enter email")
        while not click.confirm("Use '" + email + "'as git user email?"):
            name = click.prompt("Please enter new email:")
        subprocess.call("git config --global user.email '" + email + "'", shell=True)

    return {'name': name[:-1], 'mail': email[:-1]}


def get_user_choice(items, extra=None, prompt="Please choose a number", default=None):
    # Print choices
    valid_choices = []
    for index, item in enumerate(items):
        valid_choices.append(index)
        click.echo("(" + str(valid_choices[-1]) + ") " + item)
    valid_choices = list(range(0, len(items)))

    # Add default choice
    if extra:
        valid_choices.append(len(items))
        click.echo("(" + str(valid_choices[-1]) + ") " + str(extra))
    while True:
        user_choice = click.prompt(prompt + ' [0-' + str(valid_choices[-1]) + ']', type=int, default=default)
        if user_choice in valid_choices:
            if extra is not None and user_choice is valid_choices[-1]:
                # Return None if default was chosen
                return None
            else:
                return user_choice


def touch(filename, times=None):
    """create a file"""
    with open(filename, 'a'):
        os.utime(filename, times)


def update_apt_and_ros_packages():
    f_null = open(os.devnull, 'w')
    subprocess.call(["sudo", "apt-get", "update", "-o", "Dir::Etc::sourcelist=", "sources.list.d/mrt.list",
                     "-o", "Dir::Etc::sourceparts=", "-", "-o", "APT::Get::List-Cleanup=", "0"], stdout=f_null,
                    stderr=f_null)
    subprocess.check_call(["sudo", "apt-get", "install", "--only-upgrade", "mrt-cmake-modules", "--yes"], stdout=f_null)
    subprocess.check_call(["rosdep", "update"], stdout=f_null)


def zip_files(files, archive):
    """Add file to a zip archive"""
    zf = zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED)
    for filename in files:
        if isinstance(filename, tuple):
            zf.write(filename[0], arcname=filename[1])
        else:
            zf.write(filename)
    zf.close()


def check_naming(pkg_name):
    while re.match("^[a-z][a-z_]+$", pkg_name) is None:
        pkg_name = str(
            input("Please enter a package name containing only [a-z] and _ (First char must be a letter): "))

    # Fail safe
    if pkg_name[-4:] == "_ros":
        pkg_name = pkg_name[:-4]
    if pkg_name[-5:] == "_tool":
        pkg_name = pkg_name[:-5]
    if pkg_name[-4:] == "_ros":
        pkg_name = pkg_name[:-4]

    if pkg_name in get_rosdeps():
        click.secho("This name collides with a rosdep dependency. Please choose a different one.", fg="red")
        sys.exit(1)

    return pkg_name


def get_rosdeps():
    """ Returns a list of all rosdep dependencies known"""
    process = subprocess.Popen(['rosdep', 'db'], stdout=subprocess.PIPE)
    output, __ = process.communicate()
    return [line.split(" -> ")[0] for line in output.split("\n") if " -> " in line]


def create_directories(pkg_name, pkg_type, ros):
    # Check for already existing folder
    if os.path.exists("src/" + pkg_name):
        click.secho(
            "ERROR: The folder with the name ./src/" + pkg_name +
            " exists already. Please move it or choose a different package name.",
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


def create_cmakelists(pkg_name, pkg_type, ros, self_dir):
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


def create_files(pkg_name, pkg_type, ros, self_dir):
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

    create_cmakelists(pkg_name, pkg_type, ros, self_dir)


def check_and_update_cmakelists(pkg_name, current_version):
    os.chdir(pkg_name)
    with open("CMakeLists.txt") as f:
        pkg_version = f.readline()[:-1]
    if pkg_version != current_version:
        click.echo("\n{0}: Package versions not matching: {1}<->{2}".format(pkg_name.upper(), pkg_version,
                                                                            current_version))
        if click.confirm("Update CMakeLists?"):
            ros = click.confirm("ROS package?")
            pkg_type = ""
            while not ((pkg_type == "lib") or (pkg_type == "exec")):
                pkg_type = click.prompt("[lib/exec]")

            shutil.copyfile("CMakeLists.txt", "CMakeLists.txt.bak")
            create_cmakelists(pkg_name, pkg_type, ros, self_dir)

            process = subprocess.Popen("meld CMakeLists.txt.bak CMakeLists.txt", shell=True)
            process.wait()

            if not click.confirm("Do you want to keep the changes"):
                shutil.copyfile("CMakeLists.txt.bak", "CMakeLists.txt")
                os.remove("CMakeLists.txt.bak")
                return
            os.remove("CMakeLists.txt.bak")

            if click.confirm("Have you tested your changes and want to commit them now?"):
                subprocess.call("git add CMakeLists.txt", shell=True)
                subprocess.call("git commit -m 'Update CMakeLists.txt to {0}'".format(current_version), shell=True)


def set_eclipse_project_setting():
    os.chdir("build")
    for project in find_by_pattern(".project", "build"):
        os.chdir(os.path.dirname(project))
        # set environment variables
        subprocess.call(
            'awk -f $(rospack find mk)/eclipse.awk .project > .project_with_env && mv .project_with_env .project',
            shell=True)

        # add support for indexing
        if not os.path.isfile("./.settings/language.settings.xml"):
            if not os.path.isdir("./.settings"):
                os.mkdir("./.settings")
        script_dir = get_script_root()
        shutil.copy(script_dir + "/templates/language.settings.xml", "./.settings")


user = get_userinfo()
self_dir = get_script_root()
