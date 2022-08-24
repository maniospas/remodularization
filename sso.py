import pygrank as pg


class StochasticSeedOversampling(pg.Postprocessor):
    def __init__(self, ranker=None):
        super().__init__(ranker)

    def rank(self,
             graph: pg.GraphSignalGraph = None,
             personalization: pg.GraphSignalData = None,
             **kwargs):
        personalization = pg.to_signal(graph, personalization)
        nodes = [v for v in personalization if personalization[v]]
        ret = 0
        for node in nodes:
            epsilon = 1.
            while True:
                ranks = self.ranker(personalization, {v: 1. if v != node else epsilon for v in nodes})
                threshold = min(ranks[v] for v in nodes)
                oversampled = ranks >> pg.Threshold(threshold, inclusive=True)
                if pg.sum(oversampled) != pg.sum(personalization) or epsilon < 0.01:
                    break
                epsilon *= 0.9
            ret = self.ranker(oversampled) + ret
            #if threshold == 1:
            #    break
        return ret
