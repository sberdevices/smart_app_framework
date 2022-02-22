import os
import tracemalloc

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


def get_top_malloc(trace_limit=3):
    snapshot = tracemalloc.take_snapshot()
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics('traceback')
    msg = ""

    if trace_limit > 0:
        msg += f"Top malloc {trace_limit} lines\n"
        for index, stat in enumerate(top_stats[:trace_limit], 1):
            msg += f"#{index}: {stat.size // 1024} KB, {stat.count} times\n"
            for line in stat.traceback.format(limit=16):
                msg += f"{line}\n"
        other = top_stats[trace_limit:]
        if other:
            size = sum(stat.size for stat in other)
            msg += f"{len(other)} other: {size // 1024} KB\n"
    total = sum(stat.size for stat in top_stats)
    msg += f"Total allocated size: {total // 1024 // 1024} MB"
    return msg


if __name__ == "__main__":
    while 1 :
        print(show_most_common_types())
        time.sleep(1)
