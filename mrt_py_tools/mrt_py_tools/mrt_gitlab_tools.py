#!/usr/bin/python
from wstool import config_yaml, multiproject_cli
from requests.packages import urllib3
import subprocess
import getpass
import gitlab
import click
import sys
import os

urllib3.disable_warnings()


# Define paths
token_dir = os.path.expanduser("~/.mrtgitlab")
token_file = token_dir + "/.token"
host = "https://gitlab.mrt.uni-karlsruhe.de"


def create_gitlab_token_file():
    """
    This function asks for the Gitlab user name and password, in order to create a local private token file.
    Normally this function has to be called only once. From then on, the token file is used to communicate with the server.
    """
    username = raw_input("Gitlab user name: ")
    password = getpass.getpass()
    git = gitlab.Gitlab(host)
    git.login(username, password)
    gitlab_user = git.currentuser()
    token = gitlab_user['private_token']

    # Write to file
    if not os.path.exists(token_dir):
        os.mkdir(token_dir)

    if not os.path.isfile(token_file):
        os.mknod(token_file)
    os.write(os.open(token_file, 1), token)


def check_for_token_file():
    """
    This function searches for a private token file and creates it if not found.
    The token file is an authentication key for communicating with the gitlab server through the python API.
    """
    # Check for token file
    if not os.path.isfile(token_file):
        for i in range(0, 3):
            try:
                create_gitlab_token_file()
                break
            except:
                print("Cannot connect to gitlab server. Try again")


def check_sshkey():
    """
    This function tests for the presence and functionality of a ssh-key.
    The ssh-key is an authentication key for communicating with the gitlab server through the git cli-tool.
    """
    exit_code = os.system(
        'ssh -T -o "StrictHostKeyChecking=no" -o "BatchMode=yes" -o "ConnectTimeout=3" git@gitlab.mrt.uni-karlsruhe.de > /dev/null 2>&1')  # check for ssh key
    if exit_code is not 0:
        click.echo("Your SSH Key does not seem to work. Have you created one and added it to gitlab?")
        sys.exit(1)


def connect():
    """
    Connects to the server
    :return: git object
    """
    check_sshkey()
    check_for_token_file()
    # Connect
    token = os.read(os.open(token_file, 0), 20)
    git = gitlab.Gitlab(host, token=token)
    return git


def get_namespaces():
    """
    This function returns a list of all namespaces in Gitlab
    :return: List of namespace names
    """
    # Check namespaces
    click.echo("Retrieving namespaces...")
    git = connect()
    namespaces = {project['namespace']['name']: project['namespace']['id'] for project in git.getall(git.getprojects)}
    if git.currentuser()['username'] not in namespaces.keys():
        namespaces[
            git.currentuser()['username']] = 0  # The default user namespace_id will be created with first userproject
    return namespaces


def get_repos():
    """
    This function returns a list of all repositories in Gitlab
    :return: List of repositories names
    """
    # Get all repos
    git = connect()
    return list(git.getall(git.getprojects))


def find_repo(pkg_name, ns=None):
    """
    Searches for a repository within gitlab.
    If repositories in different namespaces are found, the user is asked to select one.
    :param pkg_name: Repo to search for
    :param ns: Namespace to search in
    :return: SSH URL of repository
    """
    # Search for repo
    click.secho("Search for package " + pkg_name, fg='red')
    git = connect()
    results = git.searchproject(pkg_name)

    if ns is not None:
        try:
            return next(x["ssh_url_to_repo"] for x in results if x["path_with_namespace"] == str(ns) + "/" + pkg_name)
        except:
            return ""

    exact_hits = [res for res in results if res["name"] == pkg_name]
    count = len(exact_hits)

    if count is 0:
        # None found
        click.secho("Package " + pkg_name + " could not be found.", fg='red')
        return ""
    if count is 1:
        # Only one found
        user_choice = 0
    if count > 1:
        # Multiple found
        print "More than one repo with \"" + str(pkg_name) + "\" found. Please choose:"
        for index, item in enumerate(exact_hits):
            print "(" + str(index) + ") " + item["path_with_namespace"]
        valid_choices = range(0, count)
        while True:
            user_choice = int(raw_input("Enter number: "))
            if user_choice in valid_choices:
                break

    ssh_url = exact_hits[user_choice]['ssh_url_to_repo']
    click.secho("Found " + exact_hits[user_choice]['path_with_namespace'] + ". Cloning.", fg='green')

    return ssh_url


