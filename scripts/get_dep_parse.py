#!/usr/bin/python
__author__ = "Omer Sahin Tas"
__date__ = "10.09.2015"

import os
from lxml import etree
import copy


def get_deps(src_dir):

    dependencies = {}

    for (dirpath, dirnames, filenames) in os.walk(src_dir):

        if "package.xml" in filenames:
            pkg = dirpath + "/package.xml"
            root = etree.parse(pkg).getroot()

            pkg_name = root.xpath("name")[0].text
            pkg_deps = []

            for i, dep in enumerate(root.xpath("depend")):
                pkg_deps.append(dep.text)

            dependencies[pkg_name] = pkg_deps

    return dependencies


def get_detailed_deps(pkg_deps, all_deps):

    # for all dependencies in the dependency list
    for dep in pkg_deps:

        # if the dependency has any sub-dependencies:
        if dep in all_deps.keys() and len(all_deps[dep]) > 0:

            # get the list-index of the dependency
            ind = pkg_deps.index(dep)

            # replace the list element with a dict
            pkg_deps[ind] = {}

            # recursively check if the dependency has any sub-dependencies
            pkg_deps[ind][dep] = get_detailed_deps(all_deps[dep], all_deps)

    return pkg_deps


def main(src_dir):
    dependencies = get_deps(src_dir)

    detailed_deps = copy.copy(dependencies)
    for pkg in dependencies.keys():
        detailed_deps[pkg] = get_detailed_deps(detailed_deps[pkg], dependencies)

    return detailed_deps
