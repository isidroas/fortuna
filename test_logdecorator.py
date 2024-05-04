import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
import traceback

nesting = 0

def increase_nest(func):

    def wrapper():
        global nesting
        nesting+=1
        func()
        nesting-=1
    return wrapper

def get_nesting_trimmed():
    # https://stackoverflow.com/questions/39078467/python-how-to-get-the-calling-function-not-just-its-name
    # global nesting
    return ' ' * nesting


@increase_nest

def foo():
    logging.info('%scalled', get_nesting_trimmed())

def bar():
    foo() # this should not add nesting?

def baz():
    logging.info('%sstarting', get_nesting_trimmed())
    bar()
    logging.info('%sending', get_nesting_trimmed())


# baz()
from formatter import log_trace, log_property

class A:
    def __init__(self):
        self.myattr = 0
    @log_trace()
    def foo(self, a):
        self.myattr = 1

    def bar(self, b):
        self.foo(1)
    @log_trace('c={c}')
    def baz(self, c):
        self.bar(2)
        raise AssertionError('bad things happens')

    @property
    def myattr(self):
        return self._myattr

    @myattr.setter
    @log_property()
    def myattr(self, value):
        self._myattr = value
        

a = A()
try:
    a.baz(3)
except AssertionError:
    pass
