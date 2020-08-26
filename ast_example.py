import ast
from pprint import pprint
from flask import request
from pypi_simple import PyPISimple
from piptools.scripts.compile import cli
import sys
import re
from platform import python_version
from stdlib_list import stdlib_list
import glob
import os


def get_python_files(abs_path: str) -> list[str]:
    """:arg
    path_arg: absolute directory of the code base
    return a list of paths that are organic to the code base
    """
    dep_paths = "/".join([abs_path, "**/site-packages/**/*.py"])
    all_paths = "/".join([abs_path, "**/*.py"])

    organic_paths = list(set(all_paths) - set(dep_paths))

    return organic_paths


def get_builtin_libs(python_version: str) -> set:
    assert (len(python_version) == 3 and float(python_version)), \
        "python_version must be in the form of '2.7'. Do not include the minor version."
    assert 2.6 <= float(python_version) <= 3.9, "python_version must be >= 2.6 and <= 3.9"
    top_level_libs = [lib.split(".")[0] for lib in stdlib_list(python_version)]

    return set(top_level_libs)


def generate_requirements_file(import_list: list, dest_file):
    vers = ".".join(python_version().split(".")[:-1])
    builtin_lst = get_builtin_libs(vers)
    non_builtin_lst = list(set(import_list).difference(builtin_lst))

    client = PyPISimple()
    pip_package_list = sorted([pkg for pkg in non_builtin_lst if client.get_project_files(pkg) != []])

    with open("requirements.in", 'w') as f:
        for pkg in pip_package_list:
            f.write(f"{pkg}\n")

    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    exit_code = cli()
    os.remove("requirements.in")
    sys.exit(exit_code)

def main():
    assert len(sys.argv) == 3, "[USAGE]: Ensure you provide 2 arguments " \
                               "<directory of codebase> <filepath for requirements>"


    with open("ast_example.py", "r") as source:
        tree = ast.parse(source.read())

    analyzer = Analyzer()
    analyzer.visit(tree)
    import_list = analyzer.report()

    if not os.path.isabs(sys.argv[1]):
        path = os.path.abspath(sys.argv[1])

    generate_requirements_file(import_list, "requirements.txt")


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