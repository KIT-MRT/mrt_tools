import distutils.util
import subprocess
from click.decorators import argument
from mrt_py_tools import mrt_base_tools
from wstool import config_yaml
from wstool import config as wstool_config
import click
import os


@click.command(context_settings=dict(ignore_unknown_options=True, ))
@click.argument('action', type=click.STRING)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def main(action, args):
    """
    A wrapper for wstool
    """

    mrt_base_tools.change_to_workspace_root_folder()
    ws_root = os.getcwd()
    os.chdir("src")

    if action == "init":
        click.secho("Removing wstool database src/.rosinstall", fg="yellow")
        os.remove(".rosinstall")

    # Need to init wstool?
    if not os.path.exists(".rosinstall"):
        click.echo("Initializing wstool...")
        subprocess.call("wstool init . > /dev/null", shell=True)

    # Gather git directories
    rosinstall = config_yaml.get_path_specs_from_uri(".rosinstall")
    wsconfig = wstool_config.Config(rosinstall, ".")
    rosinstall_dirs = {x.get_local_name() for x in rosinstall}
    git_directories = []
    for dir in os.listdir("."):
        if os.path.isdir(dir + "/.git"):
            git_directories.append(dir)
    git_directories = {x for x in git_directories}

    # Removing old repos from rosinstall
    old_repos = rosinstall_dirs.difference(git_directories)
    for x in old_repos:
        click.secho("Found old git repository '" + x + "': Deleting entry from wstool", fg="red")
        wsconfig.remove_element(x)

    # Adding new repos to rosinstall
    new_repos = git_directories.difference(rosinstall_dirs)
    for x in new_repos:
        click.secho("Found new git repository '" + x + "': repository added", fg="green")
        try:
            with open(x + "/.git/config", 'r') as f:
                ssh_url = next(line[7:-1] for line in f if line.startswith("\tsurl"))
        except StopIteration:
            ssh_url = None
        ps = config_yaml.PathSpec(x, "git", ssh_url)
        wsconfig.add_path_spec(ps)
    config_yaml.generate_config_yaml(wsconfig, ".rosinstall", "")

    if action == "update":

        # Search for unpushed commits
        unpushed_repos = []
        for ps in wsconfig.get_source():
            os.chdir(ws_root + "/src/" + ps.get_local_name())
            git_process = subprocess.Popen("git log --branches --not --remotes", shell=True, stdout=subprocess.PIPE)
            result = git_process.communicate()

            if result[0] != "":
                click.secho("Unpushed commits in repo '" + ps.get_local_name() + "'", fg="yellow")
                subprocess.call("git log --branches --not --remotes --oneline", shell=True)
                unpushed_repos.append(ps.get_local_name())

        if len(unpushed_repos) > 0:
            choice_str = raw_input("Push them now? [y/N]")
            if choice_str == "":
                choice_str = "n"
            push_now = distutils.util.strtobool(choice_str)

            if push_now:
                for x in unpushed_repos:
                    os.chdir(ws_root + "/src/" + x)
                    subprocess.call("git push", shell=True)

    # Pass the rest to wstool
    os.chdir(ws_root + "/src")
    if len(args) == 0:
        subprocess.call(["wstool", action])
    else:
        subprocess.call(["catkin", action, " ".join(args)])
