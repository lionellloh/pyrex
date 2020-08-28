import ast
import sys
import re
import os
import json
import importlib
from collections import defaultdict

from platform import python_version
from pypi_simple import PyPISimple
from piptools.scripts.compile import cli
from stdlib_list import stdlib_list
from wcmatch import wcmatch


def get_python_filenames(abs_path: str) -> list:
    """:arg
    path_arg: absolute directory of the code base
    return a list of paths that are organic to the code base
    """
    # TODO: try not to hardcode this deny list 'site-packages | node_modules'
    paths = wcmatch.WcMatch(abs_path, "*.py", "site-packages|node_modules", flags=wcmatch.RECURSIVE).match()

    return paths


def get_builtin_libs(python_version: str) -> set:
    assert (len(python_version) == 3 and float(python_version)), \
        "python_version must be in the form of '2.7'. Do not include the minor version."
    assert 2.6 <= float(python_version) <= 3.9, "python_version must be >= 2.6 and <= 3.9"
    top_level_libs = [lib.split(".")[0] for lib in stdlib_list(python_version)]

    return set(top_level_libs)


def flatten_nested_lst(nested_lst: list) -> list:
    ret = []
    for lst in nested_lst:
        ret.extend(lst)

    return ret

def apply_mapping(import_list:list, mapping_dict:dict) -> list:
    pip_pkg_list = [mapping_dict.get(imp, imp) for imp in import_list]

    return pip_pkg_list


def generate_requirements_file(import_mapping: dict, dest_file: str, code_dir_abs_path: str, mapping_dict:dict):
    if not os.path.exists(dest_file):
        with open(dest_file, 'w'):
            pass
    sys.path.insert(0, code_dir_abs_path)
    print(import_mapping)
    print(sys.path, end="\n\n")
    local_import_set = set()
    faulty_imports = set()
    import_list = flatten_nested_lst(list(import_mapping.values()))
    # normalize api.utils -> api and then remove duplicates
    import_set = set([imp.split(".")[0] for imp in import_list])
    print(import_set, end="\n\n")

    for dir, imps in import_mapping.items():
        print(dir)
        # insert in the path so python will prioritise the search accordingly
        sys.path.insert(0, dir)
        for imp in imps:
            top_level_imp = imp.split(".")[0]
            module_spec = importlib.util.find_spec(top_level_imp)
            if not module_spec:
                print("Faulty", top_level_imp, module_spec)
                faulty_imports.add(top_level_imp)
                continue

            print(module_spec)
            # Local import: found in origin
            if module_spec.origin and module_spec.origin[:len(code_dir_abs_path)] == code_dir_abs_path:
            # if module_spec.origin:
                print("origin", module_spec.origin, "|", code_dir_abs_path)
                local_import_set.add(imp)

            # Local import: found in submodule_search_locations
            elif module_spec.submodule_search_locations:
                for search_loc in module_spec.submodule_search_locations:
                    print(search_loc)
                    if search_loc[:len(code_dir_abs_path)] == code_dir_abs_path:
                        local_import_set.add(imp)

    print(sys.path, end ="\n\n")
    print("Faulty imports", faulty_imports)
    print("Local imports", local_import_set)
    import_list = list(import_set - local_import_set - faulty_imports)
    vers = ".".join(python_version().split(".")[:-1])
    builtin_lst = get_builtin_libs(vers)
    non_builtin_lst = list(set(import_list).difference(builtin_lst))

    client = PyPISimple()
    pip_package_list = sorted([pkg for pkg in non_builtin_lst if client.get_project_files(pkg) != []])
    pip_package_list = apply_mapping(pip_package_list, mapping_dict)

    with open(dest_file, 'w') as f:
        for pkg in pip_package_list:
            f.write(f"{pkg}\n")

    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

    # Need to change the args before running pip-compile
    sys.argv = ["", dest_file]
    print(pip_package_list)
    print("Generating dependencies from top-level imports...")
    cli()


def main():
    assert len(sys.argv) == 3, "[USAGE]: Ensure you provide 2 arguments " \
                               "<directory of codebase> <filepath for requirements>"

    # Remove 1th element
    if len(sys.path) >= 3:
        sys.path = sys.path[2:]

    else:
        sys.path = []


    if not os.path.isabs(sys.argv[1]):
        abs_path = os.path.abspath(sys.argv[1])
    else:
        abs_path = sys.argv[1]

    # Loading mappings
    with open("pip_import_names.json", 'r') as f:
        mapping_dict = json.load(f)

    requirements_file = sys.argv[2]
    filenames = get_python_filenames(abs_path)
    analyzer = Analyzer()

    for filename in filenames:
        print(f"Analyzing File: {filename}")
        with open(filename, "r") as source:
            tree = ast.parse(source.read())
            analyzer.visit(tree)
            dir = "/".join(filename.split("/")[:-1])
            analyzer.store_and_empty(dir)

    import_mapping = analyzer.report()

    generate_requirements_file(import_mapping=import_mapping, dest_file=requirements_file, code_dir_abs_path=abs_path, mapping_dict=mapping_dict)


"""
Check docs at https://greentreesnakes.readthedocs.io/en/latest/nodes.html
to understand node object attributes. 
"""


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.import_mapping = defaultdict(list)
        self.import_cache = []

    def visit_Import(self, node):
        for alias in node.names:
            self.import_cache.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.import_cache.append(node.module)
        self.generic_visit(node)

    def empty_import_cache(self):
        self.import_cache = []

    def store_and_empty(self, dir: str):
        self.import_mapping[dir].extend(self.import_cache)
        self.empty_import_cache()

    def report(self):
        return self.import_mapping


if __name__ == "__main__":
    main()
