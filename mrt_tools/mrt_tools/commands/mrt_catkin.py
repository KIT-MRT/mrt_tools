from mrt_tools.base import Workspace
from mrt_tools.utilities import *


@click.command(context_settings=dict(ignore_unknown_options=True, ))
@click.argument('action', type=click.STRING)
@click.option('-rd', '--resolve-deps', is_flag=True, help='Check and resolve dependencies before building workspace.')
@click.option('--eclipse', is_flag=True, help='Create a eclipse project.')
@click.option('--debug', is_flag=True, help='Build in debug mode.')
@click.option('--release', is_flag=True, help='Build in release mode.')
@click.option('--verbose', is_flag=True, help='Compile in verbose mode.')
@click.argument('catkin_args', nargs=-1, type=click.UNPROCESSED)
def main(action, resolve_deps, eclipse, debug, release, verbose, catkin_args):
    """ A wrapper for catkin. """
    org_dir = os.getcwd()
    ws = Workspace()
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
        subprocess.call(["catkin", action])
    else:
        subprocess.call(["catkin", action]+list(catkin_args))

    if build_eclipse:
        ws.cd_root()
        set_eclipse_project_setting()
