#!/usr/bin/python
import click

__author__ = 'bandera'
from mrt_py_tools import mrt_base_tools
import os
import subprocess
import sys
import shutil


def set_eclipse_project_setting():
    mrt_base_tools.change_to_workspace_root_folder()
    os.chdir("build")
    for project in mrt_base_tools.find(".project", "build"):
        os.chdir(os.path.dirname(project))
        # set environment variables
        subprocess.call(
            'awk -f $(rospack find mk)/eclipse.awk .project > .project_with_env && mv .project_with_env .project',
            shell=True)

        # add support for indexing
        if not os.path.isfile("./.settings/language.settings.xml"):
            if not os.path.isdir("./.settings"):
                os.mkdir("./.settings")
        script_dir = mrt_base_tools.get_script_root()
        shutil.copy(script_dir + "/templates/language.settings.xml", "./.settings")


@click.command()
@click.argument('action', type=click.STRING)
@click.option('-rd', '--resolve-deps', is_flag=True, help='Check and resolve dependencies before building workspace.')
@click.option('--eclipse', is_flag=True, help='Create a eclipse project.')
@click.option('--debug', is_flag=True, help='Build in debug mode.')
@click.option('--release', is_flag=True, help='Build in release mode.')
@click.option('--verbose', is_flag=True, help='Compile in verbose mode.')
@click.argument('catkin_args', nargs=-1, type=click.STRING)
def main(action, rd, eclipse, debug, release, verbose, catkin_args):
    """ A wrapper for catkin """
    if debug:
        catkin_args.append("-DCMAKE_BUILD_TYPE=Debug")

    if release:
        catkin_args.append("-DCMAKE_BUILD_TYPE=RelWithDebInfo")

    if verbose:
        catkin_args.append("-v")
        catkin_args.append("--make-args")
        catkin_args.append("VERBOSE=1")

    build_eclipse = False
    if eclipse:
        build_eclipse = True
        catkin_args.append("--force-cmake")
        catkin_args.append("-GEclipse CDT4 - Unix Makefiles")

    if rd:
        scriptRoot=mrt_base_tools.get_script_root()
        try:
            subprocess.check_call([os.path.join(scriptRoot, "mrt_resolve_deps")])
        except subprocess.CalledProcessError:
            print("Cannot resolve dependencies.\n")
            sys.exit(1)

    mrt_base_tools.change_to_workspace_root_folder()
    subprocess.call(["catkin"] + action + catkin_args)

    if build_eclipse:
        set_eclipse_project_setting()