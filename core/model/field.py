# coding: utf-8


class Field:
    def __init__(self, name, model, description=None, *args):
        self.name = name
        self.model = model
        self.description = description
        self.args = args
