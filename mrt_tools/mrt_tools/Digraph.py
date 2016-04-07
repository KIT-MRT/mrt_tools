import subprocess
import click
import pydot
import os


class Digraph(object):
    def __init__(self, deps, no_leafs=False):
        # create a graph object
        self.graph = pydot.Dot(graph_type='digraph')
        self.nodes = None
        self.no_leafs = no_leafs
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
        """creates or returns (if the node already exists) the node
        :param isleaf: Defines wether this Node has further children
        :param name: Name of node
        """

        # check all of the graph nodes
        for node in self.graph.get_nodes():
            if name == node.get_name():
                return node

        return self.create_node(name, isleaf=isleaf)

    def add_nodes(self, deps_dict):
        """Add several nodes
        :param deps_dict: Dictionary of Dependencies
        """
        root_node = self.get_node(list(deps_dict.keys())[0])

        for v in list(deps_dict.values())[0]:

            # if the list element is not a dict
            if type(v) != dict:
                if not self.no_leafs:
                    node = self.get_node(v, isleaf=True)
                    self.add_edge(root_node, node)

            # if the element is a dict, call recursion
            else:
                node = self.get_node(list(v.keys())[0], isleaf=False)
                self.add_edge(root_node, node)
                self.add_nodes(v)

    def add_edge(self, a, b):
        """checks if the edge already exists, if not, creates one from a2b
        :param a: Node a
        :param b: Node b
        """

        for edge_obj in self.graph.get_edge_list():
            if a.get_name() in edge_obj.obj_dict["points"] and \
                            b.get_name() in edge_obj.obj_dict["points"]:
                break
        else:
            # such an edge doesn't exist. create it
            self.graph.add_edge(pydot.Edge(a, b))

    def plot(self, pkg_name, show=True):
        """plot a directed graph with one root node
        :param pkg_name: Name of the graph, which to plot
        :param show: Open image after creation?
        """
        if not os.path.exists("pics"):
            os.mkdir("pics")
        filename = os.path.join(os.getcwd(), "pics/deps_{0}.png".format(pkg_name))
        self.graph.write_png(filename)
        if show:
            subprocess.call(["xdg-open", filename])
        click.echo("Image written to: " + os.getcwd() + "/" + filename)
