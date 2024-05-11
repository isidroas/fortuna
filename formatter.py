
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
    
from enum import StrEnum, auto
class Trim(StrEnum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()

def format_overflow(data: str, max_width, trim = Trim.LEFT):
    """
    >>> format_overflow('3031323334', max_width = 10)
    '3031323334'
    >>> format_overflow('3031323334', max_width = 8)
    '(+4)..34'
    >>> format_overflow('3031323334', max_width = 9)
    '(+4)...34'
    >>> format_overflow('3031323334353637383930', max_width = 10)
    '(+10)...30'

    >>> format_overflow('30313233343536373839', max_width = 18, trim='left')
    '(+5 )...3536373839'
    >>> format_overflow('30313233343536373839', max_width = 18, trim='right')
    '3031323334...(+5 )'

    >>> format_overflow('30313233343536373839', max_width = 18, trim='center')
    '3031...(+5 )3839'
    """
    if len(data)<= max_width:
        return data

    len_bytes, rest = divmod(len(data),2)
    assert rest==0, 'not hexa'

    fmt ='(+{: <%d})'% len(str(len_bytes))
    remaining = max_width - len(fmt.format(0))
    dots = '...' if remaining%2 else '..'
    if trim == Trim.LEFT:
        fmt += dots
    else:
        fmt = dots + fmt
    remaining = max_width - len(fmt.format(0))

    remaining_bytes, rest = divmod(remaining, 2)
    assert rest==0

    # print(remaining)
    # print(len(fmt.format(0)))
    remaining_info = fmt.format(len_bytes-remaining_bytes)
    if trim == Trim.LEFT:
        return  remaining_info+ data[-remaining:]
    elif trim == Trim.CENTER:
        # avoid unpair an hexa byte
        half, rest = divmod(remaining_bytes, 2)
        return data[:(half+rest)*2] + remaining_info + data[-half*2:]
    return  data[:remaining] + remaining_info


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

