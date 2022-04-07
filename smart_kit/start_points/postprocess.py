from typing import List, Type


class PostprocessMainLoop:

    async def postprocess(self, user, message, *args, **kwargs):
        pass


class PostprocessCompose(PostprocessMainLoop):
    postprocessors: List[PostprocessMainLoop] = []

    async def postprocess(self, user, message, *args, **kwargs):
        for processor in self.postprocessors:
            await processor.postprocess(user, message, *args, **kwargs)


def postprocessor_compose(*args: Type[PostprocessMainLoop]):
    class Compose(PostprocessCompose):
        postprocessors = [processor_cls() for processor_cls in args]
    return Compose
