import re
from ivy import module_descriptor
import logging
import revision_constraint
import networkx as nx
import matplotlib.pyplot as plt

def collect_graph_from_initial_graph(modules):
    g = nx.DiGraph()
    for m in modules.values():
        module_id = m.id
        all_versions = m.versions()
        for ver in all_versions:
            version_id = module_id + "/" + ver
            desc = m.get( ver )
            g.add_node( version_id, desc )
            for dep in desc.dependencies:
                # if we have a fixed dep here,
                # let's put it straight in the graph
                # don't know how to manage non-fixed yet
                if revision_constraint.is_fixed(dep.rev):
                    dep_id = dep.org + "/" + dep.name + "/" + dep.rev
                    g.add_node( dep_id )
                    g.add_edge( version_id, dep_id )
    return g

def collect_graph(filename, nav):
    modules = build_initial_graph(filename, nav)
    return collect_graph_from_initial_graph( modules )

"""
note to self, while these are fine
investigate graph-tool
https://graph-tool.skewed.de/static/doc/index.html
and possibly this udacity course, has fine pictures and I will presume
be simple external libraries, maybe a duff link but I record it
https://www.udacity.com/wiki/creating-network-graphs-with-python
"""

def display_graph(g):
    nx.draw(g, labels = { x : x for x in g } )
    plt.show()

def plot_labels(labels_and_pos):
    for l, pos in labels_and_pos.items():
        # bbox=dict(facecolor='red', alpha=0.5),
        plt.text(
            pos[0],
            pos[1]+8,
            s="\n".join( l.split("/") ),
            bbox=dict(facecolor='blue', alpha=0.5),
            horizontalalignment='center'
        )

def display_tree(g):
    pos = nx.nx_pydot.graphviz_layout(g, prog='dot', with_labels=True)
    # nx.draw(g, pos, labels = { x : x for x in g })
    nx.draw(g, pos)
    plot_labels(pos)
    #
    plt.show()
