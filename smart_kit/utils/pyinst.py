import os
import importlib


def data_files_for_packages(package_files: dict) -> list:
    datas = []
    for package, files in package_files.items():
        proot = os.path.dirname(importlib.import_module(package).__file__) if package != '' else ''
        datas.extend(
            (
                os.path.join(proot, f),  # Source file pattern
                os.path.join(package, os.path.dirname(f))  # Dest relative folder
            ) for f in files)
    return datas


# This is not necessarily actual files but path patters
SAF_data_files = data_files_for_packages({
    # Our app
    '': ['static/.'],
    # Our lib
    'smart_kit': ['template/.'],
    # 3rd-party libs
    'ics': ['grammar/contentline.ebnf'],
    'pymorphy2_dicts': ['data/*.json', 'data/*.array', 'data/*.dawg', 'data/*.intdawg'],
    'rnnmorph': ['models/.'],
})
