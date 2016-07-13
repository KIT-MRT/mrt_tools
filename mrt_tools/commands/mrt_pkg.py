import pprint
from collections import defaultdict

from mrt_tools.Workspace import Workspace
from mrt_tools.Digraph import Digraph
from mrt_tools.utilities import *
from mrt_tools.Git import Git

# Autocompletion
try:
    tmp_ws = Workspace(quiet=True)
    suggestions = tmp_ws.get_catkin_package_names()
    repo_list = import_repo_names()
    os.chdir(tmp_ws.org_dir)
except:
    suggestions = []
    repo_list = []

self_dir = get_script_root()


########################################################################################################################
# Package
########################################################################################################################
@click.group()
@click.pass_context
def main(ctx):
    """Package related tasks...
    :param ctx:
    """
    ctx.obj = Workspace()


@main.command(short_help="Clone catkin packages from gitlab.",
              help="This command let's you clone repositories directly into your workspace. Dependencies to other "
                   "packages are automatically resolved. Try out the bashcompletion for the package name.")
@click.argument("pkg_names", type=click.STRING, required=True, nargs=-1, autocompletion=repo_list)
@click.pass_obj
def add(ws, pkg_names):
    """Clone catkin packages from gitlab."""
    """
    This tool searches for, and clones a package from the Gitlab Server into the current workspace.
    Execute this script from within a catkin workspace
    """

    git = Git()

    for pkg_name in pkg_names:

        # Test for package
        if ws.find(pkg_name):
            click.echo("Package {0} already present in workspace config. Run 'mrt wstool update'.".format(pkg_name))
            continue

        # Add package to workspace
        repo = git.find_repo(pkg_name)
        if not repo:
            continue
        url = repo[git.get_url_string()]
        ws.add(pkg_name, url)

    ws.resolve_dependencies(git=git)


@main.command(short_help="Deletes package from workspace.",
              help="This command let's you savely remove a package from the current workspace, by checking for "
                   "uncommited or unpushed changes and removing the directory as well as the .rosinstall config entry.")
@click.argument("pkg_names", type=click.STRING, required=True, nargs=-1, autocompletion=suggestions)
@click.pass_obj
def remove(ws, pkg_names):
    """Delete package from workspace."""
    pkg_list = ws.get_catkin_package_names()
    for pkg_name in pkg_names:
        if pkg_name not in pkg_list:
            click.echo("Package {} does not exist.".format(pkg_name))
            continue
        ws.test_for_changes(pkg_name)
        ws.cd_src()
        click.echo("Removing {0}".format(pkg_name))
        shutil.rmtree(pkg_name)
    ws.recreate_index()
    ws.cd_root()


@main.command(short_help="Create a new catkin package.",
              help="This is a package creation wizard, to help creating new catkin packages. You can specify whether "
                   "to create a library or executable, ROS or non-ROS package and whether to create a Gitlab repo. "
                   "Appropriate template files and directory tree are created. When creating the repo you can choose "
                   "the namespace. The repo name is tested for conformity with the guidelines and conflicts with "
                   "rosdep packages are avoided.")
@click.argument("pkg_name", type=click.STRING, required=True)
@click.option('-t', 'pkg_type', type=click.Choice(['lib', 'exec']), help="Type: Choose between library or executable",
              prompt="Please choose package type [lib|exec]")
@click.option('-r', 'ros', is_flag=True, help="Make ROS package", prompt="Should this be a ROS package?")
@click.option('-g', 'create_git_repo', is_flag=True, help="Create Git repository", prompt="Create a git repository?")
@click.pass_obj
def create(ws, pkg_name, pkg_type, ros, create_git_repo):
    """ Create a new catkin package """
    ws.cd_root()

    pkg_name = check_naming(pkg_name)

    if ros:
        pkg_name += "_ros"
    if pkg_type == "exec":
        pkg_name += "_tool"

    if pkg_name in get_rosdeps():
        click.secho("This name collides with a rosdep dependency. Please choose a different one.", fg="red")
        sys.exit(1)

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
    user = get_gituserinfo()
    click.echo("     --> Package Maintainer.... " + user['name'] + " <" + user['email'] + ">")

    create_directories(pkg_name, pkg_type, ros)
    create_files(pkg_name, pkg_type, ros)

    if create_git_repo:
        git = Git()
        url = git.create_repo(pkg_name)
        subprocess.call("sed -i " +
                        "-e 's#\${PACKAGE_REPOSITORY_URL}#" + url + "#g' " +
                        "package.xml", shell=True)
        # Initialize repository
        ws.cd_src()
        os.chdir(pkg_name)
        subprocess.call("git init", shell=True)
        subprocess.call("git remote add origin " + url + " >/dev/null 2>&1", shell=True)
        with open('.gitignore', 'w') as f:
            f.write("*~")
        subprocess.call("git add . >/dev/null 2>&1", shell=True)
        subprocess.call("git commit -m 'Initial commit' >/dev/null 2>&1", shell=True)
        subprocess.call("git push -u origin master >/dev/null 2>&1", shell=True)
        ws.add(pkg_name, url)
    else:
        subprocess.call("sed -i -e '/  <url/d' package.xml", shell=True)


@main.group(short_help="Investigate dependencies of catkin packages.")
@click.pass_obj
def deps(ws):
    pass


