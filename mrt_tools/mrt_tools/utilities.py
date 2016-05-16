from mrt_tools.settings import user_settings
from builtins import str
import subprocess
import zipfile
import shutil
import fnmatch
import click
import sys
import os
import re
import xml.etree.ElementTree as ET


def is_ros_sourced():
    # Test whether ros is sourced
    return "ROS_ROOT" in os.environ


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


def get_gituserinfo(quiet=False):
    """Read in git user infos."""

    # Check whether git is installed
    (__, dpkg_err) = subprocess.Popen("dpkg -s git", shell=True, stdout=subprocess.PIPE).communicate()

    # Read out username and email
    (name, name_err) = subprocess.Popen("git config --get user.name", shell=True,
                                        stdout=subprocess.PIPE).communicate()
    (email, mail_err) = subprocess.Popen("git config --get user.email", shell=True,
                                         stdout=subprocess.PIPE).communicate()
    (credential_helper, credential_err) = subprocess.Popen("git config --get credential.helper", shell=True,
                                                           stdout=subprocess.PIPE).communicate()

    # Check whether git is configured
    if not quiet:
        if dpkg_err is not None:
            click.echo("Git not found, installing...")
            subprocess.call("sudo apt-get install git", shell=True)
        if name_err is not None or name == "":
            name = click.prompt("Git user name not configured. Please enter your first and last name")
            set_gituserinfo(name=name)
        if mail_err is not None or email == "":
            email = click.prompt("Git user email not configured. Please enter email")
            set_gituserinfo(email=email)
        if user_settings['Gitlab']['CACHE_GIT_CREDENTIALS_FOR_HTTPS_REPOS'] \
                and credential_helper != "cache --timeout={}".format(user_settings['Gitlab']['GIT_CACHE_TIMEOUT']):
            set_gituserinfo(credential_helper="cache --timeout={}".format(user_settings['Gitlab']['GIT_CACHE_TIMEOUT']))

    return {'name': name[:-1], 'email': email[:-1]}


def set_gituserinfo(name=None, email=None, credential_helper=None):
    if name is not None:
        subprocess.call("git config --global user.name '{}'".format(name), shell=True)
    if email is not None:
        subprocess.call("git config --global user.email '{}'".format(email), shell=True)
    if credential_helper is not None:
        subprocess.call("git config --global credential.helper '{}'".format(credential_helper), shell=True)


def get_user_choice(items, extra=None, prompt="Please choose a number", default=None):
    """
    Function to make user choose from a list of options
    :param items: List of strings
    :param extra: String or list of strings with additional options
    :param prompt: Prompt string
    :param default: Default choice
    :return: Index of choice, choice string
    """
    # Test for extra choices
    if not extra:
        extra = []
    if not isinstance(extra, list):
        extra = [extra]

    # Create choices
    choices = {index: item for index, item in enumerate(items + extra)}

    # Print choices
    for key, value in choices.items():
        click.echo("(" + str(key) + ") " + str(value))

    # Get choice
    while True:
        user_choice = click.prompt(prompt + ' [0-' + str(choices.keys()[-1]) + ']', type=int, default=default)
        if user_choice in choices.keys():
            return user_choice, choices[user_choice]


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
    while re.match("^[a-z][a-z_0-9]+$", pkg_name) is None:
        pkg_name = click.prompt(
                "Please enter a package name containing only [a-z], [0-9] and _ (First char must be a letter): ")

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

    if pkg_type == "lib":
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


def create_files(pkg_name, pkg_type, ros):
    # Create files and replace with user info
    user = get_gituserinfo()
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
                    "-e 's/\${USER_NAME}/" + user['name'].decode("utf8") + "/g' " +
                    "-e 's/\${USER_EMAIL}/" + user['email'].decode("utf8") + "/g' " +
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


def set_eclipse_project_setting(ws_root):
    build_dir = os.path.join(ws_root, "build")
    for project in find_by_pattern(".project", build_dir):
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

        # hide catkin files, etc.
        if os.path.isfile("./.project"):
            template_tree = ET.parse(script_dir + "/templates/project_filter.xml")
            template_root = template_tree.getroot()

            project_tree = ET.parse("./.project")
            project_root = project_tree.getroot()

            project_root.append(template_root)
            project_tree.write("./.project", encoding="UTF-8", xml_declaration=True)


def cache_repos():
    # For caching
    import time

    now = time.time()
    try:
        # Read in last modification time
        last_mod_lock = os.path.getmtime(user_settings['Cache']['CACHE_LOCK_FILE'])
    except OSError:
        # Set modification time to 2 * default_repo_cache_time ago
        last_mod_lock = now - 2 * user_settings['Cache']['CACHE_LOCK_DECAY_TIME']
        touch(user_settings['Cache']['CACHE_LOCK_FILE'])

    # Keep caching process from spawning several times
    if (now - last_mod_lock) > user_settings['Cache']['CACHE_LOCK_DECAY_TIME']:
        touch(user_settings['Cache']['CACHE_LOCK_FILE'])
        devnull = open(os.devnull, 'wb')  # use this in python < 3.3; python >= 3.3 has subprocess.DEVNULL
        subprocess.Popen(['mrt maintenance update_repo_cache --quiet'], shell=True, stdin=devnull, stdout=devnull,
                         stderr=devnull)


def import_repo_names(ctx=None, incomplete=None, cwords=None, cword=None):
    """
    Try to read in repos from cached file.
    If file is older than default_repo_cache_time seconds, a new list is retrieved from server.
    """
    try:
        # Read in repo list from cache
        with open(user_settings['Cache']['CACHE_FILE'], "r") as f:
            repos = f.read()
        return repos.split(",")[:-1]
    except OSError:
        return []


def changed_base_yaml():
    click.echo("Testing for changes in rosdeps...")
    import hashlib
    hasher = hashlib.md5()

    # Read hashes
    try:
        with open(user_settings['Other']['BASE_YAML_FILE'], 'rb') as f:
            buf = f.read()
            hasher.update(buf)
            new_hash = hasher.hexdigest()
    except IOError:
        new_hash = ""
        click.secho("{}: File not found. Have you installed mrt-cmake-modules?".format(
                user_settings['Other']['BASE_YAML_FILE']), fg="red")

    try:
        with open(user_settings['Other']['BASE_YAML_HASH_FILE'], 'r') as f:
            old_hash = f.read()
    except IOError:
        old_hash = ""
        if not os.path.exists(os.path.dirname(user_settings['Other']['BASE_YAML_HASH_FILE'])):
            os.makedirs(os.path.dirname(user_settings['Other']['BASE_YAML_HASH_FILE']))
        with open(user_settings['Other']['BASE_YAML_HASH_FILE'], 'wb') as f:
            f.write("")

    # Compare hashes
    if old_hash == new_hash:
        return False
    else:
        with open(user_settings['Other']['BASE_YAML_HASH_FILE'], 'w') as f:
            f.truncate()
            f.write(new_hash)
        return True


self_dir = get_script_root()
cache_repos()
