from mrt_tools.utilities import changed_base_yaml, update_apt_and_ros_packages
from wstool import multiproject_cli, config_yaml, multiproject_cmd, config as wstool_config
from mrt_tools.Git import Git, test_git_credentials
from catkin_tools.context import Context
from catkin_pkg import packages
import subprocess
import click
import shutil
import yaml
import sys
import os
import re


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
                # TODO Maybe not so smart to change rosinstall file every time -> snapshots!
                self.recreate_index()
            self.cd_root()
        elif not silent:
            click.secho("No catkin workspace root found.", fg="red")
            click.echo("This command must be invoked from within a workspace")
            sys.exit(1)

    def create(self):
        """Initialize new catkin workspace"""
        # Test for existing workspace
        if self.root:
            click.secho("Already inside a catkin workspace. Can't create new.", fg="red")
            sys.exit(1)

        # Test whether directory is empty
        if os.listdir("."):
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

        shutil.copyfile(os.getenv('ROS_ROOT') + "/../catkin/cmake/toplevel.cmake", self.src + "/CMakeLists.txt")


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

    @property
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
        """Add a repository to the workspace
        :param pkg_name: Name of package
        :param url: URL to git repo
        :param update: Run wstool update to pull new commits afterwards?
        """
        ps = config_yaml.PathSpec(pkg_name, "git", url)
        self.wstool_config.add_path_spec(ps)

        if update:
            self.write()
            if url.startswith("https"):
                test_git_credentials()
            self.update_only(pkg_name)
            # Fix for issue #9 to make ros cfg files executable
            subprocess.call("find " + os.path.join(self.src, pkg_name) + " -name \*.cfg -exec chmod 755 {} \;",
                            shell=True)

    def find(self, pkg_name):
        """Test whether package exists
        :param pkg_name:
        """
        return pkg_name in self.get_wstool_package_names()

    def update(self):
        """Update this workspace"""
        if self.contains_https():
            test_git_credentials()
        subprocess.call("wstool update -t {0} -j 10".format(self.src), shell=True)

    def update_only(self, pkgs):
        """Update this workspace
        :param pkgs: Names of packages to be updated
        """
        jobs = 1
        if isinstance(pkgs, list):
            jobs = len(pkgs)
            jobs = 10 if jobs > 10 else jobs
            pkgs = " ".join(pkgs)
        subprocess.call("wstool update -t {0} -j {1} {2}".format(self.src, jobs, pkgs), shell=True)

    def unpushed_repos(self, pkg_name=None):
        """Search for unpushed commits in workspace
        :param pkg_name: Look for only one specified package name
        """
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

    def test_for_changes(self, pkg_name=None, prompt="Are you sure you want to continue?"):
        """ Test workspace for any changes that are not yet pushed to the server
        :param pkg_name:
        :param prompt:
        """
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
        """Writes current workspace configuration to file
        :param filename: Name of file to create
        """
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
        """Returns a dict of all dependencies
        :param pkg_name: Name of package
        :param deep: Recursively retrieve dependencies
        """
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

    def resolve_dependencies(self, git=None, default_yes=None):
        # TODO maybe use rosdep2 package directly
        click.echo("Resolving dependencies...")
        # Test whether ros is sourced
        if "ROS_ROOT" not in os.environ:
            click.secho("ROS_ROOT not set. Run: 'source /opt/ros/$ROS_DISTRO/setup.bash'", fg="red")
            sys.exit(1)

        if changed_base_yaml():
            click.secho("Base YAML file changed, running 'rosdep update'.", fg="green")
            subprocess.call("rosdep update", shell=True)

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
                    self.add(missing_package, url, update=True)
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

        # install missing system dependencies
        if default_yes:
            subprocess.check_call(["rosdep", "install", "--default-yes", "--from-paths", self.src, "--ignore-src"])
        else:
            subprocess.check_call(["rosdep", "install", "--from-paths", self.src, "--ignore-src"])

    def recreate_index(self, write=True):
        """Goes through all directories within the workspace and checks whether the rosinstall file is up to date.
        :param write: Export new index to file
        """
        self.catkin_pkg_names = self.get_catkin_package_names()

        self.wstool_config = wstool_config.Config([], self.src)
        self.cd_src()

        for pkg in self.catkin_pkg_names:
            # Try reading it from git repo
            try:
                with open(pkg + "/.git/config", 'r') as f:
                    git_url = next(line[7:-1] for line in f if line.startswith("\turl"))
                    self.add(pkg, git_url, update=False)
            except (IOError, StopIteration):
                pass

        # Create rosinstall file from config
        if write:
            self.write()

    def contains_https(self):
        for ps in self.wstool_config.get_config_elements():
            if ps.get_path_spec().get_uri().startswith("https"):
                return True
        return False
