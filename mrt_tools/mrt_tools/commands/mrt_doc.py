from mrt_tools.Workspace import Workspace
from mrt_tools.utilities import *

import catkin_pkg.topological_order

import os
import subprocess
import tempfile
import webbrowser

# Autocompletion
try:
    tmp_ws = Workspace()
    suggestions = tmp_ws.get_catkin_package_names()
    repo_list = import_repo_names()
    os.chdir(tmp_ws.org_dir)
except:
    suggestions = []
    repo_list = []

self_dir = get_script_root()


########################################################################################################################
# Package
########################################################################################################################
@click.group(short_help="Build and show the documentation of a package.",
             help="The documentation of a package is build with doxygen using a template Doxyfile. If you wish, "
                  "you can also provide an individual Doxyfile by placing it in the root folder of the package. "
                  "Additional documentation can be provided in Markdown format ('.md') in the 'doc' folder. "
                  "The output files will lie in the build space of your workspace, "
                  "but can easily be opened with the 'show' command.")
def main():
    pass


@main.command(help="Generate the documentation of a workspace or package.")
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
@click.option("--this", is_flag=True, help="Build the package containing the current working directory.")
@click.option("--no-deps", is_flag=True, help="Only build specified packages, not their dependencies.")
@click.option("-v", "--verbose", is_flag=True, help="Print the info output of the doc generation")
def build(pkg_name, this, no_deps, verbose):
    ws = Workspace()
    
    # TODO: remove
    #build_workspace_doc(ws)
    #sys.exit(1)
    
    # add all workspace packages to possibly be doc builded
    pkg_list = ws.get_catkin_packages()
    is_build_workspace_doc = True
    
    if pkg_name or this:
        # build only the specified packge
        if pkg_name:
            if pkg_name not in pkg_list:
                click.secho("Package not found, can't build documentation", fg="red")
                sys.exit(1)
        # build only this packge
        elif this:
            pkg_name = os.path.basename(ws.org_dir)
            if pkg_name not in pkg_list:
                click.secho("{0} does not seem to be a catkin package.".format(pkg_name), fg="red")
                sys.exit(1)
        
        # clear doc build package list and set to specified one
        pkg_list = {pkg_name: pkg_list[pkg_name]}
          
        # add also dependencies if necessary  
        if not no_deps:
            pkg_list.update(get_dep_packages_in_workspace(ws, pkg_name))
            
        is_build_workspace_doc = False

    # order topologically to get the build order right
    pkg_list = catkin_pkg.topological_order.topological_order_packages(pkg_list)

    # output build summaey
    output = "The following packages will be doc builded: \n"
    for pkg, _ in pkg_list:
        output += "   - {}\n".format(pkg)
    click.echo(output)
    
    # build packages
    for pkg, _ in pkg_list:
        click.secho(">>> " + pkg, fg="cyan", bold=True)
        build_(ws, pkg, verbose)
        click.secho("<<< " + pkg, fg="cyan")
        
    #if is_build_workspace_doc:
    #    build_workspace_doc()

        
@main.command(short_help="Shows the documentation of a package.",
              help="Shows the documentation of a package. If the documentation is not found, it will be generated.")
@click.argument("pkg_name", type=click.STRING, required=True, autocompletion=suggestions)
def show(pkg_name):
    _, _, package_doxygen_output_dir = check_paths_(pkg_name)
    index_file = os.path.join(package_doxygen_output_dir, "html", "index.html")

    if not os.path.isfile(index_file):
        build_(pkg_name)

    if not os.path.isfile(index_file):
        raise RuntimeError("Documentation output not found. Expected to be in " + index_file)

    webbrowser.open("file://" + index_file)

@main.command(help="Removes the documentation build folder of a workspace or package.")
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
def clean(pkg_name):
    if pkg_name:
        pkg_list = [pkg_name]
    else:
        ws = Workspace()
        pkg_list = ws.get_catkin_package_names()
    
    for pkg in pkg_list:
        _, _, package_doxygen_output_dir = check_paths_(pkg_name)
        if os.path.exists(package_doxygen_output_dir):
            shutil.rmtree(package_doxygen_output_dir)

