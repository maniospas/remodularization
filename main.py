import importer
import utils
import pygrank as pg
import networkx as nx
import depytrace as dp


graph = importer.dependencies("C:\\Users\\manio\\Documents\\eclipse\\KingClashers")
graph = nx.DiGraph(graph)
print(f"{len(graph)} nodes, {graph.number_of_edges()} edges")
artifact = 'main'
print(list(graph))

trace = dp.Core()(graph, artifact)
extendedTrace = nx.DiGraph([u, v] for u in list(trace) for v in graph._adj[u])
extendedNodes = set(extendedTrace)
for u,v in graph.edges():
    if u in extendedNodes and v in extendedNodes:
        extendedTrace.add_edge(u, v)

utils.show_signal(pg.to_signal(extendedTrace, {v: 1 for v in trace}),
                  pg.to_signal(extendedTrace, {artifact: 1}))