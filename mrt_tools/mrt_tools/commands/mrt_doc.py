from mrt_tools.utilities import *

import os
import subprocess
import tempfile
import sys
import webbrowser

# Autocompletion
try:
    tmp_ws = Workspace()
    suggestions = tmp_ws.get_catkin_pkg_names()
    repo_list = import_repo_names()
    os.chdir(tmp_ws.org_dir)
except:
    suggestions = []
    repo_list = []

self_dir = get_script_root()

########################################################################################################################
# Package
########################################################################################################################
@click.group()
def main():
    pass
    
@main.command(help="Generate the documentation of a package.")
@click.argument("pkg_name", type=click.STRING, required=True, autocompletion=repo_list)
def build(pkg_name):
    build_(pkg_name)

@main.command(short_help="Shows the documentation of a package.",
              help="Shows the documentation of a package. If the documentation is not found, it will be generated.")
@click.argument("pkg_name", type=click.STRING, required=True, autocompletion=repo_list)
def show(pkg_name):
    package_build_dir = subprocess.check_output(["catkin", "locate", "--build", pkg_name], universal_newlines=True).rstrip("\n")
    package_doxygen_output_dir = os.path.join(package_build_dir, "doxygen_doc")
    
    index_file = os.path.join(package_doxygen_output_dir, "html", "index.html")

    if not os.path.isfile(index_file):
        build_(pkg_name)
    
    if not os.path.isfile(index_file):
        raise RuntimeException("Documentation output not found. Expected to be in " + index_file)
    
    webbrowser.open("file://" + index_file)
    
def build_(pkg_name):
    package_src_dir = subprocess.check_output(["catkin", "locate", "--src", pkg_name], universal_newlines=True).rstrip("\n")
    package_build_dir = subprocess.check_output(["catkin", "locate", "--build", pkg_name], universal_newlines=True).rstrip("\n")

    doxygen_template_filename = os.path.abspath(os.path.join(self_dir, "templates/Doxygen"))

    package_doxygen_output_dir = os.path.join(package_build_dir, "doxygen_doc")
    
    os.makedirs(package_doxygen_output_dir)

    additional_doxygen_config = ""
    additional_doxygen_config += "PROJECT_NAME = \"" + pkg_name + "\"\n"
    additional_doxygen_config += "OUTPUT_DIRECTORY = \"" + package_doxygen_output_dir + "\"\n"

    user_doxyfile = os.path.join(package_src_dir, "Doxyfile")
    if os.path.isfile(user_doxyfile):
        additional_doxygen_config += "@INCLUDE = \"" + user_doxyfile + "\"\n"

    with tempfile.NamedTemporaryFile() as doxyfile:
        # read standard doxygen file
        with open(doxygen_template_filename, "rb") as f:
            doxyfile.write(f.read())

        # read generated project specific doxygen file
        doxyfile.write(additional_doxygen_config)
        doxyfile.flush()

        # run doxygen
        os.chdir(package_src_dir)
        subprocess.check_call(["doxygen", doxyfile.name])
