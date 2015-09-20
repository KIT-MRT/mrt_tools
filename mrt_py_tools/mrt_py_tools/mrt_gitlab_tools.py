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
cached_repos_file = token_dir + "/repo_cache"

git = None


def connect():
    """
    Connects to the server
    :return: git object
    """
    global git

    # Test whether git is configured
    get_userinfo()

    check_token_file()

    # Connect
    token = os.read(os.open(token_file, 0), 20)
    git_obj = gitlab.Gitlab(host, token=token)

    check_sshkey()

    return git_obj


def check_token_file():
    """
    This function searches for a private token file and creates it if not found.
    The token file is an authentication key for communicating with the gitlab server through the python API.
    """
    # Check for token file
    if not os.path.isfile(token_file):
        click.echo("No gitlab token file found. Creating new one...")
        create_gitlab_token_file()


def create_gitlab_token_file():
    """
    This function asks for the Gitlab user name and password, in order to create a local private token file.
    Normally this function has to be called only once.
    From then on, the token file is used to communicate with the server.
    """
    username = raw_input("Gitlab user name: ")
    password = getpass.getpass()
    tmp_git_obj = gitlab.Gitlab(host)
    tmp_git_obj.login(username, password)
    gitlab_user = tmp_git_obj.currentuser()
    token = gitlab_user['private_token']

    # Write to file
    if not os.path.exists(token_dir):
        os.mkdir(token_dir)

    if not os.path.isfile(token_file):
        os.mknod(token_file)
    os.write(os.open(token_file, 1), token)

    click.echo("Token file created at: " + token_file)


def check_sshkey():
    """
    This function tests for the presence and functionality of a ssh-key.
    The ssh-key is an authentication key for communicating with the gitlab server through the git cli-tool.
    """
    global git
    remote_keys = git.getsshkeys()
    local_keys = get_local_ssh_keys()
    if [key for key in local_keys if key["key"] in [r["key"] for r in remote_keys]]:
        return True

    # SSH Key not on server yet. Ask user
    click.echo("No ssh key match found. Which ssh key should we use?")
    for index, item in enumerate(local_keys):
        print "(" + str(index) + ") " + "Upload key '" + item["name"] + "'"
    print "(" + str(index + 1) + ") " + "Create new key"
    valid_choices = range(0, len(local_keys) + 1)
    while True:
        user_choice = click.prompt('Please enter a number [0-' + str(len(local_keys)) + ']', type=int)
        if user_choice in valid_choices:
            break
    if user_choice == len(local_keys):
        new_key = create_new_sshkey()
        add_ssh_key(new_key)
    else:
        add_ssh_key(local_keys[user_choice])


def get_local_ssh_keys():
    keys = []
    for filename in os.listdir(os.path.expanduser("~/.ssh")):
        if filename.endswith(".pub"):
            with open(os.path.expanduser("~/.ssh/" + filename), 'r') as f:
                key = f.read().splitlines()
                while type(key) is list:
                    key = key[0]
                keys.append({'name': filename, 'key': key, 'path': os.path.expanduser("~/.ssh/" + filename)})
    return keys


def create_new_sshkey():
    from os import chmod
    from Crypto.PublicKey import RSA

    # Generate key
    click.echo("Generating new SSH Key")
    key = RSA.generate(2048)
    # Choose key file
    key_file = os.path.expanduser("~/.ssh/mrtgitlab")
    while os.path.exists(key_file):
        key_file = click.prompt("Please enter a new key name: ")
        key_file = os.path.expanduser("~/.ssh/" + key_file)

    # Write key to file
    with open(key_file, 'w') as content_file:
        chmod(key_file, 0600)
        content_file.write(key.exportKey('PEM'))
    pubkey = key.publickey()
    with open(key_file + ".pub", 'w') as content_file:
        content_file.write(pubkey.exportKey('OpenSSH'))
    click.echo("Wrote key to " + key_file + "(.pub)")

    return {"name": os.path.basename(key_file),
            "key": pubkey.exportKey('OpenSSH'),
            "path": key_file}


def add_ssh_key(key):
    global git
    click.echo("Uploading key " + key["name"])
    git.addsshkey(key["name"], key["key"])


def get_namespaces():
    """
    This function returns a list of all namespaces in Gitlab
    :return: List of namespace names
    """
    global git
    if git is None:
        # Create connection to git
        git = connect()

    # Check namespaces
    click.echo("Retrieving namespaces...")
    namespaces = {project['namespace']['name']: project['namespace']['id'] for project in get_repos()}
    if git.currentuser()['username'] not in namespaces.keys():
        namespaces[
            git.currentuser()['username']] = 0  # The default user namespace_id will be created with first userproject
    return namespaces


def get_repos():
    """
    This function returns a list of all repositories in Gitlab
    :return: List of repositories names
    """
    global git
    if git is None:
        # Create connection to git
        git = connect()

    # Get all repos
    return list(git.getall(git.getprojects, per_page=100))


def export_repo_names():
    """
    Read repo list from server and write it into caching file.
    """
    # Because we are calling this during autocompletion, we don't wont any errors.
    # -> Just exit when something is not ok.
    global git
    if git is None:
        try:
            # Connect
            token = os.read(os.open(token_file, 0), 20)
            git = gitlab.Gitlab(host, token=token)
        except:
            sys.exit(1)

    repo_dicts = get_repos()
    with open(cached_repos_file, "w") as f:
        for r in repo_dicts:
            f.write(r["name"] + ",")

    # Delete git again, as we are not sure whether all tests are met.
    git = None


def import_repo_names():
    """
    Try to read in repos from cached file. If file is older than 60 seconds, a new list is retrieved from server.
    """
    import time

    now = time.time()
    try:
        # Read in last modification time
        last_modification = os.path.getmtime(cached_repos_file)
    except OSError:
        # Set modification time to 2 Minutes ago
        last_modification = now - 2 * 60

    # Read new repo list from server if delta_t > 1 Minute
    if (now - last_modification) > 60:
        export_repo_names()

    # Read in repo list from cache
    with open(cached_repos_file, "r") as f:
        repos = f.read()
    return repos.split(",")[:-1]


def find_repo(pkg_name, ns=None):
    """
    Searches for a repository within gitlab.
    If repositories in different namespaces are found, the user is asked to select one.
    :param pkg_name: Repo to search for
    :param ns: Namespace to search in
    :return: SSH URL of repository
    """
    global git
    if git is None:
        # Create connection to git
        git = connect()

    # Search for repo
    click.secho("Search for package " + pkg_name, fg='red')
    results = git.searchproject(pkg_name)

    if ns is not None:
        try:
            return next(x["ssh_url_to_repo"] for x in results if x["path_with_namespace"] == str(ns) + "/" + pkg_name)
        except StopIteration:
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
    global git
    if git is None:
        # Create connection to git
        git = connect()

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
        check_sshkey()  # Shouldn't be needed, but gives error if not here.

    subprocess.call(["wstool", "update", pkg_name, "-t", "src"], stdout=f_null)
    return True


def create_repo(pkg_name):
    """
    This function creates a new repository on the gitlab server.
    It lets the user choose the namespace and tests whether the repo exists already.
    """
    global git
    if git is None:
        # Create connection to git
        git = connect()

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
