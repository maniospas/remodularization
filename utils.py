import pygrank as pg
from pyvis.network import Network


def print_top(scores, top=10):
    for item in sorted(list(scores.items()), key=lambda item: -item[1])[:top]:
        print(*item)


def show_signal(signal, train=None):
    graph = signal.graph
    #signal = pg.Normalize()(pg.Ordinals()(pg.Ordinals()(signal)))
    #signal = pg.Normalize()(signal)

    def rgb_to_hex(rgb):
        return '#%02x%02x%02x' % rgb

    for member in signal:
        if train is not None and train[member] != 0:
            val = int(255*signal[member])
            graph.nodes[member]['value'] = 2
            graph.nodes[member]['color'] = rgb_to_hex((255, 0, 0))
            graph.nodes[member]['color'] = rgb_to_hex((255, 255-val, 255-val))
        else:
            val = int(255*signal[member])
            graph.nodes[member]['value'] = 1
            graph.nodes[member]['color'] = rgb_to_hex((255, 255-val, 255-val))

    nt = Network('1000px', '1000px')
    nt.from_nx(graph)
    nt.show('nx.html')
