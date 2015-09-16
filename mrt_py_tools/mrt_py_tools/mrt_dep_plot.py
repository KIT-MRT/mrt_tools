#!/usr/bin/python
from mrt_py_tools import mrt_base_tools
from PIL import Image
import click
import pydot
import os

__author__ = "Omer Sahin Tas"
__date__ = "10.09.2015"



def create_node(node_name, graph, isleaf=False):
    if isleaf:
        node = pydot.Node(node_name, style="filled", fillcolor="red")
    else:
        node = pydot.Node(node_name, style="filled", fillcolor="green")
    graph.add_node(node)
    return node, graph


def get_node(node_name, graph, isleaf=False):
    """creates or returns (if the node already exists) the node"""

    # check all of the graph nodes
    for node in graph.get_nodes():
        if node_name == node.get_name():
            return node, graph

    return create_node(node_name, graph, isleaf=isleaf)


def add_nodes(deps_dict, graph):
    root_node, graph = get_node(deps_dict.keys()[0], graph)

    for v in deps_dict.values()[0]:

        # if the list element is not a dict
        if type(v) != dict:
            node, graph = get_node(v, graph, isleaf=True)
            graph = add_edge(graph, root_node, node)

        # if the element is a dict, call recursion
        else:
            node, graph = get_node(v.keys()[0], graph, isleaf=False)
            graph = add_edge(graph, root_node, node)
            add_nodes(v, graph)


def add_edge(graph, a, b):
    """checks if the edge already exists, if not, creates one from a2b"""

    for edge_obj in graph.get_edge_list():
        if a.get_name() in edge_obj.obj_dict["points"] and \
                        b.get_name() in edge_obj.obj_dict["points"]:
            break

    else:
        # such an edge doesn't exist. create it
        graph.add_edge(pydot.Edge(a, b))

    return graph


def plot_digraph(deps, pkg_name, show=True):
    """plot a directed graph with one root node"""

    # create a graph object
    graph = pydot.Dot(graph_type='digraph')

    # add nodes and edges to the root node
    for dep in deps:
        add_nodes(dep, graph)

    # save the figure
    mrt_base_tools.change_to_workspace_root_folder()
    if not os.path.exists("pics"):
        os.mkdir("pics")
    graph.write_png("pics/deps_" + pkg_name + ".png")
    if show:
        image = Image.open("pics/deps_" + pkg_name + ".png")
        image.show()
    click.echo("Image written to: "+os.getcwd()+"/pics/deps_" + pkg_name + ".png")
