import os
import objgraph
import psutil
import time


def get_meminfo():
    p = psutil.Process(os.getpid())
    return str(p.memory_info())


def show_growth(file=None):
    objgraph.show_growth(file=file, shortnames=False)


def show_most_common_types(file=None, limit=20):
    objgraph.show_most_common_types(limit=limit, shortnames=False, file=file)


def get_leaking_objects(file=None, limit=5):
    roots = objgraph.get_leaking_objects()
    objgraph.show_refs(roots[:limit], refcounts=True, shortnames=False, output=file)


if __name__ == "__main__":
    while 1 :
        print(show_most_common_types())
        time.sleep(1)
