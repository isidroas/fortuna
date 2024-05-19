
# global var. This is not thread safe
nesting = 0

from typing import Callable
from formatter import Template
from logdecorator import log_on_end, log_on_start, log_on_error
import logging
INDENT_WIDTH = '    '
#TODO: automatic format when None
def trace_method(args_fmt='', ret_fmt='', log_start=True, log_end=True):
    """
    log_start=False is only recommended when you know that there won't be more child traces
    log_end=False is only recommended when you know that there won't be more child traces and wan't to hide return value
    """

    def decorator(meth: Callable):

        def wrapper(*args, **kwargs):
            global nesting
            indent = INDENT_WIDTH* nesting
            fmt="%s{self.__class__.__name__}.{callable.__name__}(%s)" % (indent, args_fmt)
            meth2 = meth
            if log_start:
                meth2 = log_on_start(logging.DEBUG, Template(fmt))(meth2) # TODO: inficient; do outside wrapper
            if log_end:
                # if log_start and indent!='':
                #     fmt_list = list(fmt)
                #     fmt_list[len(indent)-2] = '⮑'
                #     fmt = ''.join(fmt_list)
                fmt="%s{self.__class__.__name__}.{callable.__name__}(...)" % (indent)
                meth2 = log_on_end(logging.DEBUG, Template(indent+ret_fmt+ '<- '+fmt.lstrip() ))(meth2)
                meth2 = log_on_error(logging.DEBUG, Template(fmt + ' x {e!r}'), on_exceptions=Exception)(meth2)
            nesting+=1
            try:
                return meth2(*args, **kwargs)
            finally:
                nesting-=1
        return wrapper
    return decorator

# TODO: make common with trace_method
def trace_function(args_fmt='', ret_fmt='', log_start=True, log_end=True):
    def decorator(meth: Callable):

        def wrapper(*args, **kwargs):
            global nesting
            indent = INDENT_WIDTH* nesting
            fmt="%s{callable.__name__}(%s)" % (indent, args_fmt)
            meth2 = meth
            if log_start:
                meth2 = log_on_start(logging.DEBUG, Template(fmt))(meth2) # TODO: inficient; do outside wrapper
            if log_end:
                if log_start and indent!='':
                    fmt_list = list(fmt)
                    fmt_list[len(indent)-2] = '⮑'
                    fmt = ''.join(fmt_list)
                meth2 = log_on_end(logging.DEBUG, Template(fmt + '-> ' + ret_fmt))(meth2)
                meth2 = log_on_error(logging.DEBUG, Template(fmt + ' x {e!r}'), on_exceptions=Exception)(meth2)
            nesting+=1
            try:
                return meth2(*args, **kwargs)
            finally:
                nesting-=1
        return wrapper
    return decorator

def trace_property(fmt=None):
    def decorator(meth: Callable):

        def wrapper(self, value):
            global nesting
            indent = INDENT_WIDTH * nesting
            nesting+=1
            
            if fmt is not None:
                val = Template(fmt).format(value)
            else:
                val = str(value)
            logging.debug('%s%s.%s=%s',indent, type(self).__name__, meth.__name__, val)
            meth(self, value)
            # TODO: handle exceptions
            nesting-=1
        return wrapper

    return decorator
    
