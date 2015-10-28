from wstool import multiproject_cli, config_yaml, multiproject_cmd, config as wstool_config
from requests.exceptions import ConnectionError
from catkin_tools.context import Context
from requests.packages import urllib3
from mrt_tools.utilities import *
from mrt_tools.settings import *
from Crypto.PublicKey import RSA
from catkin_pkg import packages
from builtins import object
from builtins import next
from builtins import str
import subprocess
import gitlab
import shutil
import pydot
import click
import yaml
import sys
import os
import re

urllib3.disable_warnings()

# Ugly test to test for bash completion mode
try:
    os.environ['COMP_WORDS']
    is_bashcompletion = True
except KeyError:
    is_bashcompletion = False


class Git(object):
    def __init__(self, token=None, host=default_host, use_ssh=False):
        # Host URL
        self.host = host
        self.token = token
        self.server = None
        self.ssh_key = None
        self.use_ssh = use_ssh

        if is_bashcompletion:
            self.connect()
        else:
            self.test_and_connect()

    def get_url_string(self):
        if self.use_ssh:
            return "ssh_url_to_repo"
        else:
            return "http_url_to_repo"

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

    def connect(self):
        """Connects to the server"""
        try:
            self.server = gitlab.Gitlab(self.host, token=self.token.token)
        except gitlab.exceptions.HttpError:
            click.secho("There was a problem logging in to gitlab. Did you use your correct credentials?", fg="red")
            sys.exit(1)
        except ValueError:
            click.secho("No connection to server. Did you connect to VPN?", fg="red")
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
            raise Exception("There was a problem with gitlab...")
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
        """Search for a repository within gitlab."""
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
            choice = get_user_choice([item["path_with_namespace"] for item in matching_repos],
                                     prompt="More than one repo with \"" + str(
                                         pkg_name) + "\" found. Please choose")

        url = matching_repos[choice][self.get_url_string()]
        click.secho("Found " + matching_repos[choice]['path_with_namespace'], fg='green')

        return url

    def create_repo(self, pkg_name):
        """
        This function creates a new repository on the gitlab server.
        It lets the user choose the namespace and tests whether the repo exists already.
        """
        # Dialog to choose namespace
        click.echo("Available namespaces in gitlab, please select one for your new project:")
        namespaces = self.get_namespaces()
        choice_index = get_user_choice(namespaces.keys())
        click.echo("Using namespace '" + list(namespaces.keys())[int(choice_index)] + "'")
        ns_id = list(namespaces.values())[int(choice_index)]

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
        click.echo("Repository URL is: " + response[self.url_string])
        return response[self.url_string]

    @staticmethod
    def get_local_ssh_keys(path=default_ssh_path):
        path = os.path.expanduser(path)
        keys = []
        try:
            for filename in os.listdir(path):
                key = SSHkey(name=filename, dir_path=path)
                if key.load():
                    keys.append(key)
        except OSError:
            pass
        return keys


class SSHkey(object):
    """The ssh-key is an authentication key for communicating with the gitlab server through the git cli-tool."""

    def __init__(self, name=default_ssh_key_name, key="", dir_path=default_ssh_path):
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


class Token(object):
    """
    The token file is an authentication key for communicating with the gitlab server through the python API.
    """

    def __init__(self, path=default_token_path, allow_creation=True):
        self.path = os.path.expanduser(path)
        self.token = self.load(self.path)
        if not self and allow_creation:
            self.create()

    def __bool__(self):
        return self.token != ""

    @staticmethod
    def load(path):
        """
        Read in the token from a specified path
        """
        try:
            return os.read(os.open(path, 0), 20)
        except (IOError, OSError):
            return ""

    def create(self):
        """
        Create a new token from Gitlab user name and password.
        Normally this function has to be called only once.
        From then on, the persistent token file is used to communicate with the server.
        """
        click.echo("No existing gitlab token file found. Creating new one...")

        tmp_git_obj = gitlab.Gitlab(default_host)
        gitlab_user = None
        while gitlab_user is None:
            try:
                username = click.prompt("Gitlab user name")
                password = click.prompt("Gitlab password", hide_input=True)
                tmp_git_obj.login(username, password)
                gitlab_user = tmp_git_obj.currentuser()
            except gitlab.exceptions.HttpError:
                click.secho("There was a problem logging in to gitlab. Did you use your correct credentials?", fg="red")
            except ValueError:
                click.secho("No connection to server. Did you connect to VPN?", fg="red")
            except ConnectionError:
                click.secho("No connection to server. Are you connected to the internet?", fg="red")

        self.token = gitlab_user['private_token']
        self.write()

    def write(self):
        """Write to file"""
        if not os.path.exists(os.path.dirname(self.path)):
            os.makedirs(os.path.dirname(self.path))

        with open(self.path, 'w') as f:
            f.write(self.token)

        click.echo("Token written to: " + self.path)


