import pytest
import itertools

# from tracer import trace_method
from typing import Callable


def format_args(args, kwargs):
    """
    >>> format_args((1, 2), dict(a=3))
    '1, 2, a=3'
    """
    return ", ".join(
        itertools.chain(
            (repr(a) for a in args), (f"{k}={v!r}" for k, v in kwargs.items())
        )
    )


import inspect


def get_name(fn):
    """
    >>> import random
    >>> get_name(random.Random().seed)
    'Random.seed'

    # >>> import logging
    # >>> get_name(logging.getLogger)
    # 'logging:getLogger'

    >>> from multiprocessing.pool import Pool
    >>> get_name(Pool.Process)
    'Pool.Process'
    """

    # # TODO: static, classmethods
    # if inspect.ismethod(fn):
    #     cls = type(fn.__self__)
    #     return '%s.%s' %(cls.__name__, fn.__name__)
    # else:
    #     return '%s:%s' %(fn.__module__, fn.__name__)
    return fn.__qualname__


class trace_method:
    def __init__(self, arg_fmt=None, ret_fmt=None, merge=False):
        self.merge = merge
        self.arg_fmt = arg_fmt
        self.ret_fmt = ret_fmt

    def __call__(self, method: Callable):

        def wrapper(*args, **kwargs):
            if start := self.format_start(method, args, kwargs):
                print(start)
            ret = self.method(*args, **kwargs)
            if end := self.format_end(ret):
                print(end)
            return ret

        return wrapper

    def format_start(self, method, args, kwargs={}):
        return "%s(%s)" % (get_name(method), format_args(args, kwargs))

    def format_end(self, method, ret):
        res = "<- %s(...)" % get_name(method)
        if ret is not None:
            res = "%r " % ret + res
        return res

    def format_merged(self, method, args=(), kwargs={}, ret=None):
        return "%s(%s) -> %r" % (get_name(method), format_args(args, kwargs), ret)

        res = "<- %s(...)" % get_name(method)
        if ret is not None:
            res = "%r " % ret + res
        return res

    EXC = "-X"

    def format_exception(self, method, exc):
        return "%r %s %s(...)" % (exc, self.EXC[::-1], get_name(method))

    def format_merged_exception(self, method, args, kwargs, exc):
        return "%s(%s) %s %r" % (
            get_name(method),
            format_args(args, kwargs),
            self.EXC,
            exc,
        )


class A:
    def foo(self, a, b, c=3):
        return "hello"


@pytest.fixture
def method():

    a = A()
    return a.foo


def test_trace_method(method):

    decorator = trace_method()
    # wrap = decorator(method)

    # "A.foo('one', 2) -> ..."
    # "A.foo('one', 2) ..."
    assert "A.foo('one', 2)" == decorator.format_start(method, args=("one", 2))

    assert "A.foo('one', b=2)" == decorator.format_start(
        method, args=("one",), kwargs={"b": 2}
    )

    assert "'hello' <- A.foo(...)" == decorator.format_end(method, ret="hello")
    assert "5 <- A.foo(...)" == decorator.format_end(method, ret=5)
    assert "<- A.foo(...)" == decorator.format_end(method, ret=None)

    assert "A.foo('one', 2) -> 5" == decorator.format_merged(
        method, args=("one", 2), ret=5
    )
    assert "A.foo('one', 2) -> None" == decorator.format_merged(
        method, args=("one", 2), ret=None
    )
    # "A.foo('one', 2)"

    assert (
        "A.foo('one', 2) -X AssertionError('invalid')"
        == decorator.format_merged_exception(
            method, args=("one", 2), kwargs={}, exc=AssertionError("invalid")
        )
    )

    assert "AssertionError('invalid') X- A.foo(...)" == decorator.format_exception(
        method, exc=AssertionError("invalid")
    )


def test_trace_function():
    # change to trace call?
    decorator = trace_method()
    import logging

    fn = logging.getLogger

    # assert 'logging:getLogger(5, 3)' == decorator.format_start(fn, args=(5, 3))
    assert "getLogger(5, 3)" == decorator.format_start(fn, args=(5, 3))


@pytest.mark.skip
def test_stdout(method, capsys):
    # TODO: pytest capture stdout
    wrap = trace_method()(method)
    wrap("one", 2)
    assert (
        """\
A.foo("one", 2)
"hello" <- A.foo(...)
"""
        == capsys.readouterr().out
    )
