from mrt_py_tools import mrt_base_tools, mrt_dep_plot
from catkin_pkg import packages
import click
import sys
import os


def get_detailed_deps(pkg_name, all_pkgs):
    if pkg_name in all_pkgs.keys():
        deps = [d.name for d in all_pkgs[pkg_name].build_depends]
        if len(deps) > 0:
            deps = [get_detailed_deps(d, all_pkgs) for d in deps]
            return {pkg_name: deps}
        else:
            return {pkg_name: []}
    else:
        return pkg_name


@click.command()
@click.argument("pkg_name", type=click.STRING, required=False)
def main(pkg_name):
    """ Visualize dependencies of catkin packages inside a workspace """
    mrt_base_tools.change_to_workspace_root_folder()

    all_pkgs = packages.find_packages("src")

    if pkg_name:
        if pkg_name in all_pkgs.keys():
            pkgs = {k: v for k, v in all_pkgs.items() if k == pkg_name}
        else:
            print("Package not found, cant create graph")
            sys.exit(1)
    else:
        pkg_name = os.path.basename(os.getcwd())
        pkgs = all_pkgs

    deps = pkgs.keys()
    deps = [get_detailed_deps(d, all_pkgs) for d in deps]

    mrt_dep_plot.plot_digraph(deps, pkg_name)

# TODO Create interactive plots
# TODO Create centric plot, when no package name is given
