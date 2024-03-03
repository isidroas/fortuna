pools = [
        b'\x00',
        b'\x01\x02',
]
def test_pools():

    res = format_pools(pools)
    assert res == """\
0: 0x00
1: 0x0102
    """

def test_source_pointer()
    res = format_pools(pools, [1, 0])
    assert res == """\
0: 0x00       <- 1
1: 0x0102     <- 0
    """

def test_source_pointer()
    res = format_pools(pools, [1, 1])
    assert res == """\
0: 0x00
1: 0x0102     <- 0,1
    """

def test_overflow()
    res = format_pools(pools+[b'\x03'*], width=20)
    assert res == """\
0: 0x00
1: 0x0102             <- 0,1
2: ..0303030303030303
    """
