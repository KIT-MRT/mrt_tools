#!/usr/bin/python
from wstool import config_yaml, multiproject_cli
from requests.packages import urllib3
import subprocess
import gitlab
import click
import sys
import os

urllib3.disable_warnings()

# Ugly test to test for bash completion mode
try:
    os.environ['COMP_WORDS']
    is_bashcompletion = True
except KeyError:
    is_bashcompletion = False

# Default settings
default_token_path = "~/.mrtgitlab/.token"
default_ssh_path = "~/.ssh"
default_repo_cache = "~/.mrtgitlab/repo_cache"
default_repo_cache_time = 60 # in seconds
default_host = "https://gitlab.mrt.uni-karlsruhe.de"


class Git:
    def __init__(self, token=None, host=default_host):
        # Host URL
        self.host = host
        self.token = token
        self.server = None
        self.ssh_key = None

        if is_bashcompletion:
            self.connect()
        else:
            self.test_and_connect()

    def test_and_connect(self):
        # Token
        if self.token is None:
            self.token = Token()
        elif isinstance(self.token, str):
            self.token = Token(path=self.token)
        elif isinstance(self.token, Token):
            pass
        else:
            click.secho("Can't create a token from " + str(type(self.token)), fg="red")

        # Test whether git is configured
        get_userinfo()

        # Connect
        self.connect()

        # Test ssh key
        if not self.check_ssh_key():
            # SSH Key not on server yet. Ask user
            click.echo("No ssh key match found. Which ssh key should we use?")
            local_keys = get_local_ssh_keys()
            user_choice = get_user_choice([key.name for key in local_keys], default="Create new key.")
            if user_choice is None:
                self.ssh_key = SSHkey()
                self.ssh_key.create()
            else:
                self.ssh_key = local_keys[user_choice]
            self.upload_ssh_key()

    def connect(self):
        """Connects to the server"""
        self.server = gitlab.Gitlab(self.host, token=self.token.token)

    def check_ssh_key(self):
        """Test for the presence and functionality of a ssh-key."""
        local_keys = get_local_ssh_keys()
        remote_keys = self.server.getsshkeys()
        if [key for key in local_keys if key.public_key in [r["key"] for r in remote_keys]]:
            return True
        else:
            return False

    def upload_ssh_key(self):
        """Add ssh key to gitlab user account"""
        click.echo("Uploading key " + self.ssh_key.name)
        self.server.addsshkey(self.ssh_key.name, self.ssh_key.public_key)

    def get_namespaces(self):
        """Returns a list of all namespaces in Gitlab"""

        click.echo("Retrieving namespaces...")
        namespaces = {project['namespace']['name']: project['namespace']['id'] for project in self.get_repos()}
        user_name = self.server.currentuser()['username']
        if user_name not in namespaces.keys():
            namespaces[user_name] = 0  # The default user namespace_id will be created with first user project
        return namespaces

    def get_repos(self):
        """Returns a list of all repositories in Gitlab"""

        return list(self.server.getall(self.server.getprojects, per_page=100))

    def find_repo(self, pkg_name, ns=None):
        """Search for a repository within gitlab."""

        click.secho("Search for package " + pkg_name, fg='red')
        results = self.server.searchproject(pkg_name)

        if ns is not None:
            try:
                return next(
                    x["ssh_url_to_repo"] for x in results if x["path_with_namespace"] == str(ns) + "/" + pkg_name)
            except StopIteration:
                return None

        exact_hits = [res for res in results if res["name"] == pkg_name]
        count = len(exact_hits)

        if count is 0:
            # None found
            click.secho("Package " + pkg_name + " could not be found.", fg='red')
            return ""
        if count is 1:
            # Only one found
            user_choice = 0
        else:
            # Multiple found
            print "More than one repo with \"" + str(pkg_name) + "\" found. Please choose:"
            user_choice = get_user_choice([item["path_with_namespace"] for item in exact_hits])

        ssh_url = exact_hits[user_choice]['ssh_url_to_repo']
        click.secho("Found " + exact_hits[user_choice]['path_with_namespace'], fg='green')

        return ssh_url

    def clone_pkg(self, pkg_name):
        """Search and clone a repository."""

        # Check whether package exists already
        f_null = open(os.devnull, 'w')
        wstool_process = subprocess.Popen(['wstool', 'info', pkg_name, "-t", "src"],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        wstool_output, wstool_err = wstool_process.communicate()

        if wstool_err:
            ssh_url = self.find_repo(pkg_name)
            if ssh_url is None:
                return False

            # add specified git repository to rosinstall
            wsconfig = multiproject_cli.multiproject_cmd.get_config("src", config_filename=".rosinstall")
            ps = config_yaml.PathSpec(pkg_name, "git", ssh_url)
            wsconfig.add_path_spec(ps)
            config_yaml.generate_config_yaml(wsconfig, ".rosinstall", "")
        else:
            click.echo("Package " + pkg_name + " exists already.")

        self.check_ssh_key()  # Shouldn't be needed, but gives error if not here.
        subprocess.call(["wstool", "update", pkg_name, "-t", "src"], stdout=f_null)
        return True

    def create_repo(self, pkg_name):
        """
        This function creates a new repository on the gitlab server.
        It lets the user choose the namespace and tests whether the repo exists already.
        """
        # Dialog to choose namespace
        click.echo("Available namespaces in gitlab, please select one for your new project:")
        namespaces = self.get_namespaces()
        user_choice = get_user_choice(namespaces)
        click.echo("Using namespace '" + namespaces.keys()[int(user_choice)] + "'")
        ns_id = namespaces.values()[int(user_choice)]

        # Check whether repo exists
        ssh_url = self.find_repo(pkg_name, namespaces.keys()[int(user_choice)])

        if ssh_url is not None:
            click.secho("    ERROR Repo exist already: " + ssh_url, fg='red')
            sys.exit(1)

        # Create repo
        if ns_id == 0:  # Create new user namespace
            request = self.server.createproject(pkg_name)
        else:
            request = self.server.createproject(pkg_name, namespace_id=ns_id)
        if not request:
            click.secho("There was a problem with creating the repo.", fg='red')
            sys.exit(1)

        # Return URL
        click.echo("Repository URL is: " + request['ssh_url_to_repo'])
        return request['ssh_url_to_repo']


class SSHkey:
    """The ssh-key is an authentication key for communicating with the gitlab server through the git cli-tool."""

    def __init__(self, name="mrtgitlab", key="", dir_path=default_ssh_path):
        self.name = name
        self.secret_key = ""
        self.dir_path = os.path.expanduser(dir_path)
        self.path = self.dir_path + "/" + self.name
        self.public_key = key

    def load(self):
        """Load from file"""
        try:
            # Secret key
            with open(self.path, 'r') as f:
                self.secret_key = f.read().splitlines()
                while type(self.secret_key) is list:
                    self.secret_key = self.secret_key[0]

            # Public key
            with open(self.path + ".pub", 'r') as f:
                self.public_key = f.read().splitlines()
                while type(self.public_key) is list:
                    self.public_key = self.public_key[0]

            return True
        except IOError:
            return False

    def write(self):
        """Write key to file"""
        from os import chmod

        # Choose key file
        while os.path.exists(self.path):
            key_file = click.prompt("Please enter a new key name: ")
            self.path = os.path.expanduser(self.dir_path + key_file)

        # Write keys
        if self.secret_key:
            with open(self.path, 'w') as f:
                chmod(self.path, 0600)
                f.write(self.secret_key)
        if self.public_key:
            with open(self.path + ".pub", 'w') as f:
                chmod(self.path, 0600)
                f.write(self.public_key)

        click.echo("Wrote key to " + self.path + "(.pub)")

    def create(self):
        """Create new SSH key"""
        from Crypto.PublicKey import RSA

        # Generate key
        click.echo("Generating new SSH Key")
        key = RSA.generate(2048)
        self.secret_key = key.exportKey('PEM')
        self.public_key = key.publickey().exportKey('OpenSSH')
        self.write()


class Token:
    """
    The token file is an authentication key for communicating with the gitlab server through the python API.
    """

    def __init__(self, path=default_token_path, allow_creation=True):
        self.path = os.path.expanduser(path)
        self.token = self.load(self.path)
        if not self and allow_creation:
            self.create()

    def __nonzero__(self):
        return self.token != ""

    @staticmethod
    def load(path):
        """
        Read in the token from a specified path
        """
        try:
            return os.read(os.open(path, 0), 20)
        except OSError:
            return ""

    def create(self):
        """
        Create a new token from Gitlab user name and password.
        Normally this function has to be called only once.
        From then on, the persistent token file is used to communicate with the server.
        """
        click.echo("No existing gitlab token file found. Creating new one...")
        username = click.prompt("Gitlab user name")
        password = click.prompt("Gitlab password", hide_input=True)

        tmp_git_obj = gitlab.Gitlab(default_host)
        tmp_git_obj.login(username, password)
        gitlab_user = tmp_git_obj.currentuser()

        self.token = gitlab_user['private_token']
        self.write()

    def write(self):
        """Write to file"""
        if not os.path.exists(os.path.dirname(self.path)):
            os.makedirs(os.path.dirname(self.path))

        with open(self.path, 'w') as f:
            f.write(self.token)

        click.echo("Token written to: " + self.path)


def get_local_ssh_keys(path=default_ssh_path):
    path = os.path.expanduser(path)
    keys = []
    for filename in os.listdir(path):
        key = SSHkey(name=filename, dir_path=path)
        if key.load():
            keys.append(key)
    return keys


def export_repo_names():
    """
    Read repo list from server and write it into caching file.
    """
    # Because we are calling this during autocompletion, we don't wont any errors.
    # -> Just exit when something is not ok.
    try:
        # Connect
        token = Token(path=default_token_path, allow_creation=False)
        git = Git(token=token)
        repo_dicts = git.get_repos()
    except:
        # In case the connection didn't succeed, the file is going to be flushed.
        repo_dicts = []

    with open(os.path.expanduser(default_repo_cache), "w") as f:
        for r in repo_dicts:
            f.write(r["name"] + ",")


def import_repo_names():
    """
    Try to read in repos from cached file.
    If file is older than default_repo_cache_time seconds, a new list is retrieved from server.
    """
    import time

    now = time.time()
    try:
        # Read in last modification time
        last_modification = os.path.getmtime(os.path.expanduser(default_repo_cache))
    except OSError:
        # Set modification time to 2 * default_repo_cache_time ago
        last_modification = now - 2 * default_repo_cache_time

    # Read new repo list from server if delta_t > 1 Minute
    if (now - last_modification) > default_repo_cache_time:
        export_repo_names()

    # Read in repo list from cache
    with open(os.path.expanduser(default_repo_cache), "r") as f:
        repos = f.read()
    return repos.split(",")[:-1]


def get_userinfo():
    """Read in git user infos."""

    # Check whether git is installed
    (dpkg_git, dpkg_err) = subprocess.Popen("dpkg -s git", shell=True, stdout=subprocess.PIPE).communicate()

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


def get_user_choice(items, default=None):
    # Print choices
    valid_choices = []
    for index, item in enumerate(items):
        valid_choices.append(index)
        click.echo("(" + str(valid_choices[-1]) + ") " + item)
    valid_choices = range(0, len(items))

    # Add default choice
    if default:
        valid_choices.append(len(items))
        click.echo("(" + str(valid_choices[-1]) + ") " + str(default))
    while True:
        user_choice = click.prompt('Please enter a number [0-' + str(valid_choices[-1]) + ']', type=int)
        if user_choice in valid_choices:
            if default is not None and user_choice is valid_choices[-1]:
                # Return None if default was chosen
                return None
            else:
                return user_choice
