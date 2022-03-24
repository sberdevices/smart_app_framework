from typing import List, Type


class Postprocess:

    def postprocess(self, *args, **kwargs):
        pass


def postprocessor_compose(*agrs: List[Type[Postprocess]]):
    class PostprocessCompose(Postprocess):
        postprocessors: List[Postprocess] = [processor_cls() for processor_cls in agrs]

        def postprocess(self, *args, **kwargs):
            for processor in self.postprocessors:
                processor.postprocess(*args, **kwargs)
    return PostprocessCompose
