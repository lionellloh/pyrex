import ast
from collections import defaultdict

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