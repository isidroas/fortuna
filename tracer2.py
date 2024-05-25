import itertools
import logging

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


def trace_method(method=None, *, ret_fmt=None, merge=False):
    if method is None:
        return MethodTracer(args_fmt=None, ret_fmt=ret_fmt, merge=merge)
    else:
        return MethodTracer()(method)


def trace_function(function=None, *, args_fmt=None, ret_fmt=None, merge=False):
    if function is None:
        return FunctionTracer(args_fmt=args_fmt, ret_fmt=ret_fmt, merge=merge)
    else:
        return FunctionTracer()(function)


# global var. This is not thread safe
nesting = -1
INDENT_WIDTH = "    "


def get_indent():
    return nesting * INDENT_WIDTH


def increment_indent():
    global nesting
    nesting += 1


def decrement_indent():
    global nesting
    nesting -= 1


import contextlib


@contextlib.contextmanager
def track_indent():
    increment_indent()
    try:
        yield get_indent()
        # TODO: yield nesting-1? easier for properties?
    finally:
        decrement_indent()


class FunctionTracer:
    def __init__(self, args_fmt=None, ret_fmt=None, merge=False):
        self.merge = merge
        self.args_fmt = args_fmt
        self.ret_fmt = ret_fmt

    def __call__(self, method: Callable):

        logger = logging.getLogger(method.__qualname__ + ".tracer")

        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            with track_indent() as indent:

                if not self.merge:
                    logger.debug(self.format_start(method, args, kwargs, indent))
                try:
                    ret = method(*args, **kwargs)
                except Exception as exc:
                    if self.merge:
                        logger.debug(
                            self.format_merged_exception(
                                method, args, kwargs, exc, indent
                            )
                        )
                    else:
                        logger.debug(self.format_exception(method, exc, indent))
                    raise

                if self.merge:
                    logger.debug(self.format_merged(method, args, kwargs, ret, indent))
                else:
                    logger.debug(self.format_end(method, ret, indent))
                return ret

        return wrapper

    def format_start(self, method, args, kwargs={}, indent=""):
        return "{}{name}({args}) ...".format(
            indent,
            name=get_name(method),
            args=self.format_args(args, kwargs, method),
        )

    def format_end(self, method, ret, indent=""):
        return "%s-> %s" % (indent, self.format_ret(ret))

    def format_merged(self, method, args=(), kwargs={}, ret=None, indent=""):
        return "%s%s(%s) -> %s" % (
            indent,
            get_name(method),
            self.format_args(args, kwargs, method),
            self.format_ret(ret),
        )

    def format_exception(self, method, exc, indent=""):
        return "{}-X {exc!r}".format(indent, exc=exc)

    def format_merged_exception(self, method, args, kwargs, exc, indent=""):
        return "%s%s(%s) %s %r" % (
            indent,
            get_name(method),
            self.format_args(args, kwargs, method),
            EXC,
            exc,
        )

    def format_args(self, args, kwargs, func):
        signature = inspect.signature(func)
        if self.args_fmt is not None:
            # use bind_partial instead to delay error?
            bind = signature.bind_partial(*args, **kwargs)
            bind.apply_defaults()
            return self.args_fmt.format(**bind.arguments)
        is_bounded = hasattr(func, "__self__")
        if is_bounded:
            args = args[1:]
        return format_args(args, kwargs)

    def format_ret(self, ret):
        if self.ret_fmt is None:
            return repr(ret)
        return self.ret_fmt.format(ret)


class MethodTracer(FunctionTracer):
    def format_args(self, args, kwargs, func):
        return super().format_args(args[1:], kwargs, func)


from abc import abstractmethod


class TracedSetBase:

    def __init__(self, value_fmt=None):
        self.value_fmt = value_fmt

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

    def __set__(self, obj, value):
        logger = logging.getLogger(self.qualname + ".tracer")
        with track_indent() as indent:  # is uncommon property with child calls?
            try:
                self.setter(obj, value)
            except Exception as exc:
                logger.debug(self.format_exception(value, exc, indent))
                raise
            logger.debug(self.format_set(value, indent))

    @abstractmethod
    def setter(self, obj, value): ...

    def format_set(self, value, indent=""):
        return "%s%s=%s" % (indent, self.qualname, self.format_value(value))

    def format_exception(self, value, exc, indent=""):
        return "%s%s=%r %s %r" % (indent, self.qualname, value, EXC, exc)

    def format_value(self, value):
        if self.value_fmt is None:
            return repr(value)
        return self.value_fmt.format(value)

    @property
    def qualname(self):
        return "%s.%s" % (self.owner.__name__, self.name)


class TracedSet(TracedSetBase):

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)
        self.private_name = "_" + name

    def __get__(self, obj, type=None):
        return getattr(obj, self.private_name)

    def __delete__(self, obj):
        del self.private_name

    def setter(self, obj, value):
        setattr(obj, self.private_name, value)


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
