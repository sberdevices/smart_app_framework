from typing import List


class Postprocess:

    def postprocess(self, *args, **kwargs):
        pass


class PostprocessCompose(Postprocess):
    postprocessors: List[Postprocess] = []

    def postprocess(self, *args, **kwargs):
        for processor in self.postprocessors:
            processor.postprocess(*args, **kwargs)
