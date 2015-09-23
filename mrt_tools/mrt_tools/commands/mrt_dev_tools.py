#!/usr/bin/python
from mrt_tools.settings import *
from mrt_tools.commands.mrt_create_pkg import create_cmakelists
from mrt_tools.base import *
import shutil
import os

self_dir = get_script_root()
current_version = None
with open(self_dir + "/templates/CMakeLists.txt") as f:
    for line in f:
        if line.startswith("#pkg_version="):
            current_version = line[:-1]
            break
if not current_version:
    raise Exception("current pkg_version could not be found.")


@click.group()
def main():
    """A collection of development functions"""
    pass


@main.command()
@click.argument("package", required=False)
def update_cmakelists(package):
    """Update CMAKELISTS"""
    ws = Workspace()
    catkin_packages = ws.get_catkin_package_names()

    if not package:
        for pkg_name in catkin_packages:
            ws.cd_src()
            check_and_update_cmakelists(pkg_name)
    else:
        check_and_update_cmakelists(package)

    click.secho("The commit is not yet pushed, in case you didn't really test the changes yet... You "
                           "didn't, right? Ok, so go ahead and test them and then run 'mrt wstool update'", fg="yellow")


def check_and_update_cmakelists(pkg_name):
    os.chdir(pkg_name)
    with open("CMakeLists.txt") as f:
        pkg_version = f.readline()[:-1]
    if pkg_version != current_version:
        click.echo("\n{0}: Package versions not matching: {1}<->{2}".format(pkg_name.upper(), pkg_version,
                                                                            current_version))
        if click.confirm("Update CMakeLists?"):
            ros = click.confirm("ROS package?")
            pkg_type = ""
            while not ((pkg_type == "lib") or (pkg_type == "exec")):
                pkg_type = click.prompt("[lib/exec]")

            shutil.copyfile("CMakeLists.txt", "CMakeLists.txt.bak")
            create_cmakelists(pkg_name, pkg_type, ros, self_dir)

            process = subprocess.Popen("meld CMakeLists.txt.bak CMakeLists.txt", shell=True)
            process.wait()

            if not click.confirm("Do you want to keep the changes"):
                shutil.copyfile("CMakeLists.txt.bak", "CMakeLists.txt")
                os.remove("CMakeLists.txt.bak")
                return
            os.remove("CMakeLists.txt.bak")

            if click.confirm("Have you tested your changes and want to commit them now?"):
                subprocess.call("git add CMakeLists.txt", shell=True)
                subprocess.call("git commit -m 'Update CMakeLists.txt to {0}'".format(current_version), shell=True)



@main.command()
def penalty():
    """Report a crime to the deamon"""
    subprocess.call('xdg-email \
                    --utf8 \
                    --body "Lieber Ablassdaemon,\n ich möchte folgende Meldung machen:\n\n" \
                    --subject "Nachricht an den Ablassdaemon" \
                    "ablassdaemon@mrt.kit.edu"', shell=True)


@main.command()
def clean():
    """Delete everything in current workspace."""
    ws = Workspace()
    ws.test_for_changes()
    ws.cd_root()
    current_path = os.getcwd()
    click.confirm("Delete everything within " + current_path, abort=True)
    file_list = [f for f in os.listdir(".")]
    for f in file_list:
        if os.path.isdir(f):
            shutil.rmtree(f)
        else:
            os.remove(f)


@main.command()
def fix_package_xml():
    """Inserts missing URL into package.xml"""

    def insert_url(filename, url):
        with open(filename, 'r') as f:
            contents = f.readlines()
        click.clear()
        for index, item in enumerate(contents):
            click.echo("{0}: {1}".format(index, item))
        linenumber = click.prompt("Line to enter url?", type=click.INT)
        contents.insert(linenumber, '  <url type="repository">{0}</url>\n'.format(url))
        contents = "".join(contents)
        with open(filename, 'w') as f:
            f.write(contents)
        if click.confirm("Commit?"):
            org_dir = os.getcwd()
            os.chdir(os.path.dirname(filename))
            subprocess.call("git add {0}".format(filename), shell=True)
            subprocess.call("git commit -m 'Added repository url to package.xml'", shell=True)
            os.chdir(org_dir)

    ws = Workspace()
    ws.pkgs = ws.get_catkin_packages()
    ws.config = wstool_config.Config([], ws.src)
    ws.cd_src()
    for pkg in ws.pkgs.keys():
        try:
            # Try to read it from package xml
            if len(ws.pkgs[pkg].urls) > 1:
                raise IndexError
            ssh_url = ws.pkgs[pkg].urls[0].url
        except IndexError:
            click.secho("Warning: No URL (or multiple) defined in src/" + pkg + "/package.xml!", fg="yellow")
            try:
                # Try reading it from git repo
                with open(pkg + "/.git/config", 'r') as f:
                    ssh_url = next(line[7:-1] for line in f if line.startswith("\turl"))
                    insert_url(ws.src + "/" + pkg + "/package.xml", ssh_url)
            except IOError:
                click.secho("Warning: Could not figure out any URL for " + pkg, fg="red")
                ssh_url = None
        ws.add(pkg, ssh_url, update=False)

    # Create rosinstall file from config
    ws.write()
