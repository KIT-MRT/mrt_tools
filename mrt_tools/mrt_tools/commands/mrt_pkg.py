from mrt_tools.Workspace import Workspace
from mrt_tools.Digraph import Digraph
from mrt_tools.utilities import *
from mrt_tools.Git import Git

# Autocompletion
try:
    tmp_ws = Workspace()
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

    for pkg_name in pkg_names:

        # Test for package
        if ws.find(pkg_name):
            click.echo("Package {0} already present in workspace config. Run 'mrt wstool update'.".format(pkg_name))
            continue

        # Add package to workspace
        git = Git()
        repo = git.find_repo(pkg_name)
        if not repo:
            continue
        url = repo[git.get_url_string()]
        ws.add(pkg_name, url)

    ws.resolve_dependencies(git=git)


@main.command(short_help="Deletes package from workspace.",
              help="This command let's you savely remove a package from the current workspace, by checking for "
                   "uncommited or unpushed changes and removing the directory as well as the .rosinstall config entry.")
@click.argument("pkg_name", type=click.STRING, required=True, autocompletion=suggestions)
@click.pass_obj
def remove(ws, pkg_name):
    """Delete package from workspace."""
    pkg_list = ws.get_catkin_package_names()
    if pkg_name:
        if pkg_name not in pkg_list:
            click.secho("Package does not exist.", fg="red")
            sys.exit(1)
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


@main.command(short_help="Visualize dependencies of catkin packages.",
              help="This is a powerfull tool to visualize dependecies of individual packages or your complete "
                   "workspace. You can specify a package name, use the '--this' flag or leave the argument away to "
                   "create dependency graphs for the whole workspace. Dependencys are checked by using catkin, "
                   "the resulting images are written to 'ws/pics/'")
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
@click.option("--this", is_flag=True)
@click.option("--repos-only", is_flag=True)
@click.pass_obj
def visualize_deps(ws, pkg_name, this, repos_only):
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
                deps = [ws.get_dependencies(pkg_name, deep=True)]
                graph = Digraph(deps, repos_only)
                graph.plot(pkg_name, show=False)
        if click.confirm("Create complete dependency graph for workspace?", abort=True):
            pkg_name = os.path.basename(ws.root)

    deps = [ws.get_dependencies(pkg, deep=True) for pkg in pkg_list]
    graph = Digraph(deps, repos_only)
    graph.plot(pkg_name)


@main.command(short_help="List dependencies of catkin packages.",
              help="This will list all dependencies of a named catkin package.")
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
@click.option("--this", is_flag=True)
@click.pass_obj
def list_deps(ws, pkg_name, this):
    """ Visualize dependencies of catkin packages."""
    pkg_list = ws.get_catkin_package_names()

    if this or not pkg_name:
        pkg_name = os.path.basename(ws.org_dir)
        if pkg_name not in pkg_list:
            click.secho("{0} does not seem to be a catkin package.".format(pkg_name), fg="red")
            sys.exit(1)

    dep_dict = ws.get_dependencies(pkg_name, deep=True)
    dep_list = dep_dict[pkg_name]
    git_deps = set()
    apt_deps = set()

    found_one = True
    while found_one:
        found_one = False
        for obj in dep_list:
            if isinstance(obj, basestring):
                found_one = True
                apt_deps.add(obj)
            elif isinstance(obj, dict):
                found_one = True
                git_deps.update(set(obj.keys()))
                dep_list += obj.values()
            elif isinstance(obj, list):
                found_one = True
                dep_list += obj
            if found_one:
                dep_list.remove(obj)

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
