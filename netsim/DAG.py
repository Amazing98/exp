import networkx as nx
from random import randint
import json

from networkx.linalg import graphmatrix


def random_dag(nodes, edges):
    """Generate a random Directed Acyclic Graph (DAG) with a given number of nodes and edges."""
    G = nx.DiGraph()
    for i in range(nodes):
        G.add_node(i)
    while edges > 0:
        a = randint(0, nodes-1)
        b = a
        while b == a:
            b = randint(0, nodes-1)
        G.add_edge(a, b)
        if nx.is_directed_acyclic_graph(G):
            edges -= 1
        else:
            # we closed a loop!
            G.remove_edge(a, b)

    first_node = nodes
    last_node = nodes + 1
    G.add_node(first_node)
    G.add_node(last_node)

    for node, in_edge in dict(G.in_degree()).items():
        if in_edge == 0:
            if node == first_node or node == last_node:
                continue
            G.add_edge(first_node, node)

    for node, out_edge in dict(G.out_degree()).items():
        if out_edge == 0:
            if node == first_node or node == last_node:
                continue
            G.add_edge(node, last_node)

    return G


graph = []
for i in range(500):
    edge = randint(20, 40)
    node = randint(8, 20)
    G = random_dag(node, edge)
    graph.append(G)

print(len(graph))

g_json = {"graphs": []}
for G in graph:
    g_json["graphs"].append(nx.adjacency_data(G))
    # print(list(nx.topological_sort(G)))
    # print(nx.adjacency_data(G))
with open("./graph_full3.json", "w") as f:

    json.dump(g_json, f)
