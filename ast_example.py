import ast
import sys
import re
import os
import importlib

from platform import python_version
from pypi_simple import PyPISimple
from piptools.scripts.compile import cli
from stdlib_list import stdlib_list
from wcmatch import wcmatch

def get_python_files(abs_path: str) -> list:
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


def generate_requirements_file(import_list: list, dest_file: str, code_dir_abs_path: str):
    if not os.path.exists(dest_file):
        with open(dest_file, 'w'):
            pass
    # insert in the path so python will prioritise the search accordingly
    sys.path.insert(0, code_dir_abs_path)
    print(sys.path, end = "\n\n")
    local_import_set = set()
    faulty_imports = set()
    # normalize api.utils -> api and then remove duplicates
    import_set = set([imp.split(".")[0] for imp in import_list])
    print(import_set, end = "\n\n")
    for imp in import_set:
        module_spec = importlib.util.find_spec(imp)
        # What happens if u run this in a virtualenv that does not contain the package?
        if module_spec is None or module_spec.origin is None:
            faulty_imports.add(imp)
            continue
        print(module_spec)
        if module_spec.origin[:len(code_dir_abs_path)] == code_dir_abs_path:
            local_import_set.add(imp)

    import_list = list(import_set - local_import_set - faulty_imports)
    # print("IMPORT LIST", import_list)
    # print("FAULTY IMPORTS", faulty_imports)
    vers = ".".join(python_version().split(".")[:-1])
    builtin_lst = get_builtin_libs(vers)
    non_builtin_lst = list(set(import_list).difference(builtin_lst))

    client = PyPISimple()
    pip_package_list = sorted([pkg for pkg in non_builtin_lst if client.get_project_files(pkg) != []])
    pip_package_list = [pkg.replace("_", "-") for pkg in pip_package_list]
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

    if not os.path.isabs(sys.argv[1]):
        abs_path = os.path.abspath(sys.argv[1])
    else:
        abs_path = sys.argv[1]

    requirements_file = sys.argv[2]
    files = get_python_files(abs_path)
    analyzer = Analyzer()

    for file in files:
        print(f"Analyzing File: {file}")
        with open(file, "r") as source:
            tree = ast.parse(source.read())
            analyzer.visit(tree)

    import_list = analyzer.report()

    generate_requirements_file(import_list, requirements_file, abs_path)


"""
Check docs at https://greentreesnakes.readthedocs.io/en/latest/nodes.html
to understand node object attributes. 
"""
class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.imports.append(node.module)
        self.generic_visit(node)

    def report(self):
        return self.imports


if __name__ == "__main__":
    main()