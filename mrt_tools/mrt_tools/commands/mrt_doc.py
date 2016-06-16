from mrt_tools.Workspace import Workspace
from mrt_tools.utilities import *

import catkin_pkg.topological_order

import os
import subprocess
import tempfile
import webbrowser
import hashlib
import time

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
@click.option("--workspace-docs", "-w", is_flag=True, default=True,
              help="Build a documentation page with combines all documentation in this workspace")
def build(pkg_name, this, no_deps, verbose, workspace_docs):
    start = time.time()
    ws = Workspace()

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
            pkg_list.update(get_dep_packages_in_workspace_(ws, pkg_name))
            
        is_build_workspace_doc = False

    # order topologically to get the build order right
    pkg_list = catkin_pkg.topological_order.topological_order_packages(pkg_list)

    # output build summary
    end = time.time()
    click.secho("[doc build] Found '{}' packages in {:.1f} seconds.".format(len(pkg_list), end - start))

    # build packages
    for pkg, _ in pkg_list:
        output_start_status_(pkg)
        build_(ws, pkg, verbose)
        output_finished_states_(pkg)

    # build workspace docs
    if workspace_docs:
        click.echo("[doc build] Build workspace documentation")
        output_start_status_("workspace_doc")
        build_workspace_doc_(ws)
        output_finished_states_("workspace_doc")


@main.command(short_help="Shows the documentation of a package.",
              help="Shows the documentation of a package. If the documentation is not found, it will be generated.")
@click.argument("pkg_name", type=click.STRING, required=False, autocompletion=suggestions)
def show(pkg_name):
    if pkg_name:
        index_file = get_html_index_file_path_(pkg_name)
    else:
        ws = Workspace()
        doc_folder = get_workspace_doc_folder_(ws)
        index_file = os.path.join(doc_folder, "html", "index.html")

    if not os.path.isfile(index_file):
        build_(ws, pkg_name)

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
        _, _, package_doxygen_output_dir = check_paths_(pkg)
        if os.path.exists(package_doxygen_output_dir):
            shutil.rmtree(package_doxygen_output_dir)

    if not pkg_name:
        doc_folder = get_workspace_doc_folder_(ws)
        if os.path.exists(doc_folder):
            shutil.rmtree(doc_folder)


def build_(ws, pkg_name, verbose=None):
    # prepare build paths
    package_src_dir, package_build_dir, package_doxygen_output_dir = check_paths_(pkg_name)

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
    for dep_package, _ in get_dep_packages_in_workspace_(ws, pkg_name):
        tag_files.append(get_tag_file_config_entry_(dep_package))
        
    config["TAGFILES"] = " ".join(tag_files)
    
    # configure search engine (not working correctly with local http python server)
    #port = 8213
    #config["SEARCHENGINE_URL"] = "http://localhost:{}/cgi-bin/doxysearch.cgi".format(port)
    #config["EXTERNAL_SEARCH_ID"] = pkg_name
    
    # Set the input folders. Only add those which are 
    input_folders = ["README.md", "doc", "include", "src"]
    input_folders = ['"{}"'.format(f) for f in input_folders if os.path.exists(os.path.join(package_src_dir, f))]
    config["INPUT"] = " ".join(input_folders)
    
    if os.path.exists(os.path.join(package_src_dir, "doc")):
        config["IMAGE_PATH"] = "doc"
    
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
            config["@INCLUDE"] = '"{}"'.format(user_doxyfile)

        # build
        run_doxygen_(config, package_src_dir)

        # output warn log file if not empty
        with open(warn_logfile_name, "r") as f:
            warn_log = f.read().rstrip("\n")
            if len(warn_log) > 0:
                click.secho(warn_log, fg="yellow")
    finally:
        if os.path.isfile(warn_logfile_name):
            os.remove(warn_logfile_name)


def run_doxygen_(config, package_src_dir):
    # generate config
    additional_doxygen_config = "\n".join(["{0} = {1}".format(k, v) for k, v in config.items()])

    # build
    with tempfile.NamedTemporaryFile() as doxyfile:
        # read standard doxygen file
        with open(get_doxygen_template_filename_(), "rb") as f:
            doxyfile.write(f.read())

        # read generated project specific doxygen file
        doxyfile.write(additional_doxygen_config)
        doxyfile.flush()

        # run doxygen
        os.chdir(package_src_dir)
        subprocess.check_call(["doxygen", doxyfile.name])