@deps.command(short_help="Visualize dependencies of catkin packages.",
              help="This is a powerfull tool to visualize dependecies of individual packages or your complete "
                   "workspace. You can specify a package name, use the '--this' flag or leave the argument away to "
                   "create dependency graphs for the whole workspace. Dependencys are checked by using catkin, "
                   "the resulting images are written to 'ws/pics/'")
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
@click.option("--this", is_flag=True)
@click.option("--repos-only", is_flag=True)
@click.pass_obj
def draw(ws, pkg_name, this, repos_only):
    """ Visualize dependencies of catkin packages."""
    pkg_list = ws.get_catkin_package_names()

    if pkg_name:
        if pkg_name not in pkg_list:
            click.secho("Package not found, cant create graph", fg="red")
            sys.exit(1)
        pkg_list = [pkg_name]
    elif this:
        pkg_name = os.path.basename(ws.org_dir)
        if pkg_name not in pkg_list:
            click.secho("{0} does not seem to be a catkin package.".format(pkg_name), fg="red")
            sys.exit(1)
        pkg_list = [pkg_name]
    else:
        if click.confirm("Create dependency graph for every package?"):
            for pkg_name in pkg_list:
                click.echo("Creating graph for {}...".format(pkg_name))
                deps = ws.get_dependencies(pkg_name, deep=True)
                graph = Digraph(deps, repos_only)
                graph.plot(pkg_name, show=False)
        if click.confirm("Create complete dependency graph for workspace?", abort=True):
            pkg_name = os.path.basename(ws.root)

    deps = dict()
    for pkg in pkg_list:
        deps.update(ws.get_dependencies(pkg, deep=True))
    graph = Digraph(deps, repos_only)
    graph.plot(pkg_name)


@deps.command(short_help="List dependencies of catkin packages.",
              help="This will list all dependencies of a named catkin package.")
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
@click.option("--this", is_flag=True)
@click.pass_obj
def show(ws, pkg_name, this):
    """ Visualize dependencies of catkin packages."""
    pkg_list = ws.get_catkin_package_names()

    if this or not pkg_name:
        pkg_name = os.path.basename(ws.org_dir)
        if pkg_name not in pkg_list:
            click.secho("{0} does not seem to be a catkin package.".format(pkg_name), fg="red")
            sys.exit(1)

    these_deps = ws.get_dependencies(pkg_name, deep=True)[pkg_name]
    git_deps = set()
    apt_deps = set()

    def sort(d):
        for k, v in d.iteritems():
            if not v:
                apt_deps.add(k)
            else:
                git_deps.add(k)
                sort(v)

    sort(these_deps)

    click.echo("")
    click.echo("Dependencies for {}".format(pkg_name))
    click.echo("")
    click.echo("Gitlab dependencies")
    click.echo("===================")
    for dep in git_deps:
        click.echo(dep)
    click.echo("")
    click.echo("Apt-get dependencies")
    click.echo("====================")
    for dep in apt_deps:
        click.echo(dep)


@deps.command(short_help="Lookup reverse dependencies.",
              help="This will crawl all packages (in the MRT workspace, on the master branch, on the latest commit, "
                   "in gitlab) inorder to detect, who directly relies on this pkg.")
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
@click.option("--this", is_flag=True)
@click.option("-u", "--update", is_flag=True)
@click.pass_obj
def rlookup(ws, pkg_name, this, update):
    if update or not os.path.exists(user_settings['Cache']['CACHED_DEPS_WS']):
        click.echo("Updating repo cache...")
        process = subprocess.Popen(['mrt maintenance update_cached_deps'], shell=True)
        process.wait()  # Wait for process to finish and set returncode
        # print(process.returncode)

    if not pkg_name and not this:
        click.secho("Please specify a package or use the '--this' flag.", fg="red")
        sys.exit(1)

    if this:
        pkg_list = ws.get_catkin_package_names()
        pkg_name = os.path.basename(ws.org_dir)
        if pkg_name not in pkg_list:
            click.secho("{0} does not seem to be a catkin package.".format(pkg_name), fg="red")
            sys.exit(1)

    rdeps = {}
    for root, dirs, files in os.walk(user_settings['Cache']['CACHED_DEPS_WS']):
        def insert_into_dict(d, data):
            key = data[0]
            if type(d) is list:
                d.append(key)
                return d
            elif type(d) is dict and key not in d:
                if len(data) == 2:
                    d[key] = []
                else:
                    d[key] = dict()
            d[key] = insert_into_dict(d[key], data[1:])
            return d

        if files == ["package.xml"]:
            filename = os.path.join(root, files[0])
            root, branch = os.path.split(root)
            root, repo = os.path.split(root)
            root, namespace = os.path.split(root)
            with open(filename, 'r') as f:
                for line in f:
                    line = line.decode("utf-8")
                    if pkg_name in line and "depend" in line:
                        match = re.search("\</.*\>", line)
                        typ = match.string[match.start() + 2:match.end() - 1]
                        rdeps = insert_into_dict(rdeps, [namespace, repo, branch, typ])

    click.echo("I found the following packages relying on {}:\n".format(pkg_name))
    for namespace, d_repo in rdeps.iteritems():
        for repo, d_branches in d_repo.iteritems():
            click.echo("{}/{}:".format(namespace, repo))
            for branch, typ in d_branches.iteritems():
                click.echo("\t- On branch '{}': {}".format(branch, typ))
