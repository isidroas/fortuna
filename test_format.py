pools = [
        b'\x00',
        b'\x01\x02',
]

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
    >>> template, pointer_template= _get_templates(5, 3, width=20)
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

def test_pools():

    res = format_pools(pools, width=17)
    assert res == """\
0: 0x00        
1: 0x0102      
"""

def test_source_pointer():
    res = format_pools(pools, [1, 0], width=17)
    assert res == """\
0: 0x00    <- 1  
1: 0x0102  <- 0  
"""

def test_source_pointer_overlaped():
    res = format_pools(pools, [1, 1], width=17)
    assert res == """\
0: 0x00   
1: 0x0102  <- 0,1
"""

pools2 = [
        b'\x00',
        b'\x01\x02\x03\x04\x05',
]

def test_overflow():
    res = format_pools(pools2, [1, 0], width=20)
    assert res == """\
0: 0x00       <- 1  
1: 0x(+4)..05 <- 0  
"""

# TODO: test empty
