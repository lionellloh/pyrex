import importlib
import os
import re
import sys

from platform import python_version
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

def get_local_faulty_imports(import_mapping: dict, code_dir_abs_path: str) -> tuple:
    faulty_import_set = set()
    local_import_set = set()
    for dir, imps in import_mapping.items():
        # insert in the path so python will prioritise the search accordingly
        sys.path.insert(0, dir)
        for imp in imps:
            top_level_imp = imp.split(".")[0]
            module_spec = importlib.util.find_spec(top_level_imp)
            if not module_spec:
                faulty_import_set.add(top_level_imp)
                continue

            # Local import: found in origin
            if module_spec.origin and module_spec.origin[:len(code_dir_abs_path)] == code_dir_abs_path:
                local_import_set.add(imp)

            # Local import: found in submodule_search_locations
            elif module_spec.submodule_search_locations:
                for search_loc in module_spec.submodule_search_locations:
                    print(search_loc)
                    if search_loc[:len(code_dir_abs_path)] == code_dir_abs_path:
                        local_import_set.add(imp)

    return local_import_set, faulty_import_set


def generate_requirements_file(import_mapping: dict, dest_file: str, code_dir_abs_path: str, mapping_dict:dict):
    if not os.path.exists(dest_file):
        with open(dest_file, 'w'):
            pass
    sys.path.insert(0, code_dir_abs_path)
    import_list = flatten_nested_lst(list(import_mapping.values()))

    # normalize api.utils -> api and then remove duplicates
    import_set = set([imp.split(".")[0] for imp in import_list])

    local_import_set, faulty_import_set = get_local_faulty_imports(import_mapping, code_dir_abs_path)

    # Filter 1: Remove local and error-generating imports
    non_local_import_set = import_set - local_import_set - faulty_import_set
    vers = ".".join(python_version().split(".")[:-1])
    builtin_pkg_set = get_builtin_libs(vers)
    # Filter 2: Remove builtin packages
    third_party_imports = list(non_local_import_set.difference(builtin_pkg_set))
    # Filter 3: Apply mapping according to json file
    pip_package_list = apply_mapping(third_party_imports, mapping_dict)

    with open(dest_file, 'w') as f:
        for pkg in pip_package_list:
            f.write(f"{pkg}\n")

    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

    # Need to change the args before running pip-compile
    sys.argv = ["", dest_file]
    print("Generating dependencies from top-level imports...")
    cli()