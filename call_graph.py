import networkx as nx


def _path2files(path):
    import os
    from glob import glob
    filenames = list()
    pattern = "*.py"
    for found_dir, _, _ in os.walk(path):
        filenames.extend([f for f in glob(os.path.join(found_dir, pattern)) if f])
    return filenames


def _converter(content="default"):
    if content == "default":
        return lambda node: [str(node)]
    elif content == "trace":
        return lambda node: [node.get_name()]
    elif content == "predicates":
        return lambda node: node.get_name().split(".")
    elif content == "name":
        return lambda node: [node.name]
    else:
        raise Exception("Invalid converter content")


def create_pyan_graph(path, keep_undefined=False, content="default"):
    converter = _converter(content)
    from pyAn.analyzer import CallGraphVisitor
    from pyAn.analyzer import Flavor
    visitor = CallGraphVisitor(_path2files(path))
    visited_nodes = [node for name in visitor.nodes for node in visitor.nodes[name] if node.defined or keep_undefined]
    # visited_nodes.sort(key=lambda x: (x.namespace, x.name))
    G = nx.DiGraph()
    modules = {}
    for node in visited_nodes:
        if (node.flavor == Flavor.MODULE or node.flavor == Flavor.CLASS) and node in visitor.defines_edges:
            modules[node] = [cdefined for defined in visitor.defines_edges[node] if defined.defined or keep_undefined
                             for cdefined in converter(defined)] + [cnode for cnode in converter(node)]
        if node in visitor.uses_edges:
            for cnode in converter(node):
                G.add_node(cnode)
            for called in visitor.uses_edges[node]:
                if (called.defined or keep_undefined) and (
                        called.flavor == Flavor.FUNCTION or called.flavor == Flavor.CLASSMETHOD or called.flavor == Flavor.METHOD):
                    for cnode in converter(node):
                        for ccalled in converter(called):
                            G.add_edge(cnode, ccalled)
                            G.add_edge(ccalled, cnode)
    return G, modules


def create_predicate_graph(path):
    import astor
    import ast
    import re

    def _get_function_words(node):
        words = list()
        for line in astor.to_source(node).split('\n'):
            line_text = re.sub(r"\(|\)|\:|\.|\[|\]|\"|\'|\||\\|\{|\}|\=|\+|\-|\*|\/|\%|\.|\,|\<|\>", " ", line)
            words.extend([word for word in line_text.split(' ') if len(word) > 1])
            # words.extend(word.lower() for word in re.findall("[A-Z]*[a-z]+", line))
        return words

    pairs = list()
    function_names = list()
    frequencies = {}
    for path in _path2files(path):
        a = astor.code_to_ast.parse_file(path)
        for node in ast.iter_child_nodes(a):
            if type(node).__name__ == 'ClassDef' and hasattr(node, 'name'):
                for method in ast.iter_child_nodes(node):
                    if hasattr(method, 'name'):
                        method_name = method.name
                        frequencies[method_name] = frequencies.get(method_name, 0) + 1
                        if type(method).__name__ == 'FunctionDef':
                            function_names.append(node.name)
                            pairs.append((node.name, method.name))
                            function_names.append(method_name)
                            for word in _get_function_words(method):
                                pairs.append((method_name, word))
                                frequencies[word] = frequencies.get(word, 0) + 1
            if type(node).__name__ == 'FunctionDef' and hasattr(node, 'name'):
                pairs.append((path.split('\\')[-2].split('.')[-1], node.name))
                function_names.append(path.split('\\')[-2].split('.')[-1])
                function_names.append(node.name)
                frequencies[node.name] = frequencies.get(node.name, 0) + 1
                for word in _get_function_words(node):
                    pairs.append((node.name, word))
                    frequencies[word] = frequencies.get(word, 0) + 1
    pairs = [(node1, node2) for node1, node2 in pairs if "__" not in node1 and "__" not in node2 and
             node1 != node2 and (frequencies.get(node2, 0) > 1 and node2 in function_names)]
    return pairs