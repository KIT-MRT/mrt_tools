#!/usr/bin/python
__author__ = "Omer Sahin Tas"
__date__ = "10.09.2015"

import sys
import pprint
from get_dep_parse import main as get_dep_parse
from get_dep_plot import plot_main


def select_pkg(deps):

    print("\033[1m\033[4mNumber    Package Name\033[0m\033[0m")
    for i, pkg in enumerate(deps):
        print("%6i    %s" %(i, pkg))

    print("\n\n\033[1mEnter the package number whose dependency is to be plotted\033[0m")

    selection = raw_input()
    for i, pkg_name in enumerate(deps):
        if i == int(selection):
            print("Selected package: %s" %pkg_name)
            return pkg_name


def main(src_dir):
    # parse dependencies
    detailed_deps = get_dep_parse(src_dir)
    
    # ask for user input
    pkg_name = select_pkg(detailed_deps)
    selected_pkg = detailed_deps[pkg_name]
    
    if False:
        pprint.pprint(selected_pkg)
    
    plot_main(selected_pkg, pkg_name)
    


if __name__ == "__main__":
    print "usage: python get_dep_main.py ~/mrt_projects/bbf_workspace/"
    workspace = sys.argv[1]
    src_dir = workspace + "/src"
    main(src_dir)