class Workspace(object):
    """Object representing a catkin workspace"""

    def __init__(self, silent=False):
        self.org_dir = os.getcwd()
        self.root = self.get_root()
        self.updated_apt = False
        self.wstool_config = None
        self.wstool_pks = None
        self.wstool_pkg_names = None
        self.catkin_config = None
        self.catkin_pkgs = None
        self.catkin_pkg_names = None

        if self.root is not None:
            self.src = self.root + "/src/"
            self.load()
            self.catkin_pkgs = self.get_catkin_packages()
            self.catkin_pkg_names = self.get_catkin_package_names()
            self.wstool_pkg_names = self.get_wstool_package_names()
            if not set(self.catkin_pkg_names).issubset(set(self.wstool_pkg_names)):
                # click.secho("INFO: wstool and catkin found different packages! Maybe you should run 'ws fix "
                #             "url_in_package_xml'", fg='yellow')
                self.recreate_index()
            self.cd_root()
        elif not silent:
            raise Exception("No catkin workspace root found.")

    def create(self):
        """Initialize new catkin workspace"""
        # Test for existing workspace
        if self.root:
            click.secho("Already inside a catkin workspace. Can't create new.", fg="red")
            sys.exit(1)

        # Test whether directory is empty
        if os.listdir("."):
            click.echo(os.listdir("."))
            if not click.confirm("The repository folder is not empty. Would you like to continue?"):
                sys.exit(0)

        click.secho("Creating workspace", fg="green")
        self.root = os.getcwd()
        os.mkdir("src")
        subprocess.call("catkin init", shell=True)
        os.chdir("src")
        subprocess.call("wstool init", shell=True)
        subprocess.call("catkin build", shell=True)

        self.src = self.root + "/src/"
        self.load()
        self.catkin_pkgs = self.get_catkin_packages()
        catkin_pkgs = set(self.get_catkin_package_names())
        wstool_pks = set(self.get_wstool_package_names())
        if not catkin_pkgs.issubset(wstool_pks):
            click.echo("wstool and catkin found different packages!")
            self.recreate_index()
        self.cd_root()

    def clean(self):
        """Delete everything in current workspace."""
        self.test_for_changes()
        self.cd_root()
        click.secho("WARNING:", fg="red")
        click.confirm("Delete everything within " + self.root, abort=True)
        for f in os.listdir(self.root):
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)

    def exists(self):
        """Test whether workspace exists"""
        return self.get_root() is not None

    @staticmethod
    def get_root():
        """Find the root directory of a workspace, starting from '.' """
        org_dir = os.getcwd()
        current_dir = org_dir
        while current_dir != "/" and current_dir != "":
            if ".catkin_tools" in os.listdir(current_dir):
                break
            current_dir = os.path.dirname(current_dir)

        os.chdir(org_dir)
        if current_dir == "/" or current_dir == "":
            return None
        else:
            return current_dir

    def cd_root(self):
        """Changes directory to workspace root"""
        os.chdir(self.root)

    def cd_src(self):
        """Changes directory to workspace src folder"""
        os.chdir(self.src)

    def load(self):
        """Read in .rosinstall from workspace"""
        self.wstool_config = multiproject_cli.multiproject_cmd.get_config(self.src, config_filename=".rosinstall")
        self.catkin_config = Context.load()
        self.catkin_pkgs = self.get_catkin_packages()

    def write(self):
        """Write to .rosinstall in workspace"""
        config_yaml.generate_config_yaml(self.wstool_config, self.src + ".rosinstall", "")

    def add(self, pkg_name, url, update=True):
        """Add a repository to the workspace"""
        ps = config_yaml.PathSpec(pkg_name, "git", url)
        self.wstool_config.add_path_spec(ps)
        if update:
            self.write()
            self.update_only(pkg_name)

    def find(self, pkg_name):
        """Test whether package exists"""
        return pkg_name in self.get_wstool_package_names()

    def update(self):
        """Update this workspace"""
        subprocess.call("wstool update -t {0} -j 10".format(self.src), shell=True)

    def update_only(self, pkgs):
        """Update this workspace"""
        jobs = 1
        if isinstance(pkgs, list):
            jobs = len(pkgs)
            jobs = 10 if jobs > 10 else jobs
            pkgs = " ".join(pkgs)
        subprocess.call("wstool update -t {0} -j {1} {2}".format(self.src, jobs, pkgs), shell=True)

    def unpushed_repos(self, pkg_name=None):
        """Search for unpushed commits in workspace"""
        # Read in again
        self.catkin_pkg_names = self.get_catkin_package_names()
        self.wstool_pkg_names = self.get_wstool_package_names()
        unpushed_repos = []
        for pkg in self.wstool_pkg_names:
            if pkg not in self.catkin_pkg_names:
                continue

            # If we are only looking for one specific pkg:
            if pkg_name and pkg != pkg_name:
                continue

            try:
                os.chdir(self.src + pkg)
                git_process = subprocess.Popen("git log --branches --not --remotes", shell=True, stdout=subprocess.PIPE)
                result = git_process.communicate()

                if result[0] != "":
                    click.secho("Unpushed commits in repo '" + pkg + "'", fg="yellow")
                    subprocess.call("git log --branches --not --remotes --oneline", shell=True)
                    unpushed_repos.append(pkg)
            except OSError:  # Directory does not exist (repo not cloned yet)
                pass

        os.chdir(self.org_dir)
        return unpushed_repos

    def fetch(self, pkg_name=None):
        """Perform a git fetch in every repo"""
        # Read in again
        self.catkin_pkg_names = self.get_catkin_package_names()
        self.wstool_pkg_names = self.get_wstool_package_names()
        for pkg in self.wstool_pkg_names:
            # If we are only looking for one specific pkg:
            if pkg_name and pkg != pkg_name:
                continue

            try:
                os.chdir(self.src + pkg)
                click.echo("Fetching in {0}...".format(pkg))
                subprocess.call("git fetch --quiet", shell=True)
            except OSError:  # Directory does not exist (repo not cloned yet)
                pass
        os.chdir(self.org_dir)

    def test_for_changes(self, pkg_name=None, prompt="Are you sure you want to continue?"):
        """ Test workspace for any changes that are not yet pushed to the server """
        # Parse git status messages
        statuslist = multiproject_cmd.cmd_status(self.wstool_config, untracked=True)
        statuslist = [{k["entry"].get_local_name(): k["status"]} for k in statuslist if k["status"] != ""]

        if pkg_name:
            statuslist = [line for line in statuslist if pkg_name in line]

        # Check for unpushed commits
        unpushed_repos = self.unpushed_repos(pkg_name)

        # Prompt user if changes detected
        if len(unpushed_repos) > 0 or len(statuslist) > 0:
            if len(statuslist) > 0:  # Unpushed repos where asked already
                click.secho("\nYou have the following uncommited changes:", fg="red")
                for e in statuslist:
                    click.echo(list(e.keys())[0])
                    click.echo(list(e.values())[0])

            click.confirm(prompt, abort=True)

    def snapshot(self, filename):
        """Writes current workspace configuration to file"""
        source_aggregate = multiproject_cmd.cmd_snapshot(self.wstool_config)
        with open(filename, 'w') as f:
            f.writelines(yaml.safe_dump(source_aggregate))

    def get_catkin_packages(self):
        """Returns a dict of all catkin packages"""
        return packages.find_packages(self.src)

    def get_catkin_package_names(self):
        """Returns a list of all catkin packages in ws"""
        self.catkin_pkgs = self.get_catkin_packages()
        return [k for k, v in list(self.catkin_pkgs.items())]

    def get_wstool_packages(self):
        """Returns a list of all wstool packages in ws"""
        return self.wstool_config.get_config_elements()

    def get_wstool_package_names(self):
        """Returns a list of all wstool packages in ws"""
        self.wstool_pks = self.get_wstool_packages()
        return [pkg.get_local_name() for pkg in self.wstool_pks]

    def get_dependencies(self, pkg_name, deep=False):
        """Returns a dict of all dependencies"""
        if pkg_name in list(self.catkin_pkgs.keys()):
            deps = [d.name for d in self.catkin_pkgs[pkg_name].build_depends]
            if len(deps) > 0:
                if deep:
                    deps = [self.get_dependencies(d, self.catkin_pkgs) for d in deps]
                return {pkg_name: deps}
            else:
                return {pkg_name: []}
        else:
            return pkg_name

    def get_all_dependencies(self):
        """Returns a flat list of dependencies"""
        return set(
            [build_depend.name for catkin_pkg in list(self.catkin_pkgs.values()) for build_depend in
             catkin_pkg.build_depends])

    def resolve_dependencies(self, git=None):
        # TODO maybe use rosdep2 package directly
        click.echo("Resolving dependencies...")
        # Test whether ros is sourced
        if "LD_LIBRARY_PATH" not in os.environ or "/opt/ros" not in os.environ["LD_LIBRARY_PATH"]:
            click.secho("ROS_ROOT not set. Source /opt/ros/<dist>/setup.bash", fg="red")
            raise Exception("ROS_ROOT not set.")

        if not git:
            git = Git()

        regex_rosdep_resolve = re.compile("ERROR\[([^\]]*)\]: Cannot locate rosdep definition for \[([^\]]*)\]")

        while True:
            rosdep_process = subprocess.Popen(['rosdep', 'check', '--from-paths', self.src, '--ignore-src'],
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            rosdep_output, rosdep_err = rosdep_process.communicate()

            if not rosdep_err:
                break

            missing_packages = dict()
            for match in regex_rosdep_resolve.finditer(rosdep_err):
                missing_packages[match.group(2)] = match.group(1)

            if not missing_packages:
                click.echo(rosdep_output)
                click.echo(rosdep_err)
                sys.exit(1)

            gitlab_packages = []
            for missing_package, package_dep_specified in missing_packages.items():
                # Search for package in gitlab
                url = git.find_repo(missing_package)
                if url:
                    self.add(missing_package, url, update=False)
                    gitlab_packages.append(missing_package)
                else:
                    # no Gitlab project found
                    if not self.updated_apt:
                        # first not found package. Update apt-get and ros.
                        click.secho("Updating mrt apt-get and rosdep and resolve again. This might take a while ...",
                                    fg='green')
                        update_apt_and_ros_packages()
                        self.updated_apt = True
                        break
                    else:
                        click.secho(
                            "Package {0} (requested from: {1}) could not be found.".format(missing_package,
                                                                                           package_dep_specified),
                            fg='red')
                        sys.exit(1)
            # Load new gitlab packages
            self.write()
            self.update_only(gitlab_packages)

        # install missing system dependencies
        subprocess.check_call(["rosdep", "install", "--from-paths", self.src, "--ignore-src"])

    def recreate_index(self, write=True):
        """Goes through all directories within the workspace and checks whether the rosinstall file is up to date."""
        self.catkin_pkg_names = self.get_catkin_package_names()

        self.wstool_config = wstool_config.Config([], self.src)
        self.cd_src()

        for pkg in self.catkin_pkg_names:
            # Try reading it from git repo
            try:
                with open(pkg + "/.git/config", 'r') as f:
                    git_ssh_url = next(line[7:-1] for line in f if line.startswith("\turl"))
                    self.add(pkg, git_ssh_url, update=False)
            except (IOError, StopIteration):
                pass

        # Create rosinstall file from config
        if write:
            self.write()


class Digraph(object):
    def __init__(self, deps):
        # create a graph object
        self.graph = pydot.Dot(graph_type='digraph')
        self.nodes = None
        # add nodes and edges to the root node
        for dep in deps:
            self.add_nodes(dep)

    def create_node(self, name, isleaf=False):
        if isleaf:
            node = pydot.Node(name, style="filled", fillcolor="red")
        else:
            node = pydot.Node(name, style="filled", fillcolor="green")
        self.graph.add_node(node)
        return node

    def get_node(self, name, isleaf=False):
        """creates or returns (if the node already exists) the node"""

        # check all of the graph nodes
        for node in self.graph.get_nodes():
            if name == node.get_name():
                return node

        return self.create_node(name, isleaf=isleaf)

    def add_nodes(self, deps_dict):
        """Add several nodes"""
        root_node = self.get_node(list(deps_dict.keys())[0])

        for v in list(deps_dict.values())[0]:

            # if the list element is not a dict
            if type(v) != dict:
                node = self.get_node(v, isleaf=True)
                self.add_edge(root_node, node)

            # if the element is a dict, call recursion
            else:
                node = self.get_node(list(v.keys())[0], isleaf=False)
                self.add_edge(root_node, node)
                self.add_nodes(v)

    def add_edge(self, a, b):
        """checks if the edge already exists, if not, creates one from a2b"""

        for edge_obj in self.graph.get_edge_list():
            if a.get_name() in edge_obj.obj_dict["points"] and \
                            b.get_name() in edge_obj.obj_dict["points"]:
                break
        else:
            # such an edge doesn't exist. create it
            self.graph.add_edge(pydot.Edge(a, b))

    def plot(self, pkg_name, show=True):
        """plot a directed graph with one root node"""
        if not os.path.exists("pics"):
            os.mkdir("pics")
        filename = os.path.join(os.getcwd(), "pics/deps_{0}.png".format(pkg_name))
        self.graph.write_png(filename)
        if show:
            subprocess.call(["xdg-open", filename])
        click.echo("Image written to: " + os.getcwd() + "/" + filename)


def import_repo_names():
    """
    Try to read in repos from cached file.
    If file is older than default_repo_cache_time seconds, a new list is retrieved from server.
    """
    try:
        # Read in repo list from cache
        with open(os.path.expanduser(default_repo_cache), "r") as f:
            repos = f.read()
        return repos.split(",")[:-1]
    except OSError:
        return []
