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
    return fn.__qualname__

EXC = "-X"


class trace_method:
    def __init__(self, arg_fmt=None, ret_fmt=None, merge=False):
        self.merge = merge
        self.arg_fmt = arg_fmt
        self.ret_fmt = ret_fmt

    def __call__(self, method: Callable):

        def wrapper(*args, **kwargs):
            if not self.merge:
                print(self.format_start(method, args, kwargs))
            try:
                ret = method(*args, **kwargs)
            except Exception as exc:
                if self.merge:
                    print(self.format_merged_exception(method, args, kwargs, exc))
                else:
                    print(self.format_exception(method, exc))
                raise

            if self.merge:
                print(self.format_merged(method, args, kwargs, ret))
            else:
                print(self.format_end(method, ret))
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

    def format_exception(self, method, exc):
        return "%r %s %s(...)" % (exc, EXC[::-1], get_name(method))

    def format_merged_exception(self, method, args, kwargs, exc):
        return "%s(%s) %s %r" % (
            get_name(method),
            format_args(args, kwargs),
            EXC,
            exc,
        )

from abc import abstractmethod
class TracedSetBase:

    def __init__(self, value_fmt=None):
        self.value_fmt = value_fmt

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

    def __set__(self, obj, value):
        try:
            self.setter(obj, value)
        except Exception as exc:
            print(self.format_exception(value, exc))
            raise
        print(self.format_set(value))

    @abstractmethod
    def setter(self, obj, value):
        ...

    def format_set(self, value):
        return "%s.%s=%r" % (self.owner.__name__, self.name, value)

    def format_exception(self, value, exc):
        return "%s.%s=%r %s %r" % (self.owner.__name__,self.name, value, EXC, exc)

class TracedSet(TracedSetBase):

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)
        self.private_name = '_' + name

    def __get__(self, obj, type=None):
        return getattr(obj, self.private_name)

    def __delete__(self, obj):
        del self.private_name

    def setter(self, obj, value):
        setattr(obj, self.private_name,  value)


import functools
class TracedSetWrapped(TracedSetBase):
    def __init__(self, *args, inner_descriptor, **kwargs):
        self.inner_descriptor = inner_descriptor
        functools.update_wrapper(self, inner_descriptor)
        super().__init__(*args, **kwargs)
        # TODO: assign here in case it does not exist?

    # def __set_name__(self, owner, name):
    #     self.inner_descriptor.__set_name__(owner, name)

    def __get__(self, obj, type=None):
        return self.inner_descriptor.__get__(obj, type)

    def __delete__(self, obj):
        self.inner_descriptor.__del__(obj)

    def setter(self, obj, value):
        self.inner_descriptor.__set__(obj, value)


def trace_property(prop=None, *, value_fmt=None):
    if prop is None:
        return lambda prop: TracedSetWrapped(inner_descriptor=prop, value_fmt=value_fmt)
    else:
        return TracedSetWrapped(inner_descriptor=prop)

    

# TODO: put here static and class methods
class A:
    my_attr = TracedSet()

    @property
    def my_attr2(self):
        return self._my_atrr2

    @trace_property
    @my_attr2.setter
    def my_attr2(self, value):
        if value>=10:
            raise ValueError('should be less than 10')
        self._my_atrr2 = value

    def foo(self, a, b, c=3):
        return a + b

@pytest.fixture
def method():

    a = A()
    return a.foo

@pytest.fixture
def prop():

    a = A()
    return a.my_prop


def test_trace_method(method):

    decorator = trace_method()
    # wrap = decorator(method)

    # "A.foo('one', 2) -> ..."
    # "A.foo('one', 2) ..."
    assert "A.foo('one', 2)" == decorator.format_start(method, args=("one", 2))

    assert "A.foo('one', b=2)" == decorator.format_start(
        method, args=("one",), kwargs={"b": 2}
    )

    # "'hello' = A.foo(...)"
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

    # 'logging:getLogger(5, 3)'
    assert "getLogger(5, 3)" == decorator.format_start(fn, args=(5, 3))

def test_trace_property(method):
    decorator = TracedSet()
    decorator.owner = A
    decorator.name = 'foo'
    assert "A.foo=3" == decorator.format_set(3)
    assert "A.foo=3 -X ValueError('Minimum is ten')" == decorator.format_exception(3, ValueError('Minimum is ten'))

def test_trace_property2():
    a = A()
    a.my_attr=3
    assert a.my_attr==3
    a.my_attr2=4
    assert a.my_attr2==4

def test_stdout(method, capsys):
    # TODO: pytest capture stdout
    wrap = trace_method()(method)
    wrap("one", " two")
    assert (
        """\
A.foo('one', ' two')
'one two' <- A.foo(...)
"""
        == capsys.readouterr().out
    )

    with pytest.raises(TypeError):
        wrap("one", 2)
    assert (
        """\
A.foo('one', 2)
TypeError('can only concatenate str (not "int") to str') X- A.foo(...)
"""
        == capsys.readouterr().out
    )


def test_stdout_merged(method, capsys):
    wrap = trace_method(merge=True)(method)
    wrap("one", " two")
    assert "A.foo('one', ' two') -> 'one two'\n" == capsys.readouterr().out

    with pytest.raises(TypeError):
        wrap("one", 2)
    assert (
        "A.foo('one', 2) -X TypeError('can only concatenate str (not \"int\") to str')\n"
        == capsys.readouterr().out
    )

def test_stdout_property(capsys):
    a = A()
    a.my_attr = 3
    assert "A.my_attr=3\n" == capsys.readouterr().out

    a = A()
    a.my_attr2 = 3
    assert "A.my_attr2=3\n" == capsys.readouterr().out
    with pytest.raises(ValueError):
        a.my_attr2=11
    assert "A.my_attr2=11 -X ValueError('should be less than 10')\n" == capsys.readouterr().out
