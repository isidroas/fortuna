from fortuna.formatter import *
pools = [
        b'\x00',
        b'\x01\x02',
]


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

def test_pools_empty():

    res = format_pools([b'', b''], width=17)
    assert res == """\
0: 0x            
1: 0x            
"""

def test_bytes_template():
    template = Template('0x{:X}')
    assert '0x12AB' == template.format(b'\x12\xab')

    template = Template('0x{:8X}')
    assert '0x(+4)..35' == template.format(b'12345')
