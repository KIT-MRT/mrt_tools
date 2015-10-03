from mrt_tools.utilities import *
from mrt_tools.base import *
import click

# Autocompletion
try:
    tmp_ws = Workspace()
    suggestions = tmp_ws.get_catkin_package_names()
    repo_list = import_repo_names()
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
    """Package related tasks..."""
    ctx.obj = Workspace()


@main.command()
@click.argument("pkg_name", type=click.STRING, required=True, autocompletion=repo_list)
@click.pass_obj
def add(ws, pkg_name):
    """Clone catkin packages from gitlab."""
    """
    This tool searches for, and clones a package from the Gitlab Server into the current workspace.
    Execute this script from within a catkin workspace
    """

    # Test for package
    if ws.find(pkg_name):
        click.echo("Package {0} already present in workspace config. Run 'mrt wstool update'.".format(pkg_name))
        return

    # Add package to workspace
    git = Git()
    url = git.find_repo(pkg_name)  # Gives error string
    if not url:
        sys.exit(1)
    ws.add(pkg_name, url)
    ws.resolve_dependencies(git=git)


@main.command()
@click.argument("pkg_name", type=click.STRING, required=True, autocompletion=suggestions)
@click.pass_obj
def remove(ws, pkg_name):
    """Delete package from workspace."""
    ws.test_for_changes(pkg_name)
    ws.cd_src()
    click.echo("Removing {0}".format(pkg_name))
    shutil.rmtree(pkg_name)
    ws.recreate_index()
    ws.cd_root()


@main.command()
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
    click.echo("     --> Package Maintainer.... " + user['name'] + " <" + user['mail'] + ">")

    create_directories(pkg_name, pkg_type, ros)
    create_files(pkg_name, pkg_type, ros)

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
    else:
        subprocess.call("sed -i -e '/  <url/d' package.xml", shell=True)


@main.command()
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
@click.pass_obj
def visualize_deps(ws, pkg_name):
    """ Visualize dependencies of catkin packages."""
    pkg_list = ws.get_catkin_package_names()
    ws.cd_root()
    if pkg_name:
        if pkg_name not in pkg_list:
            click.secho("Package not found, cant create graph", fg="red")
            sys.exit(1)
        pkg_list = [pkg_name]
    else:
        if click.confirm("Create dependency graph for every package?"):
            for pkg_name in pkg_list:
                deps = [ws.get_dependencies(pkg_name, deep=True)]
                graph = Digraph(deps)
                graph.plot(pkg_name, show=False)
        if click.confirm("Create complete dependency graph for workspace?", abort=True):
            pkg_name = os.path.basename(os.getcwd())

    deps = [ws.get_dependencies(pkg_name, deep=True) for pkg_name in pkg_list]

    graph = Digraph(deps)
    graph.plot(pkg_name)
