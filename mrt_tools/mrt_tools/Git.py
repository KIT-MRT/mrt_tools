from mrt_tools.CredentialManager import get_credentials, get_token, store_credentials
from requests.exceptions import ConnectionError
from requests.packages import urllib3
from mrt_tools.utilities import get_user_choice, get_gituserinfo
from mrt_tools.settings import user_settings
from Crypto.PublicKey import RSA
from builtins import object
from builtins import next
from builtins import str
import subprocess
import gitlab
import click
import sys
import os

# Alternatively install pyopenssl ndg-httpsclient pyasn1
urllib3.disable_warnings()

# Ugly test to test for bash completion mode
try:
    os.environ['COMP_WORDS']
    is_bashcompletion = True
except KeyError:
    is_bashcompletion = False


class Git(object):
    def __init__(self, quiet=False):
        # Host URL
        self.host = user_settings['Gitlab']['HOST_URL']
        self.use_ssh = user_settings['SSH']['USE_SSH']
        self.token = get_token()
        self.server = None
        self.ssh_key = None

        if is_bashcompletion or quiet:
            self.connect(quiet=True)
        else:
            self.test_and_connect()

    def get_url_string(self):
        if self.use_ssh:
            return "ssh_url_to_repo"
        else:
            return "http_url_to_repo"

    def test_and_connect(self):
        # Test whether git is configured
        get_gituserinfo()

        self.connect(quiet=False)

        # Test ssh key
        if self.use_ssh and not self.check_ssh_key():
            # SSH Key not on server yet. Ask user
            local_keys = self.get_local_ssh_keys()
            choice_idx, choice_value = get_user_choice([key.name for key in local_keys],
                                                       extra=["Create new key.", "Use https instead of a ssh key"],
                                                       prompt="No ssh key match found. Which ssh key should we use?")
            if choice_value == "Use https instead of a ssh key":
                self.use_ssh = False
                return
            elif choice_value == "Create new key.":
                self.ssh_key = SSHkey()
                self.ssh_key.create()
            else:
                self.ssh_key = local_keys[choice_idx]
            self.upload_ssh_key()

    def connect(self, quiet=False):
        """Connects to the server"""
        try:
            username, password = get_credentials(quiet=quiet)
            if self.token:
                self.server = gitlab.Gitlab(self.host, token=self.token, auth=(username, password))
            else:
                # Login with username and password
                self.server = gitlab.Gitlab(self.host, auth=(username, password))
                self.server.login(username, password)
                gitlab_user = self.server.currentuser()
                if gitlab_user is None:
                    click.secho("Could not create token. Exiting...", fg="red")
                    sys.exit(1)
                else:
                    self.token = gitlab_user['private_token']
                    click.secho("Created gitlab token: {}".format(self.token), fg="green")
                store_credentials('token', self.token)
        except gitlab.exceptions.HttpError:
            click.secho("There was a problem logging in to gitlab. Did you use your correct credentials?", fg="red")
            sys.exit(1)
        except ConnectionError:
            click.secho("No internet connection. Could not connect to server.", fg="red")
            sys.exit(1)

    def check_ssh_key(self):
        """Test for the presence and functionality of a ssh-key."""
        local_keys = self.get_local_ssh_keys()
        try:
            remote_keys = self.server.getsshkeys()
        except ConnectionError:
            click.secho("Couldn't connect to server. Are you connected to the internet?")
            sys.exit(1)

        if remote_keys is False:
            click.secho("There was a problem with gitlab... Exiting", fg="red")
            sys.exit(1)
        if [key for key in local_keys if key.public_key in [r["key"] for r in remote_keys]]:
            return True
        else:
            return False

    def upload_ssh_key(self):
        """Add ssh key to gitlab user account"""
        click.echo("Uploading key " + self.ssh_key.name)
        self.server.addsshkey(self.ssh_key.name, self.ssh_key.public_key)

    def get_namespaces(self):
        """Returns a dict {name:id} of all namespaces in Gitlab"""
        click.echo("Retrieving namespaces...")
        namespaces = list(self.server.getall(self.server.getgroups, per_page=100))
        namespaces = sorted(namespaces, key=lambda k: k['name'])
        user_name = self.server.currentuser()['username']
        namespace_dict = {ns['name']: ns['id'] for ns in namespaces}
        if user_name not in list(namespace_dict.keys()):
            namespace_dict[user_name] = 0
        return namespace_dict

    def get_repos(self):
        """Returns a list of all repositories in Gitlab"""
        return list(self.server.getall(self.server.getprojects, per_page=100))

    def find_repo(self, pkg_name, ns=None):
        """Search for a repository within gitlab.
        :param ns:  Namespace in which to search
        :param pkg_name: Name of the repo
        """
        click.secho("Search for package " + pkg_name, fg='red')
        # Results is a dict or a list of dicts, depending on how many results were found
        results = self.server.searchproject(pkg_name)

        # If we declared a namespace, there will only be one result with this name in this namespace
        if ns:
            try:
                return next(
                    x[self.get_url_string()] for x in results if x["path_with_namespace"] == str(ns) + "/" + pkg_name)
            except StopIteration:
                return None
        else:
            # The searchproject command will also find the query as a substring in repo names, therefor we have to
            # check again.
            matching_repos = [res for res in results if res["name"] == pkg_name]
            count = len(matching_repos)

        if count is 0:
            # None found
            click.secho("Package " + pkg_name + " could not be found.", fg='red')
            return None
        if count is 1:
            # Only one found
            choice = 0
        else:
            # Multiple found
            choice, _ = get_user_choice([item["path_with_namespace"] for item in matching_repos],
                                        prompt="More than one repo with \"" + str(
                                            pkg_name) + "\" found. Please choose")

        url = matching_repos[choice][self.get_url_string()]
        click.secho("Found " + matching_repos[choice]['path_with_namespace'], fg='green')

        return url

    def create_repo(self, pkg_name):
        """
        This function creates a new repository on the gitlab server.
        It lets the user choose the namespace and tests whether the repo exists already.
        :param pkg_name: Name of the repo to create
        """
        # Dialog to choose namespace
        click.echo("Available namespaces in gitlab, please select one for your new project:")
        namespaces = self.get_namespaces()
        choice_index, choice_value = get_user_choice(namespaces.keys())
        click.echo("Using namespace '" + choice_value + "'")
        ns_id = namespaces[choice_value]

        # Check whether repo exists
        url = self.find_repo(pkg_name, list(namespaces.keys())[int(choice_index)])

        if url is not None:
            click.secho("    ERROR Repo exist already: " + url, fg='red')
            sys.exit(1)

        # Create repo
        if ns_id == 0:  # Create new user namespace
            response = self.server.createproject(pkg_name)
        else:
            response = self.server.createproject(pkg_name, namespace_id=ns_id)
        if not response:
            click.secho("There was a problem with creating the repo.", fg='red')
            sys.exit(1)

        # Return URL
        click.echo("Repository URL is: " + response[self.get_url_string()])
        return response[self.get_url_string()]

    @staticmethod
    def get_local_ssh_keys():
        keys = []
        try:
            for filename in os.listdir(os.path.expanduser("~/.ssh")):
                key = SSHkey(name=filename)
                if key.load():
                    keys.append(key)
        except OSError:
            pass
        return keys


