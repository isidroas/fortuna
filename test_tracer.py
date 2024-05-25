import pytest
from tracer2 import *


# TODO: put here static and class methods
class A:
    my_attr = TracedSet()

    @property
    def my_attr2(self):
        return self._my_atrr2

    @trace_property
    @my_attr2.setter
    def my_attr2(self, value):
        if value >= 10:
            raise ValueError("should be less than 10")
        self._my_atrr2 = value

    def foo(self, a, b, c=3):
        return a + b

    @trace_method(merge=True)
    def f_merged(self, a, b, c=3):
        return a + b

    @trace_method
    def level1(self, a, b):
        res = self.level2_not_interesting(a + b)
        return self.level2_interesting(res)

    # it allows you to ignore non-insteresting functions
    def level2_not_interesting(self, c):
        return self.level3(c)

    @trace_method(merge=True)
    def level3(self, c):
        return c * 2

    @trace_method(merge=True)
    def level2_interesting(self, c):
        return c - 1


@pytest.fixture
def reset_indent():
    import tracer2

    tracer2.nesting = -1


@pytest.fixture
def method():

    a = A()
    return a.foo


@pytest.fixture
def prop():

    a = A()
    return a.my_prop


def test_trace_method():

    def method(): ...

    method.__qualname__ = "A.foo"
    decorator = FunctionTracer()
    # wrap = decorator(method)

    # "A.foo('one', 2) -> ..."
    # "A.foo('one', 2) ..."
    assert "A.foo('one', 2) ..." == decorator.format_start(method, args=("one", 2))

    assert "A.foo('one', b=2) ..." == decorator.format_start(
        method, args=("one",), kwargs={"b": 2}
    )

    # 'hello' <-
    # 'hello' = A.foo(...)
    # 'hello' <- A.foo(...)
    # <- 'hello'
    assert "-> 'hello'" == decorator.format_end(
        method, ret="hello"
    )  # menos información, pero era redundante. Esta opción tiene todo el sentido como se empezó ...; Además con el highliter creo que queda espectacular y más sencillo porque todas apuntan a un mismo sentido
    assert "-> 5" == decorator.format_end(method, ret=5)
    assert "-> None" == decorator.format_end(method, ret=None)

    assert "A.foo('one', 2) -> 5" == decorator.format_merged(
        method, args=("one", 2), ret=5
    )

    # or "A.foo('one', 2)"
    assert "A.foo('one', 2) -> None" == decorator.format_merged(
        method, args=("one", 2), ret=None
    )

    assert (
        "A.foo('one', 2) -X AssertionError('invalid')"
        == decorator.format_merged_exception(
            method, args=("one", 2), kwargs={}, exc=AssertionError("invalid")
        )
    )

    assert "-X AssertionError('invalid')" == decorator.format_exception(
        method, exc=AssertionError("invalid")
    )


def test_arg_formats():
    def func(a, b, c=3): ...

    method.__qualname__ = "A.foo"
    t = FunctionTracer(args_fmt="b={b}")
    assert "b=7" == t.format_args((5,), {"b": 7}, func)


def test_ret_format():
    t = FunctionTracer(ret_fmt="{0:.3}")
    assert "0.333" == t.format_ret(1 / 3)


def test_trace_function():
    # change to trace call?
    decorator = FunctionTracer()
    import logging

    fn = logging.getLogger

    # 'logging:getLogger(5, 3)'
    assert "getLogger(5, 3)" == decorator.format_start(fn, args=(5, 3))


def test_trace_property(method):
    decorator = TracedSet()
    decorator.owner = A
    decorator.name = "foo"
    assert "A.foo=3" == decorator.format_set(3)
    assert "A.foo=3 -X ValueError('Minimum is ten')" == decorator.format_exception(
        3, ValueError("Minimum is ten")
    )


def test_trace_property2():
    a = A()
    a.my_attr = 3
    assert a.my_attr == 3
    a.my_attr2 = 4
    assert a.my_attr2 == 4


def test_stdout(caplog, reset_indent):

    A.foo2 = MethodTracer()(A.foo)
    a = A()
    method = a.foo2

    with caplog.at_level(logging.DEBUG, logger="A.foo"):
        method("one", " two")
    assert "A.foo('one', ' two')" == caplog.records.pop(0).message
    assert "'one two' <- A.foo(...)" == caplog.records.pop(0).message

    with caplog.at_level(logging.DEBUG, logger="A.foo"), pytest.raises(TypeError):
        method("one", 2)

    assert "A.foo('one', 2)" == caplog.records.pop(0).message
    assert (
        "TypeError('can only concatenate str (not \"int\") to str') X- A.foo(...)"
        == caplog.records.pop(0).message
    )


def test_stdout_merged(caplog, reset_indent):

    A.foo2 = MethodTracer(merge=True)(A.foo)
    a = A()
    method = a.foo2

    with caplog.at_level(logging.DEBUG, logger="A.foo"):
        method("one", " two")

    assert "A.foo('one', ' two') -> 'one two'" == caplog.records.pop(0).message

    with caplog.at_level(logging.DEBUG, logger="A.foo"), pytest.raises(TypeError):
        method("one", 2)

    assert (
        "A.foo('one', 2) -X TypeError('can only concatenate str (not \"int\") to str')"
        == caplog.records.pop(0).message
    )


def test_stdout_property(caplog, reset_indent):
    a = A()

    with caplog.at_level(logging.DEBUG, logger="A.my_attr"):
        a.my_attr = 3
    assert "A.my_attr=3" == caplog.records.pop(0).message

    a = A()
    with caplog.at_level(logging.DEBUG, logger="A.my_attr2"):
        a.my_attr2 = 3
    assert "A.my_attr2=3" == caplog.records.pop(0).message
    with caplog.at_level(logging.DEBUG, logger="A.my_attr2"), pytest.raises(ValueError):
        a.my_attr2 = 11
    assert (
        "A.my_attr2=11 -X ValueError('should be less than 10')"
        == caplog.records.pop(0).message
    )


def test_stdout_indent(caplog, reset_indent):
    # TODO: test property
    a = A()

    with caplog.at_level(logging.DEBUG, logger="A"):
        a.level1(2, 3)

    assert """\
A.level1(2, 3)
    A.level3(5) -> 10
    A.level2_interesting(10) -> 9
9 <- A.level1(...)\
""" == "\n".join(
        record.message for record in caplog.records
    )
