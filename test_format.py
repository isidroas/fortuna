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
    '<- {: <5}'
    >>> template
    '{: <1}: 0x{: <7}'
    """

    pointer_template = '<- {: <%d}' %  len(','.join(' ' * n_sources))
    template = '{: <%d}: 0x' % (2 if n_pools>10 else 1)
    template += '{: <%d}' % ( width - len(template.format('')) - len(pointer_template.format('')))

    return template, pointer_template
    

def format_pools(pools, sources=(), width = 27):
    """
    format is:

        number_of_pool: 0xCAFEE     <- source1, source2
    """
    template, pointer_template= _get_templates(len(pools), len(sources), width)
    res =''
    for index, pool in enumerate(pools):
        res+=template.format(index, pool.hex().upper())
        sources_pointing = list(_get_sources(index, sources))
        if sources_pointing:
            res += pointer_template.format(','.join(str(i) for i in sources_pointing))
        res+='\n'
    return res

def test_pools():

    res = format_pools(pools)
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
    print(res)
    assert res == """\
0: 0x00    
1: 0x0102  <- 0,1
"""

def test_overflow():
    res = format_pools(pools+[b'\x03'*10], width=20)
    # TODO: put length?
    assert res == """\
0: 0x00
1: 0x0102             <- 0,1
2: ..0303030303030303
"""