class SSHkey(object):
    """The ssh-key is an authentication key for communicating with the gitlab server through the git cli-tool."""

    def __init__(self, name="mrtgitlab"):
        self.name = name
        self.secret_key = ""
        self.dir_path = os.path.expanduser("~/.ssh")
        self.path = self.dir_path + "/" + self.name
        self.public_key = ""

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
        except (IOError, OSError):
            return False

    def write(self):
        """Write key to file"""
        from os import chmod

        # Choose key file
        while os.path.exists(self.path):
            key_file = click.prompt("Please enter a new key name: ")
            self.path = os.path.expanduser(self.dir_path + key_file)

        # Write keys
        if not os.path.exists(os.path.dirname(self.path)):
            os.makedirs(os.path.dirname(self.path))
        if self.secret_key:
            with open(self.path, 'w') as f:
                chmod(self.path, 0o600)
                f.write(self.secret_key)
        if self.public_key:
            with open(self.path + ".pub", 'w') as f:
                chmod(self.path, 0o600)
                f.write(self.public_key)
        subprocess.call("eval '$(ssh-agent -s)'", shell=True)
        subprocess.call("ssh-add " + self.path, shell=True)
        click.echo("Wrote key to " + self.path + "(.pub)")

    def create(self):
        """Create new SSH key"""
        click.echo("Generating new SSH Key")
        key = RSA.generate(2048)
        self.secret_key = key.exportKey('PEM')
        self.public_key = key.publickey().exportKey('OpenSSH')
        self.write()


def set_git_credentials(username, password):
    url = user_settings['Gitlab']['HOST_URL']
    if url.startswith("https://"):
        host = url[8:]
    elif url.startswith("http://"):
        host = url[7:]
    else:
        host = url
    git_process = subprocess.Popen("git credential-cache store", shell=True, stdin=subprocess.PIPE)
    git_process.communicate(
        input="protocol=https\nhost={}\nusername={}\npassword={}".format(host, username, password))


def test_git_credentials():
    # Test whether git credentials are still stored:
    if user_settings['Gitlab']['USE_GIT_CREDENTIAL_CACHE'] \
            and not os.path.exists(os.path.expanduser("~/.git-credential-cache/socket")):
        username, password = get_credentials()
        set_git_credentials(username, password)
