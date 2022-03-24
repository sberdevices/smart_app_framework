from typing import List, Type


class Postprocess:

    def postprocess(self, user, message, *args, **kwargs):
        pass


class PostprocessCompose(Postprocess):
    postprocessors: List[Postprocess] = []

    def postprocess(self, user, message, *args, **kwargs):
        for processor in self.postprocessors:
            processor.postprocess(user, message, *args, **kwargs)


def postprocessor_compose(*agrs: List[Type[Postprocess]]):
    class Compose(PostprocessCompose):
        postprocessors = [processor_cls() for processor_cls in agrs]
    return Compose
