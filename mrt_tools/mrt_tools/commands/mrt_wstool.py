from mrt_tools.Workspace import Workspace
from mrt_tools.Git import test_git_credentials
from mrt_tools.utilities import *


########################################################################################################################
# WStool
########################################################################################################################
@click.command(context_settings=dict(ignore_unknown_options=True, ), short_help="A wrapper for wstool.",
               help=subprocess.check_output(["wstool", "--help"]))
@click.argument('action', type=click.STRING)
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def main(action, args):
    """
    A wrapper for wstool.
    """
    ws = Workspace()
    ws.cd_src()

    if action == "init":
        click.secho("Removing wstool database src/.rosinstall", fg="yellow")
        os.remove(".rosinstall")
        click.echo("Initializing wstool...")
        ws.recreate_index()
        return

    # Need to init wstool?
    if not os.path.exists(".rosinstall"):
        ws.write()

    if action == "update":
        # Test git credentials to avoid several prompts
        if ws.contains_https():
            test_git_credentials()

        ws.recreate_index() # Rebuild .rosinstall in case a package was deletetd manually

        # Speedup the pull process by parallelization
        if not [a for a in args if a.startswith("-j")]:
            args += ("-j10",)

    if action == "fetch":
        if ws.contains_https():
            test_git_credentials()
        action = "foreach"
        args = ("git fetch", )

    if action == "push":
        # Search for unpushed commits
        unpushed_repos = ws.unpushed_repos()

        if len(unpushed_repos) > 0:
            if click.confirm("Push them now?"):
                for x in unpushed_repos:
                    ws.cd_src()
                    os.chdir(x)
                    subprocess.call("git push", shell=True)
        else:
            click.echo("No unpushed commits.")
        sys.exit(0)

    # Pass the rest to wstool
    if len(args) == 0:
        process = subprocess.Popen(["wstool", action, "-t", ws.src])
    else:
        process = subprocess.Popen(["wstool", action, "-t", ws.src] + list(args))
    process.wait()  # Wait for process to finish and set returncode

    if action == "status":
        ws.unpushed_repos()

    sys.exit(process.returncode)
