#!/usr/bin/python
__author__ = "Omer Sahin Tas"
__date__ = "10.09.2015"

import pydot

def create_node(node_name, graph):
    node = pydot.Node(node_name, style="filled", fillcolor="red")
    graph.add_node(node)
    return node, graph


def get_node(node_name, graph):
    """creates or returns (if the node already exists) the node"""

    # check all of the graph nodes
    for node in graph.get_nodes():
        if node_name == node.get_name():
            return node, graph
                
    return create_node(node_name, graph)


def add_nodes(deps_dict, graph, root_node):

    root_node, graph = get_node(deps_dict.keys()[0], graph)

    for v in deps_dict.values()[0]:

        # if the list element is not a dict
        if type(v) != dict:
            node, graph = get_node(v, graph)
            graph = add_edge(graph, root_node, node)

        # if the element is a dict, call recursion
        else:
            node, graph = get_node(v.keys()[0], graph)
            graph = add_edge(graph, root_node, node)
            add_nodes(v, graph, node)


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

    

def plot_main(deps, pkg_name):
    """main func for plot"""
    
    # create a graph object
    graph = pydot.Dot(graph_type='digraph')
    
    # create the root node
    root_node, graph = get_node(pkg_name, graph)
    
    # add nodes and edges to the root node
    for dep in deps:
        
        # if the list element is a list
        if type(dep) != dict:
            node, graph = create_node(dep, graph)
            graph.add_edge(pydot.Edge(root_node, node))
            
        # if the element is a dict
        else:
            # create the node and add the edge 
            node, graph = create_node(dep.keys()[0], graph)
            graph.add_edge(pydot.Edge(root_node, node))
            
            # call 'add_nodes' for recursion
            add_nodes(dep, graph, root_node)
            
    
    # save the figure
    graph.write_png("deps_" + pkg_name + ".png")

    print "figure saved!" 
