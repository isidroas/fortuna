
def _get_sources(pool_index, sources):
    """
    >>> list(_get_sources(2, (1, 2, 0, 2)))
    [1, 3]
    """
    try:
        source = sources.index(pool_index)
    except ValueError:
        source = None

    while source is not None:
        yield source
        try:
            source = sources.index(pool_index, source+1)
        except ValueError:
            source = None


def _get_templates(n_pools, n_sources, width):
    """
    >>> template, pointer_template, _= _get_templates(5, 3, width=20)
    >>> pointer_template
    ' <- {: <5}'
    >>> template
    '{: <1}: 0x{: <6}'
    """

    pointer_template = (' <- {: <%d}' %  len(','.join(' ' * n_sources))) if n_sources else ''
    template = '{: <%d}: 0x' % (2 if n_pools>10 else 1)
    hex_width =  width - len(template.format('')) - len(pointer_template.format(''))
    template += '{: <%d}' % hex_width

    return template, pointer_template, hex_width
    
def format_overflow(data: bytes, max_width):
    """
    >>> format_overflow('3031323334', max_width = 10)
    '3031323334'
    >>> format_overflow('3031323334', max_width = 8)
    '(+4)..34'
    >>> format_overflow('3031323334', max_width = 9)
    '(+4)...34'
    >>> format_overflow('3031323334353637383930', max_width = 10)
    '(+10)...30'
    """
    if len(data)<= max_width:
        return data

    len_bytes, rest = divmod(len(data),2)
    assert rest==0, 'not hexa'

    fmt ='(+{: <%d})'% len(str(len_bytes))
    remaining = max_width - len(fmt.format(0))
    fmt += '...' if remaining%2 else '..'
    remaining = max_width - len(fmt.format(0))

    remaining_bytes, rest = divmod(remaining, 2)
    assert rest==0

    # print(remaining)
    # print(len(fmt.format(0)))
    return fmt.format(len_bytes-remaining_bytes) + data[-remaining:]


def format_pools(pools, sources=(), width = 27):
    """
    format is:

        number_of_pool: 0xCAFEE     <- source1, source2
    """
    template, pointer_template, hex_width = _get_templates(len(pools), len(sources), width)
    res =''
    for index, pool in enumerate(pools):
        data = pool.hex().upper()
        res+=template.format(index, format_overflow(data, hex_width))
        sources_pointing = list(_get_sources(index, sources))
        if sources_pointing:
            res += pointer_template.format(','.join(str(i) for i in sources_pointing))
        res+='\n'
    return res

import string
from functools import partial
class Formatter(string.Formatter):
    def format_field(self, value, format_spec):
        if isinstance(value, (bytes, bytearray)):
            if format_spec.endswith('X'):
                format_spec = format_spec[:-1]
                value = value.hex().upper()
            if format_spec.isdigit():
                value = format_overflow(value, int(format_spec))
                format_spec = ''
        return super().format_field(value, format_spec)

from collections import UserString
class Template(UserString):
    """
    inspired in https://github.com/mkdocs/mkdocs/blob/53fec50e57f6bad152ad589a83ae83d1cd72b2f5/mkdocs/config/config_options.py#L640
    """
    def format(self_, *args, **kwargs):
        fmt = Formatter()
        return fmt.format(str(self_), *args, **kwargs)

# global var. This is not thread safe
nesting = 0

from typing import Callable
from logdecorator import log_on_end, log_on_start, log_on_error
import logging
#TODO: change name to trace_method
def log_trace(args_fmt='', ret_fmt='', log_start=True, log_end=True):

    def decorator(meth: Callable):

        def wrapper(*args, **kwargs):
            global nesting
            indent = ' ' * nesting
            fmt="%s{self.__class__.__name__}.{callable.__name__}(%s)" % (indent, args_fmt)
            meth2 = meth
            if log_start:
                meth2 = log_on_start(logging.DEBUG, Template(fmt))(meth2) # TODO: inficient; do outside wrapper
            if log_end:
                meth2 = log_on_end(logging.DEBUG, Template(fmt + '-> ' + ret_fmt))(meth2)
                meth2 = log_on_error(logging.DEBUG, Template(fmt + ' ⚡{e!r}'), on_exceptions=Exception)(meth2)
            nesting+=1
            try:
                return meth2(*args, **kwargs)
            finally:
                nesting-=1
        return wrapper
    return decorator

#TODO: change name to trace_property
def log_property():
    def decorator(meth: Callable):

        def wrapper(self, value):
            global nesting
            indent = ' ' * nesting
            nesting+=1
            
            logging.debug('%s%s.%s=%s',indent, type(self).__name__, meth.__name__, value)
            meth(self, value)
            # TODO: handle exceptions
            nesting-=1
        return wrapper

    return decorator
    
