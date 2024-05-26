from fortuna.pool_formatter import *
from fortuna.byte_formatter import *

pools = [
    b"\x00",
    b"\x01\x02",
]


def test_pools():

    res = format_pools(pools, width=17)
    assert (
        res
        == """\
0: 0x00          
1: 0x0102        
"""
    )


def test_source_pointer():
    res = format_pools(pools, [1, 0], width=17)
    assert (
        res
        == """\
0: 0x00    <- 1  
1: 0x0102  <- 0  
"""
    )


def test_source_pointer_overlaped():
    res = format_pools(pools, [1, 1], width=17)
    assert (
        res
        == """\
0: 0x00   
1: 0x0102  <- 0,1
"""
    )


pools2 = [
    b"\x00",
    b"\x01\x02\x03\x04\x05",
]


def test_overflow():
    res = format_pools(pools2, [1, 0], width=20)
    assert (
        res
        == """\
0: 0x00       <- 1  
1: 0x(+4)..05 <- 0  
"""
    )


def test_pools_empty():

    res = format_pools([b"", b""], width=17)
    assert (
        res
        == """\
0: 0x            
1: 0x            
"""
    )


def test_bytes_template():
    template = Template("0x{:X}")
    assert "0x12AB" == template.format(b"\x12\xab")

    template = Template("0x{:8X}")
    assert "0x(+4)..35" == template.format(b"12345")


def test_formatter():
    fmt = Formatter()
    assert "0x0102" == fmt.format("0x{:X}", b"\x01\x02")

    b = bytes.fromhex("30313233343536373839")
    assert "0x" + format_overflow(b.hex().upper(), 18, print_total=True) == fmt.format(
        "0x{:18X}", b
    )
    assert "0x" + format_overflow(b.hex().upper(), 18, print_total=False) == fmt.format(
        "0x{:#18X}", b
    )
    assert "0x" + format_overflow(
        b.hex().upper(), 18, "right", print_total=True
    ) == fmt.format("0x{:>18X}", b)


def test_regex():
    m = PATTERN.match("50")
    assert m is None

    m = PATTERN.match("50X")
    assert m.group("align") is None
    assert m.group("width") == "50"
    assert m.group("alternate") is None

    m = PATTERN.match("<#50X")
    assert m.group("align") == "<"
    assert m.group("width") == "50"
    assert m.group("alternate") == "#"
