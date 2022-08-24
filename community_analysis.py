import networkx as nx
import pygrank as pg

import sso
from importer import dependencies
from tqdm import tqdm
import math

#repo = "https://github.com/sai-pullabhotla/jftp"
repo = "https://github.com/apache/logging-log4j1"
#repo = "https://github.com/PhilJay/MPAndroidChart"
#repo = "https://github.com/greenrobot/EventBus"
#repo = "https://github.com/airbnb/lottie-android"

#algorithm = pg.AbsorbingWalks(0.5, max_iters=10000)
algorithm = pg.PageRank(0.9, max_iters=1000) >> sso.StochasticSeedOversampling()
graph = nx.Graph(dependencies(repo, package="main."))
package_names = set(".".join(node.split(".")[:-1]) for node in graph if "." in node)
packages = {package: [node for node in graph if package in node] for package in package_names}
packages = {k: v for k, v in packages.items() if len(v) > 5}
train, test = pg.split(packages, 3)
test_nodes = graph# [v for t in test.values() for v in t]

print(graph)

ranks = [algorithm(graph, v) for v in tqdm(list(train.values()))]
options = list(range(len(train)))
found_set = [list() for _ in train]
for v in test_nodes:
    found_set[max(options, key=lambda i:ranks[i][v])].append(v)

f1s = list()
conds = list()
for train_part, test_part, found in zip(train.values(), test.values(), found_set):
    if len(found) <= 3:
        continue
    ppv = pg.PPV(test_part, exclude=train_part)(pg.to_signal(graph, found))
    tpr = pg.TPR(test_part, exclude=train_part)(pg.to_signal(graph, found))
    cond = pg.Conductance()(pg.to_signal(graph, found))
    if math.isinf(cond):
        pass  #print(tpr, ppv, len(found), len(graph))
    else:
        conds.append(cond)
    f1s.append(0 if ppv+tpr == 0 else ppv*tpr*2./(ppv+tpr))
print(f"F1 {sum(f1s)/len(f1s):.3f}\t Cond {sum(conds)/len(conds)}")
