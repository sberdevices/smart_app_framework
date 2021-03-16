import sys
from functools import wraps


def exc_handler(on_error_obj_method_name=None, handled_exceptions=None, on_error_return_res=None):
    handled_exceptions = tuple(handled_exceptions) if handled_exceptions else (Exception,)

    def exc_handler_decorator(funct):
        @wraps(funct)
        def _wrapper(obj, *args, **kwarg):
            result = None
            try:
                result = funct(obj, *args, **kwarg)
            except handled_exceptions:
                try:
                    on_error = getattr(obj, on_error_obj_method_name) if \
                        on_error_obj_method_name else (lambda *x: on_error_return_res)
                    result = on_error(*args, **kwarg)
                except:
                    print(sys.exc_info())
            return result

        return _wrapper

    return exc_handler_decorator
