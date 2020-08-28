import ast
import sys
import os
import json

from Analyzer import Analyzer
from utils import get_python_filenames, generate_requirements_file

MAPPINGS_FILE = "pip_import_mappings.json"
def main():
    assert len(sys.argv) == 3, "[USAGE]: Ensure you provide 2 arguments " \
                               "<directory of codebase> <filepath for requirements>"
    # Remove first 2 elements as they refer to current dir
    if len(sys.path) >= 3:
        sys.path = sys.path[2:]

    else:
        sys.path = []

    if not os.path.isabs(sys.argv[1]):
        abs_path = os.path.abspath(sys.argv[1])
    else:
        abs_path = sys.argv[1]

    # Loading mappings
    with open(MAPPINGS_FILE, 'r') as f:
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

    generate_requirements_file(import_mapping=import_mapping, dest_file=requirements_file, code_dir_abs_path=abs_path,
                               mapping_dict=mapping_dict)


if __name__ == "__main__":
    main()
