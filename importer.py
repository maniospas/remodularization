import glob
import os
from git import Repo
import re


def _remove_extension(path):
    if path.endswith(".py"):
        return path[:-3]
    if path.endswith(".java"):
        return path[:-5]
    raise Exception("invalid extension")


def download(root):
    if "https:" in root:
        folder = "data/"+"/".join(root.split("/")[-2:])
        if not os.path.exists(folder):
            print("Downloading...")
            Repo.clone_from(root, folder)
        root = folder
    return root


def calls(root):
    from call_graph import create_predicate_graph
    root = download(root)
    if root[-1] != "/":
        root += "/"
    return create_predicate_graph(root)


def pydependencies(root):
    root = download(root)
    from pycg.pycg import CallGraphGenerator
    from pycg import formats
    from pycg.utils.constants import CALL_GRAPH_OP
    entry_points = [path for path in glob.glob(root + "/**/*.py", recursive=True)]
    cg = CallGraphGenerator(entry_points, root, 10, CALL_GRAPH_OP)
    cg.analyze()
    output = formats.Simple(cg).generate()
    return [(u, v) for u in output for v in output[u]]


def dependencies(root, package="", hierarchical_dependencies=True, autopackage=True):
    root = download(root)
    if autopackage:
        if os.path.exists(root+"/"+root.split("/")[-1]):
            package = package+"."+root.split(".")[-1]
            root = root+"/"+root.split("/")[-1]
        if os.path.exists(root+"/src"):
            #package = package+".src"
            root = root + "/src"
    if root[-1] != "/":
        root += "/"
    imports = list()
    files = set()
    for path in glob.glob(root + '**/*.*', recursive=True):
        if not path.endswith(".py") and not path.endswith(".java"):
            continue
        with open(path, encoding='utf-8') as file:
            path = path[len(root):].replace("/", "\\")
            files.add(path)
            for line in file:
                line = line.strip()
                if "import" in line:
                    line = line.split(" as ")[0]
                    if "from" in line:
                        second = line.split("import ")[-1].strip()
                        if " " in second or "*" in second:
                            continue
                        line = (line.split("import ")[0].split("from")[-1].strip() + "." + second).strip()
                    else:
                        line = line.split("import ")[-1].strip()
                    if " " in line or not line:
                        continue
                    imports.append((path, line))
    import_paths = [_remove_extension(path).replace("\\", ".") for path in files]
    dependencies = list()
    for path, imported in imports:
        if imported.startswith("."):
            imported = ".".join(path.split("\\")[:-1]) + imported
        path = _remove_extension(path).replace("\\", ".")
        for file in import_paths:
            if "ExecuteCommandDlg" in path:
                print(file, imported)
            if file.endswith(imported[:-1]):
                imported = file
                break
        if path.startswith(package) and imported.startswith(package):
            dependencies.append((path.replace(".__init__", ""), imported))

    if hierarchical_dependencies:
        for path in files:
            path = _remove_extension(path).replace("\\", ".")
            splt = path.split(".")
            for i in range(1, len(splt)+1):
                dependencies.append((".".join(splt[:(i-1)]), ".".join(splt[:i])))
    return dependencies
