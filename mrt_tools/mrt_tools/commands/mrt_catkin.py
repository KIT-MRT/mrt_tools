from mrt_tools.Workspace import Workspace
from mrt_tools.utilities import *


@click.command(context_settings=dict(ignore_unknown_options=True, ), short_help="A wrapper for catkin.",
               help=subprocess.check_output(["catkin", "--help"]))
@click.argument('action', type=click.STRING)
@click.option('-rd', '--resolve-deps', is_flag=True, help='Check and resolve dependencies before building workspace.')
@click.option('--eclipse', is_flag=True, help='Create a eclipse project.')
@click.option('--debug', is_flag=True, help='Build in debug mode.')
@click.option('--release', is_flag=True, help='Build in release mode.')
@click.option('--verbose', is_flag=True, help='Compile in verbose mode.')
@click.option('-w', '--warnings', is_flag=True, help='Show all warnings during comilation. This overrides user '
                                                     'settings')
@click.option('-nw', '--no-warnings', is_flag=True, help='Show no warnings during comilation. This overrides user '
                                                     'settings')
@click.option('-y', '--default_yes', is_flag=True, help='Default to yes when asked to install dependencies.')
@click.argument('catkin_args', nargs=-1, type=click.UNPROCESSED)
def main(action, resolve_deps, eclipse, debug, release, verbose, warnings, no_warnings, default_yes, catkin_args):
    """ A wrapper for catkin. """
    org_dir = os.getcwd()
    ws = Workspace()
    ws.cd_root()

    if debug:
        catkin_args = ("-DCMAKE_BUILD_TYPE=Debug",) + catkin_args
    elif release:
        catkin_args = ("-DCMAKE_BUILD_TYPE=RelWithDebInfo",) + catkin_args
    else:
        catkin_args = ("-DCMAKE_BUILD_TYPE={}".format(user_settings['Catkin']['DEFAULT_BUILD_TYPE']),) + catkin_args

    if (user_settings['Catkin']['SHOW_WARNINGS_DURING_COMPILATION'] or warnings) and not no_warnings:
        catkin_args = ("-DCMAKE_CXX_FLAGS=-Wall",) + ("-DCMAKE_CXX_FLAGS=-Wextra",) + catkin_args

    build_eclipse = False
    if eclipse:
        build_eclipse = True
        catkin_args = ("--force-cmake",) + catkin_args
        catkin_args = ("-GEclipse CDT4 - Unix Makefiles",) + catkin_args

    if verbose:
        catkin_args += ("-v",)
        catkin_args += ("--make-args VERBOSE=1 --",)

    if resolve_deps:
        ws.resolve_dependencies(default_yes=default_yes)

    os.chdir(org_dir)
    if len(catkin_args) == 0:
        subprocess.call(["catkin", action])
    else:
        subprocess.call(["catkin", action]+list(catkin_args))

    if build_eclipse:
        set_eclipse_project_setting(ws.root)
