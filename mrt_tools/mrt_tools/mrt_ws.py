from mrt_tools.utilities import *
from mrt_tools.base import *
import time
import shutil
import click

# Autocompletion
# try:
#     tmp_ws = Workspace()
#     suggestions = tmp_ws.get_catkin_package_names()
#     repo_list = import_repo_names()
# except:
suggestions = []
repo_list = []
self_dir = get_script_root()


########################################################################################################################
### Workspace
########################################################################################################################
@click.group()
@click.pass_context
def main(ctx):
    """A collection of tools to perform on a catkin workspace"""
    ctx.obj = Workspace(silent=True)

    if not ctx.obj.exists() and ctx.invoked_subcommand != "init" and ctx.invoked_subcommand != "snapshot":
        click.secho("No catkin workspace root found.", fg="red")
        click.echo("This command must be invoked from within a workspace")
        sys.exit(1)


@main.command()
@click.pass_obj
def init(ws):
    """ Initialize a catkin workspace. """
    ws.create()


@main.command()
@click.pass_obj
def remove(ws):
    """Delete everything in current workspace."""
    ws.clean()


@main.command()
@click.argument('catkin_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def clean(ws, catkin_args):
    """Delete compiled code."""
    ws.cd_root()
    if not catkin_args:
        catkin_args = ("-a",)

    if len(catkin_args) == 0:
        subprocess.call(["catkin", "clean"])
    else:
        subprocess.call(["catkin", "clean"] + list(catkin_args))


@main.command(context_settings=dict(ignore_unknown_options=True, ))
@click.option('-rd', '--resolve-deps', is_flag=True, help='Check and resolve dependencies before building workspace.')
@click.option('--eclipse', is_flag=True, help='Create a eclipse project.')
@click.option('--debug', is_flag=True, help='Build in debug mode.')
@click.option('--release', is_flag=True, help='Build in release mode.')
@click.option('--verbose', is_flag=True, help='Compile in verbose mode.')
@click.argument('catkin_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def build(ws, resolve_deps, eclipse, debug, release, verbose, catkin_args):
    """Compile code"""
    org_dir = os.getcwd()
    ws.cd_root()

    if debug:
        catkin_args += ("-DCMAKE_BUILD_TYPE=Debug",)

    if release:
        catkin_args += (" -DCMAKE_BUILD_TYPE=RelWithDebInfo",)

    if verbose:
        catkin_args += (" -v",)
        catkin_args += (" --make-args",)
        catkin_args += (" VERBOSE=1",)

    build_eclipse = False
    if eclipse:
        build_eclipse = True
        catkin_args += (" --force-cmake",)
        catkin_args += (" -GEclipse CDT4 - Unix Makefiles",)

    if resolve_deps:
        ws.resolve_dependencies()

    os.chdir(org_dir)
    if len(catkin_args) == 0:
        subprocess.call(["catkin", "build"])
    else:
        subprocess.call(["catkin", "build"] + list(catkin_args))

    if build_eclipse:
        ws.cd_root()
        set_eclipse_project_setting()


@main.command()
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def status(ws, args):
    """Print the git status of files in workspace"""
    ws.cd_src()

    # Show untracked files as well
    if not ("--untracked" in args or "-u" in args):
        args += ("--untracked",)

    # Pass the rest to wstool
    if len(args) == 0:
        subprocess.call("wstool status")
    else:
        subprocess.call(["wstool", "status"] + list(args))

    ws.unpushed_repos()


@main.command()
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def info(ws, args):
    """List all git repos and their status."""
    ws.cd_src()

    # Show untracked files as well
    if not ("--untracked" in args or "-u" in args):
        args += ("--untracked",)

    # Pass the rest to wstool
    if len(args) == 0:
        subprocess.call(["wstool", "info"])
    else:
        subprocess.call(["wstool", "info"] + list(args))


@main.command()
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def update(ws, args):
    """Perform a git push & pull on every repo"""
    ws.cd_src()
    # Search for unpushed commits
    ws.scan()  # Rebuild .rosinstall in case a package was deletetd manually
    unpushed_repos = ws.unpushed_repos()

    if len(unpushed_repos) > 0:
        if click.confirm("Push them now?"):
            for x in unpushed_repos:
                ws.cd_src()
                os.chdir(x)
                subprocess.call("git push", shell=True)

    # Speedup the pull process by parallelization
    if not [a for a in args if a.startswith("-j")]:
        args += ("-j10",)

    # Pass the rest to wstool
    subprocess.call(["wstool", "update"] + list(args))


########################################################################################################################
### Snapshot
########################################################################################################################
@main.group()
def snapshot():
    """Save or restore the current state of the ws..."""
    pass


@snapshot.command()
@click.argument("name", type=click.STRING, required=True)
@click.pass_obj
def create(ws, name):
    """Create a snapshot of the current workspace."""
    """
    This function creates a zip file, containing the workspace configuration '.catkin_tools' and a '.rosinstall' file.
    The workspace configuration contains build settings like whether 'install' was specified.
    The .rosinstall file pins every repository to the commit it is at right now.
    """
    suffix = "_" + time.strftime("%y%m%d")
    snapshot_name = name + suffix + file_ending
    filename = os.path.join(os.getcwd(), snapshot_name)

    # First test whether it's safe to create a snapshot
    ws.test_for_changes(prompt="Are you sure you want to continue? These changes won't be included in the snapshot!")

    # Create snapshot of rosinstall
    ws.cd_root()
    ws.snapshot(filename=".rosinstall")

    # Create archive
    with open(version_file, "w") as f:
        f.write(snapshot_version)
    files = [('.rosinstall', 'src/.rosinstall'), '.catkin_tools', version_file]
    files += [os.path.join(dp, f) for dp, dn, fn in os.walk(".catkin_tools") for f in fn]
    zip_files(files, filename)
    os.remove(".rosinstall")
    os.remove(version_file)
    click.secho("Wrote snapshot to " + filename, fg="green")


@snapshot.command()
@click.argument("name", type=click.STRING, required=True)
def restore(name):
    """Restore a catkin workspace from a snapshot"""
    """
    This function takes a zip file as created in create_snapshot and tries to restore it.
    Therefor a new workspace is initiated, the settings and .rosinstall file are copied from the snapshot.
    Next, the specified commits are cloned into the workspace and the whole workspace is build.
    """
    org_dir = os.getcwd()
    filename = os.path.join(org_dir, name)
    workspace = os.path.join(org_dir, os.path.basename(name).split(".")[0] + "_snapshot_ws")

    # Read archive
    try:
        zf = zipfile.ZipFile(filename, "r", zipfile.ZIP_DEFLATED)
        # file_list = [f.filename for f in zf.filelist]
        version = zf.read(version_file)
    except IOError:
        click.echo(os.getcwd())
        click.secho("Can't find file: '" + name + file_ending + "'", fg="red")
        sys.exit()

    if version == "0.1.0":
        # Create workspace folder
        try:
            os.mkdir(workspace)
            os.chdir(workspace)
            ws = Workspace(silent=True)
            ws.create()
        except OSError:
            click.secho("Directory {0} exists already".format(workspace), fg="red")
            os.chdir(org_dir)
            sys.exit(1)

        # Extract archive
        zf.extractall(path=workspace)
        os.remove(os.path.join(workspace, version_file))

        # Clone packages
        click.secho("Cloning packages", fg="green")
        ws.update()
        ws.resolve_dependencies()

        # Build workspace
        click.secho("Building workspace", fg="green")
        subprocess.call(["catkin", "clean", "-a"])
        subprocess.call(["catkin", "build"])

    else:
        click.secho("ERROR: Snapshot version not known.", fg="red")


########################################################################################################################
### Package
########################################################################################################################
@main.group()
def pkg():
    """Package related tasks..."""
    pass


@pkg.command()
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


@pkg.command()
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


@pkg.command()
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


@pkg.command()
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
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


########################################################################################################################
### Fixes
########################################################################################################################
@main.group()
def fix():
    """Repair tools..."""
    pass


@fix.command()
@click.pass_obj
def url_in_package_xml(ws):
    """Inserts missing URL into package.xml"""

    def insert_url(filename, url):
        with open(filename, 'r') as f:
            contents = f.readlines()
        click.clear()
        for index, item in enumerate(contents):
            click.echo("{0}: {1}".format(index, item[:-1]))
        linenumber = click.prompt("\n\nPlease specify the line to insert the url in", type=click.INT)
        contents.insert(linenumber, '  <url type="repository">{0}</url>\n'.format(url))
        contents = "".join(contents)
        with open(filename, 'w') as f:
            f.write(contents)
        click.clear()
        if click.confirm("OK, did that. Commit these changes?"):
            org_dir = os.getcwd()
            os.chdir(os.path.dirname(filename))
            subprocess.call("git add {0}".format(filename), shell=True)
            subprocess.call("git commit -m 'Added repository url to package.xml'", shell=True)
            os.chdir(org_dir)

    ws.catkin_pkg_names = ws.get_catkin_package_names()
    ws.config = wstool_config.Config([], ws.src)
    ws.cd_src()

    for pkg_name in ws.catkin_pkg_names:
        filename = os.path.join(ws.src, pkg_name, "package.xml")
        # Try reading it from git repo
        try:
            with open(pkg_name + "/.git/config", 'r') as f:
                git_ssh_url = next(line[7:-1] for line in f if line.startswith("\turl"))
        except IOError:
            git_ssh_url = None

        # Try to read it from package xml
        try:
            if len(ws.catkin_pkgs[pkg_name].urls) > 1:
                raise IndexError
            xml_ssh_url = ws.catkin_pkgs[pkg_name].urls[0].url
        except IndexError:
            xml_ssh_url = None

        # Testing all cases:
        if xml_ssh_url is not None and git_ssh_url is not None:
            if xml_ssh_url != git_ssh_url:
                click.secho("WARNING in {0}: URL declared in src/{1}/package.xml, differs from the git repo url for {"
                            "0}!".format(pkg_name.upper(), pkg_name),
                            fg="red")
                click.echo("PackageXML: {0}".format(xml_ssh_url))
                click.echo("Git repo  : {0}".format(git_ssh_url))
                if click.confirm("Replace the url in package.xml with the correct one?"):
                    subprocess.call("sed -i -e '/  <url/d' {0}".format(filename), shell=True)
                    insert_url(filename, git_ssh_url)
        if xml_ssh_url is not None and git_ssh_url is None:
            click.secho("WARNING in {0}: URL declared in package.xml, but {1} does not seem to be a remote "
                        "repository!".format(pkg_name.upper(), pkg_name), fg="yellow")
            if click.confirm("Remove the url in package.xml?"):
                click.secho("Fixing...", fg="green")
                subprocess.call("sed -i -e '/  <url/d' {0}".format(filename), shell=True)
        if xml_ssh_url is None and git_ssh_url is not None:
            click.secho("WARNING in {0}: No URL (or multiple) defined in package.xml!".format(pkg_name.upper()),
                        fg="yellow")
            if click.confirm("Insert (Replace) the url in package.xml with the correct one?"):
                subprocess.call("sed -i -e '/  <url/d' {0}".format(filename), shell=True)
                insert_url(filename, git_ssh_url)
        if xml_ssh_url is None and git_ssh_url is None:
            click.secho("INFO in {0}: Does not seem to be a git repository. You should use Version Control for your "
                        "code!".format(pkg_name.upper()), fg="cyan")

        if git_ssh_url is not None:
            ws.add(pkg_name, git_ssh_url, update=False)

    ws.write()


@fix.command()
@click.argument("package", required=False)
@click.pass_obj
def update_cmakelists(ws, pkg):
    """Update CMAKELISTS"""
    catkin_packages = ws.get_catkin_package_names()

    # Read in newest CMakeLists.txt
    current_version = None
    with open(self_dir + "/templates/CMakeLists.txt") as f:
        for line in f:
            if line.startswith("#pkg_version="):
                current_version = line[:-1]
                break
    if not current_version:
        raise Exception("current pkg_version could not be found.")

    if not pkg:
        for pkg_name in catkin_packages:
            ws.cd_src()
            check_and_update_cmakelists(pkg_name, current_version)
    else:
        check_and_update_cmakelists(pkg, current_version)

    click.secho("The commit is not yet pushed, in case you didn't really test the changes yet... You "
                "didn't, right? Ok, so go ahead and test them and then run 'mrt wstool update'", fg="yellow")


@fix.command()
@click.pass_obj
def recreate_rosinstall(ws):
    """Reinitialise the workspace index"""
    ws.cd_src()
    click.secho("Removing wstool database src/.rosinstall", fg="yellow")
    os.remove(".rosinstall")
    click.echo("Initializing wstool...")
    ws.recreate_index(write=True)


@fix.command()
@click.pass_obj
def resolve_deps(ws):
    """Resolve dependencies for packages"""
    ws.resolve_dependencies()
