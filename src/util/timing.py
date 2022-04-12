import time
from functools import wraps
from contextlib import contextmanager
from .obj import SingletonDecorator


@SingletonDecorator
class Timer:
    """ Times methods and code blocks """

    def __init__(self):
        self.methods = {}
        self.code_blocks = {}

    def time_method(self, func):
        func_name = func.__name__ + '()'
        if not self.methods.get(func_name, None):
            self.methods[func_name] = _TimedMethod(func_name)

        @wraps(func)
        def wrapper_func(*args, **kwargs):
            start = time.time()
            value = func(*args, **kwargs)
            end = time.time() - start
            self.methods[func_name].update(end)
            return value
        return wrapper_func

    @contextmanager
    def time_code_block(self, code_desc):
        if not self.code_blocks.get(code_desc, None):
            self.code_blocks[code_desc] = _TimedCode(code_desc)
        start = time.time()
        yield
        end = time.time() - start
        self.code_blocks[code_desc].update(end)


class _TimedObject:
    """Times methods and code blocks"""
    def __init__(self):
        self.n_timed = 0
        self.times = []
        self.avg_time = 0.0

    def update(self, next_time):
        self.n_timed += 1
        self.times.append(next_time)
        self.avg_time = sum(self.times) / self.n_timed


class _TimedCode(_TimedObject):
    def __init__(self, code_desc):
        super().__init__()
        self.code_desc = code_desc

    def get_name(self):
        return self.code_desc


class _TimedMethod(_TimedObject):
    def __init__(self, method_name):
        super().__init__()
        self.method_name = method_name

    def get_name(self):
        return self.method_name
