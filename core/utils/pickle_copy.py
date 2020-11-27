import pickle


def pickle_deepcopy(obj):
    return pickle.loads(pickle.dumps(obj, -1))
