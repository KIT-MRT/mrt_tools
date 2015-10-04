from mrt_tools.utilities import *
from mrt_tools.base import *
import click


########################################################################################################################
# Fixes
########################################################################################################################
@click.group()
@click.pass_context
def main(ctx):
    """Repair tools..."""
    ctx.obj = Workspace()


@main.command()
@click.pass_obj
def url_in_package_xml(ws):
    """Inserts missing URL into package.xml"""

    def insert_url(file_name, url):
        with open(file_name, 'r') as f:
            contents = f.readlines()
        click.clear()
        for index, item in enumerate(contents):
            click.echo("{0}: {1}".format(index, item[:-1]))
        linenumber = click.prompt("\n\nPlease specify the line to insert the url in", type=click.INT)
        contents.insert(linenumber, '  <url type="repository">{0}</url>\n'.format(url))
        contents = "".join(contents)
        with open(file_name, 'w') as f:
            f.write(contents)
        click.clear()
        if click.confirm("OK, did that. Commit these changes?"):
            org_dir = os.getcwd()
            os.chdir(os.path.dirname(file_name))
            subprocess.call("git add {0}".format(file_name), shell=True)
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


@main.command()
@click.argument("package", required=False)
@click.pass_obj
def update_cmakelists(ws, package):
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

    if not package:
        for pkg_name in catkin_packages:
            ws.cd_src()
            check_and_update_cmakelists(pkg_name, current_version)
    else:
        check_and_update_cmakelists(package, current_version)

    click.secho("The commit is not yet pushed, in case you didn't really test the changes yet... You "
                "didn't, right? Ok, so go ahead and test them and then run 'mrt wstool update'", fg="yellow")


@main.command()
@click.pass_obj
def recreate_rosinstall(ws):
    """Reinitialise the workspace index"""
    ws.cd_src()
    click.secho("Removing wstool database src/.rosinstall", fg="yellow")
    os.remove(".rosinstall")
    click.echo("Initializing wstool...")
    ws.recreate_index(write=True)


@main.command()
@click.pass_obj
def resolve_deps(ws):
    """Resolve dependencies for packages"""
    ws.resolve_dependencies()