def clone_pkg(pkg_name):
    """
    This function searches for and clones a repository.
    :param pkg_name: Repository to clone
    :return: Boolean for success
    """
    # Check whether package exists already
    f_null = open(os.devnull, 'w')
    wstool_process = subprocess.Popen(['wstool', 'info', pkg_name, "-t", "src"],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    wstool_output, wstool_err = wstool_process.communicate()

    if wstool_err:
        ssh_url = find_repo(pkg_name)
        if ssh_url == "":
            return False

        # add specified git repository to rosinstall
        wsconfig = multiproject_cli.multiproject_cmd.get_config("src", config_filename=".rosinstall")
        ps = config_yaml.PathSpec(pkg_name, "git", ssh_url)
        wsconfig.add_path_spec(ps)
        config_yaml.generate_config_yaml(wsconfig, ".rosinstall", "")
    else:
        click.echo("Package " + pkg_name + " exists already.")

    subprocess.call(["wstool", "update", pkg_name, "-t", "src"], stdout=f_null)
    return True


def create_repo(pkg_name):
    """
    This function creates a new repository on the gitlab server.
    It lets the user choose the namespace and tests whether the repo exists already.
    """
    namespaces = get_namespaces()

    # Dialog to choose namespace
    print "Available namespaces in gitlab:"
    for index, item in enumerate(namespaces):
        print "(" + str(index) + ") " + item
    valid_choices = {str(x) for x in range(0, len(namespaces))}
    while True:
        user_choice = str(raw_input("Please select one of the above namespaces for your new project: "))
        if user_choice in valid_choices:
            break
    print "Using namespace '" + namespaces.keys()[int(user_choice)] + "'"
    ns_id = namespaces.values()[int(user_choice)]

    # Check whether repo exists
    ssh_url = find_repo(pkg_name, namespaces.keys()[int(user_choice)])

    if ssh_url != "":
        click.secho("    ERROR Repo exist already: " + ssh_url, fg='red')
        sys.exit(1)

    # Create repo
    git = connect()
    if ns_id == 0:  # Create new user namespace
        request = git.createproject(pkg_name)
    else:
        request = git.createproject(pkg_name, namespace_id=ns_id)
    if not request:
        click.secho("There was a problem with creating the repo.", fg='red')
        sys.exit(1)

    # Return URL
    print "Repository URL is: " + request['ssh_url_to_repo']
    return request['ssh_url_to_repo']


def git_error():
    """
    Print error and instructions on how to configure git
    """
    click.secho("ERROR: Please install git and configure your username and email adress.", fg="red")
    click.echo("You can do this with:")
    click.echo(">sudo apt-get install git")
    click.echo(">git config --global user.name 'FIRSTNAME LASTNAME'")
    click.echo(">git config --global user.email EMAIL@ADRESS.DOMAIN")
    sys.exit(1)


def get_userinfo():
    """
    Tries to read in git user infos.
    """
    # Check whether git is installed
    (dpkg_git, dpkg_err) = subprocess.Popen("dpkg -s git", shell=True, stdout=subprocess.PIPE).communicate()

    # Read out username and email
    (name, name_err) = subprocess.Popen("git config --get user.name", shell=True, stdout=subprocess.PIPE).communicate()
    (email, mail_err) = subprocess.Popen("git config --get user.email", shell=True,
                                         stdout=subprocess.PIPE).communicate()

    # Check wether git is configured
    if dpkg_err is not None or name_err is not None or mail_err is not None:
        git_error()

    user = {'name': name[:-1], 'mail': email[:-1]}
    return user
