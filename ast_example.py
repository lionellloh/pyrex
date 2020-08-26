import ast
from pprint import pprint
from flask import request


def main():
    with open("ast_example.py", "r") as source:
        tree = ast.parse(source.read())

    print(tree)
    analyzer = Analyzer()
    analyzer.visit(tree)
    analyzer.report()

"""
Check docs at https://greentreesnakes.readthedocs.io/en/latest/nodes.html
to understand class attributes. 
"""
class Analyzer(ast.NodeVisitor):
    def __init__(self):
        self.stats = {"import": [], "from": []}

    def visit_Import(self, node):
        for alias in node.names:
            self.stats["import"].append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.stats["import"].append(node.module)
        for alias in node.names:
            self.stats["from"].append(alias.name)
        self.generic_visit(node)

    def report(self):
        pprint(self.stats)


if __name__ == "__main__":
    main()