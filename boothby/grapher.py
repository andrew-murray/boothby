import networkx as nx
import matplotlib.pyplot as plt

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
