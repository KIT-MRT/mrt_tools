from builtins import str
from builtins import input
#!/usr/bin/python
from mrt_tools.base import Git, get_userinfo, Workspace, get_script_root, touch
import subprocess
import shutil
import click
import re
import os
import sys

user = get_userinfo()


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


@click.command()
@click.argument("pkg_name", type=click.STRING, required=True)
@click.option('-t', 'pkg_type', type=click.Choice(['lib', 'exec']), help="Type: Choose between library or executable",
              prompt="Please choose package type [lib|exec]")
@click.option('-r', 'ros', is_flag=True, help="Make ROS package", prompt="Should this be a ROS package?")
@click.option('-g', 'create_git_repo', is_flag=True, help="Create Git repository", prompt="Create a git repository?")
def main(pkg_name, pkg_type, ros, create_git_repo):
    """ Create a new catkin package """
    ws = Workspace()
    ws.cd_root()
    self_dir = get_script_root()

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

    create_directories(pkg_name, pkg_type, ros)
    create_files(pkg_name, pkg_type, ros, self_dir)

    if create_git_repo:
        git = Git()
        ssh_url = git.create_repo(pkg_name)
        subprocess.call("sed -i " +
                        "-e 's#\${PACKAGE_REPOSITORY_URL}#" + ssh_url + "#g' " +
                        "package.xml", shell=True)
        # Initialize repository
        ws.cd_src()
        os.chdir(pkg_name)
        subprocess.call("git init", shell=True)
        subprocess.call("git remote add origin " + ssh_url + " >/dev/null 2>&1", shell=True)
        with open('.gitignore', 'w') as f:
            f.write("*~")
        subprocess.call("git add . >/dev/null 2>&1", shell=True)
        subprocess.call("git commit -m 'Initial commit' >/dev/null 2>&1", shell=True)
        subprocess.call("git push -u origin master >/dev/null 2>&1", shell=True)
        ws.add(pkg_name, ssh_url)
