from typing import List, Type


class Postprocess:

    def postprocess(self, user, message, *args, **kwargs):
        pass


def postprocessor_compose(*agrs: List[Type[Postprocess]]):
    class PostprocessCompose(Postprocess):
        postprocessors: List[Postprocess] = [processor_cls() for processor_cls in agrs]

        def postprocess(self, user, message, *args, **kwargs):
            for processor in self.postprocessors:
                processor.postprocess(user, message, *args, **kwargs)
    return PostprocessCompose