def build_(ws, pkg_name, verbose=None):
    # prepare build paths
    package_src_dir, package_build_dir, package_doxygen_output_dir = check_paths_(pkg_name)

    doxygen_template_filename = os.path.abspath(os.path.join(self_dir, "templates/Doxygen"))

    if not os.path.exists(package_doxygen_output_dir):
        os.makedirs(package_doxygen_output_dir)

    # generate doxygen configuration file
    config = dict()
    config["PROJECT_NAME"] = "\"" + pkg_name + "\""
    config["OUTPUT_DIRECTORY"] = "\"" + package_doxygen_output_dir + "\""
    
    tag_file_name = os.path.abspath(os.path.join(package_doxygen_output_dir, pkg_name + ".tag"))
    config["GENERATE_TAGFILE"] = "\"" + tag_file_name + "\""    
    
    # determine all dependent packages from workspace and add the tag files
    tag_files = list()
    for dep_package, _ in get_dep_packages_in_workspace(ws, pkg_name):
        _, _, dep_package_doxygen_output_dir = check_paths_(dep_package)
        dep_tag_file_name = os.path.abspath(os.path.join(dep_package_doxygen_output_dir, dep_package + ".tag"))
        tag_output_file_name = os.path.abspath(os.path.join(dep_package_doxygen_output_dir, "html"))

        tag_files.append('"{}"="{}"'.format(dep_tag_file_name, tag_output_file_name))
        
    config["TAGFILES"] = " ".join(tag_files)
    
    # configure search engine
    port = 8213
    config["SEARCHENGINE_URL"] = "http://localhost:{}/cgi-bin/doxysearch.cgi".format(port)
    #config["EXTERNAL_SEARCH_ID"] = pkg_name
    
    # Set the input folders. Only add those which are 
    input_folders = ["doc", "include", "src"]
    input_folders = ['"{}"'.format(f) for f in input_folders if os.path.isdir(os.path.join(package_src_dir, f))]
    config["INPUT"] = " ".join(input_folders)
    
    # Add quite if not verbose
    if not verbose:
        config["QUIET"] = "YES"
    
    warn_logfile_name = None        
    try:
        # add warn logfile
        warn_logfile_name = tempfile.NamedTemporaryFile(delete=False).name
        
        config["WARN_LOGFILE"] = '"{}"'.format(warn_logfile_name)

        # Add include to user defined doxygen file
        user_doxyfile = os.path.join(package_src_dir, "Doxyfile")
        if os.path.isfile(user_doxyfile):
            additional_doxygen_config += "@INCLUDE = \"" + user_doxyfile + "\"\n"
            
        # generate config
        additional_doxygen_config = "\n".join(["{0} = {1}".format(k, v) for k, v in config.items()])

        # build
        with tempfile.NamedTemporaryFile() as doxyfile:
            # read standard doxygen file
            with open(doxygen_template_filename, "rb") as f:
                doxyfile.write(f.read())

            # read generated project specific doxygen file
            doxyfile.write(additional_doxygen_config)
            doxyfile.flush()
            
            print(additional_doxygen_config)

            # run doxygen
            os.chdir(package_src_dir)
            subprocess.check_call(["doxygen", doxyfile.name])
            
        # output warn log file if not empty
        with open(warn_logfile_name, "r") as f:
            warn_log = f.read().rstrip("\n")
            if len(warn_log) > 0:
                click.secho(warn_log, fg="yellow")
    finally:
        if os.path.isfile(warn_logfile_name):
            os.remove(warn_logfile_name)

def build_workspace_doc(ws):
    pkg_list = ws.get_catkin_packages()
    
    ws_doc = ["\mainpage"]
    
    for pkg_name in sorted(pkg_list.iterkeys()):
        pkg = pkg_list[pkg_name]
        
        ws_doc.append('<a href=\"http://www.google.de\"><b>' + pkg_name + '</b></a>')
        ws_doc.append("\par")
        ws_doc.append("\parblock")
        ws_doc.append(pkg.description)
        ws_doc.append("")
        ws_doc.append('<table border="0">')
        ws_doc.append("<tr><td>Version</td>" + "<td>&nbsp;</td>" + "<td>" + pkg.version + "</td></tr>")
        
        ws_doc += generate_multi_entry("Author", ["{} ({})".format(f.name, f.email) for f in pkg.authors])        
        ws_doc += generate_multi_entry("Maintainer", ["{} ({})".format(f.name, f.email) for f in pkg.maintainers])
        ws_doc += generate_multi_entry("License", pkg.licenses)

        ws_doc.append("</table>")
        ws_doc.append("\endparblock")
        
    ws_doc_str = ""
    for ws_doc_entry in ws_doc:
        ws_doc_str += "{}\n".format(ws_doc_entry)
        
    with open("/home/beck/tmp/doxygen/output.md", "w+") as f:
        f.write(ws_doc_str)
    
    
def generate_multi_entry(heading, entries):
    doc = list()
    is_first = True
    for entry in entries:
        doc_str = "<tr><td>"
        if is_first:
            doc_str += heading
            is_first = False
            
        doc_str += "</td>" + "<td>&nbsp;</td>" + "<td>" + entry + "</td></tr>"
        doc.append(doc_str)
        
    return doc

    

def get_dep_packages_in_workspace(ws, pkg_name):
    """Returns all packages which depends from pkg_name which are also in the current workspace"""
    package_deps = ws.get_dependencies(pkg_name)[pkg_name]
    ws_packages = ws.get_catkin_packages()
    
    return [(p, ws_packages[p]) for p in package_deps if p in ws_packages]

def check_paths_(pkg_name):
    if pkg_name not in suggestions:
        click.echo("Package '{}' does not exist inside this workspace.".format(pkg_name))
        sys.exit()
    package_src_dir = subprocess.check_output(["catkin", "locate", "--src", pkg_name], universal_newlines=True).rstrip(
        "\n")
    package_build_dir = subprocess.check_output(["catkin", "locate", "--build", pkg_name],
                                                universal_newlines=True).rstrip("\n")
    package_doxygen_output_dir = os.path.join(package_build_dir, "doxygen_doc")

    return package_src_dir, package_build_dir, package_doxygen_output_dir

