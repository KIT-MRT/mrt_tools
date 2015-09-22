from mrt_tools.base import Workspace
from PIL import Image
import pydot
import click
import sys
import os


@click.command()
@click.argument("pkg_name", type=click.STRING, required=False)
def main(pkg_name):
    """ Visualize dependencies of catkin packages."""
    ws = Workspace()
    pkg_list = ws.get_catkin_package_names()
    ws.cd_root()
    if pkg_name:
        if pkg_name not in pkg_list:
            print("Package not found, cant create graph")
            sys.exit(1)
        pkg_list = [pkg_name]
    else:
        if click.confirm("Create dependency graph for every package?"):
            for pkg_name in pkg_list:
                deps = [ws.get_dependencies(pkg_name, deep=True)]
                graph = Digraph(deps)
                graph.plot(pkg_name, show=False)
        if click.confirm("Create complete dependency graph for workspace?", abort=True):
            pkg_name = os.path.basename(os.getcwd())

    deps = [ws.get_dependencies(pkg_name, deep=True) for pkg_name in pkg_list]

    graph = Digraph(deps)
    graph.plot(pkg_name)


# TODO Create interactive plots
# TODO Create centric plot, when complete dependency graph is generated


class Digraph:
    def __init__(self, deps):
        # create a graph object
        self.graph = pydot.Dot(graph_type='digraph')
        self.nodes = None
        # add nodes and edges to the root node
        for dep in deps:
            self.add_nodes(dep)

    def create_node(self, name, isleaf=False):
        if isleaf:
            node = pydot.Node(name, style="filled", fillcolor="red")
        else:
            node = pydot.Node(name, style="filled", fillcolor="green")
        self.graph.add_node(node)
        return node

    def get_node(self, name, isleaf=False):
        """creates or returns (if the node already exists) the node"""

        # check all of the graph nodes
        for node in self.graph.get_nodes():
            if name == node.get_name():
                return node

        return self.create_node(name, isleaf=isleaf)

    def add_nodes(self, deps_dict):
        """Add several nodes"""
        root_node = self.get_node(deps_dict.keys()[0])

        for v in deps_dict.values()[0]:

            # if the list element is not a dict
            if type(v) != dict:
                node = self.get_node(v, isleaf=True)
                self.add_edge(root_node, node)

            # if the element is a dict, call recursion
            else:
                node = self.get_node(v.keys()[0], isleaf=False)
                self.add_edge(root_node, node)
                self.add_nodes(v)

    def add_edge(self, a, b):
        """checks if the edge already exists, if not, creates one from a2b"""

        for edge_obj in self.graph.get_edge_list():
            if a.get_name() in edge_obj.obj_dict["points"] and \
                            b.get_name() in edge_obj.obj_dict["points"]:
                break
        else:
            # such an edge doesn't exist. create it
            self.graph.add_edge(pydot.Edge(a, b))

    def plot(self, pkg_name, show=True):
        """plot a directed graph with one root node"""
        if not os.path.exists("pics"):
            os.mkdir("pics")
        filename = "pics/deps_{0}.png".format(pkg_name)
        self.graph.write_png(filename)
        if show:
            image = Image.open(filename)
            image.show()
        click.echo("Image written to: " + os.getcwd() + "/" + filename)