def build_workspace_doc_(ws):
    pkg_list = ws.get_catkin_packages()

    # create doc folder
    doc_folder = get_workspace_doc_folder_(ws)

    if not os.path.isdir(doc_folder):
        os.makedirs(doc_folder)

    # generate main page and tag file list
    ws_doc = list()
    tag_files = list()
    ws_doc.append("\mainpage")
    
    for pkg_name in sorted(pkg_list.iterkeys()):
        pkg = pkg_list[pkg_name]

        tag_file_name = get_tage_file_name_(pkg_name)
        if not os.path.isfile(tag_file_name):
            continue
        
        ws_doc.append('<a href=\"{}\"><b>{}</b></a>'.format(get_html_index_file_path_(pkg_name), pkg_name))
        ws_doc.append("\par")
        ws_doc.append("\parblock")
        ws_doc.append(pkg.description)
        ws_doc.append("")
        ws_doc.append('<table border="0">')
        ws_doc.append("<tr><td>Version</td>" + "<td>&nbsp;</td>" + "<td>" + pkg.version + "</td></tr>")
        
        ws_doc += gen_multi_entry_table_("Author", ["{} ({})".format(f.name, f.email) for f in pkg.authors])
        ws_doc += gen_multi_entry_table_("Maintainer", ["{} ({})".format(f.name, f.email) for f in pkg.maintainers])
        ws_doc += gen_multi_entry_table_("License", pkg.licenses)

        ws_doc.append("</table>")
        ws_doc.append("\endparblock")

        tag_files.append(get_tag_file_config_entry_(pkg_name))
        
    ws_doc_str = ""
    for ws_doc_entry in ws_doc:
        ws_doc_str += "{}\n".format(ws_doc_entry)

    main_file_path = os.path.join(doc_folder, "main.md")
    with open(main_file_path, "w+") as f:
        f.write(ws_doc_str)

    # generate config file
    config = dict()

    config["PROJECT_NAME"] = '"Workspace {}"'.format(ws.get_workspace_name())
    config["OUTPUT_DIRECTORY"] = doc_folder
    config["INPUT"] = main_file_path
    config["QUIET"] = "YES"
    config["WARNINGS"] = "NO"
    config["TAGFILES"] = " ".join(tag_files)
    config["AUTOLINK_SUPPORT"] = "NO"

    # build documentation
    run_doxygen_(config, doc_folder)
    
    
def gen_multi_entry_table_(heading, entries):
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


def get_html_index_file_path_(pkg_name):
    _, _, dep_package_doxygen_output_dir = check_paths_(pkg_name)
    return os.path.abspath(os.path.join(dep_package_doxygen_output_dir, "html", "index.html"))


def get_tage_file_name_(pkg_name):
    _, _, package_doxygen_output_dir = check_paths_(pkg_name)
    tag_file_name = os.path.abspath(os.path.join(package_doxygen_output_dir, pkg_name + ".tag"))
    return tag_file_name


def get_tag_file_config_entry_(pkg_name):
    _, _, package_doxygen_output_dir = check_paths_(pkg_name)
    tag_file_name = os.path.abspath(os.path.join(package_doxygen_output_dir, pkg_name + ".tag"))
    tag_output_file_name = os.path.abspath(os.path.join(package_doxygen_output_dir, "html"))

    return '"{}"="{}"'.format(tag_file_name, tag_output_file_name)


def get_dep_packages_in_workspace_(ws, pkg_name):
    """Returns all packages which depends from pkg_name which are also in the current workspace"""
    package_deps = ws.get_dependencies(pkg_name)[pkg_name]
    ws_packages = ws.get_catkin_packages()
    
    return [(p, ws_packages[p]) for p in package_deps if p in ws_packages]


def get_workspace_doc_folder_(ws):
    doc_folder_name = "workspace_doc_" + str(hashlib.sha224(ws.get_root()).hexdigest()[:10])
    doc_folder = subprocess.check_output(["catkin", "locate", "--build"], universal_newlines=True).rstrip("\n")
    doc_folder = os.path.join(doc_folder, doc_folder_name)
    return doc_folder


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


def get_doxygen_template_filename_():
    return os.path.abspath(os.path.join(self_dir, "templates/Doxygen"))


def output_start_status_(pkg_name):
    click.echo("Starting  " + click.style(">>>", fg="green", bold=True) + " " +
               click.style(pkg_name, fg="cyan", bold=True))


def output_finished_states_(pkg_name):
    click.echo(click.style("Finished  ", fg="black", bold=True) + click.style("<<<", fg="green") + " " +
               click.style(pkg_name, fg="cyan"))

