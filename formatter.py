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
            source = sources.index(pool_index, source + 1)
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

    pointer_template = (
        (" <- {: <%d}" % len(",".join(" " * n_sources))) if n_sources else ""
    )
    template = "{: <%d}: 0x" % (2 if n_pools > 10 else 1)
    hex_width = width - len(template.format("")) - len(pointer_template.format(""))
    template += "{: <%d}" % hex_width

    return template, pointer_template, hex_width


from enum import StrEnum, auto


class Trim(StrEnum):
    LEFT = auto()
    CENTER = auto()
    RIGHT = auto()


def format_overflow(data: str, max_width, trim=Trim.LEFT, print_total=False):
    """
    >>> format_overflow('3031323334', max_width = 10)
    '3031323334'
    >>> format_overflow('3031323334', max_width = 9)
    '<+4...>34'
    >>> format_overflow('3031323334', max_width = 9, print_total=True)
    '<=5...>34'
    >>> format_overflow('3031323334', max_width = 8)
    '<+5...>'
    >>> format_overflow('3031323334', max_width = 6)
    Traceback (most recent call last):
    ValueError: even trimmed descriptor with length 7 does not fit in max width 6

    >>> format_overflow('3031323334', max_width = 9)
    '<+4...>34'
    >>> format_overflow('3031323334353637383930', max_width = 10)
    '<+10...>30'

    >>> format_overflow('30313233343536373839', max_width = 18, trim='left')
    '<+ 5...>3536373839'
    >>> format_overflow('30313233343536373839', max_width = 18, trim='right')
    '3031323334<...+ 5>'

    >>> format_overflow('30313233343536373839', max_width = 18, trim='center')
    '303132<...+ 5>3839'
    """
    if len(data) <= max_width:
        return data

    len_bytes, rest = divmod(len(data), 2)
    assert rest == 0, "not hexa"

    fmt = "%s{: >%d}" % ('=' if print_total else '+', len(str(len_bytes)))
    if trim == Trim.LEFT:
        fmt = '<%s...>' % fmt
    else:
        fmt = '<...%s>' % fmt
    visible_length = max_width - len(fmt.format(0))

    if visible_length<0:
        msg = 'even trimmed descriptor with length %d does not fit in max width %d' % (len(fmt.format(0)), max_width )
        raise ValueError(msg)

    visible_length_bytes, rest = divmod(visible_length, 2)
    # if max_width==6:
    #     print(locals())
        # breakpoint()
    if rest :
        # avoid unpair an hexa byte
        visible_length -=1 
        # downside: the whole max_width wont'b be leveraged

    # print(visible)
    # print(len(fmt.format(0)))
    trimmed_descriptor = fmt.format(len_bytes if print_total else len_bytes - visible_length_bytes)
    if trim == Trim.LEFT:
        return trimmed_descriptor + data[len(data)-visible_length:] # https://stackoverflow.com/questions/11337941/python-negative-zero-slicing
    elif trim == Trim.CENTER:
        # avoid unpair an hexa byte
        half, rest = divmod(visible_length_bytes, 2)
        return data[: (half + rest) * 2] + trimmed_descriptor + data[-half * 2 :]
    return data[:visible_length] + trimmed_descriptor


def format_pools(pools, sources=(), width=27):
    """
    format is:

        number_of_pool: 0xCAFEE     <- source1, source2
    """
    template, pointer_template, hex_width = _get_templates(
        len(pools), len(sources), width
    )
    res = ""
    for index, pool in enumerate(pools):
        data = pool.hex().upper()
        res += template.format(index, format_overflow(data, hex_width))
        sources_pointing = list(_get_sources(index, sources))
        if sources_pointing:
            res += pointer_template.format(",".join(str(i) for i in sources_pointing))
        res += "\n"
    return res


import string
from functools import partial
import re

PATTERN = re.compile(r"(?P<align><|\^|>)?(?P<alternate>#)?(?P<width>\d*)?X")


class Formatter(string.Formatter):
    def format_field(self, value, format_spec):
        if isinstance(value, (bytes, bytearray)):
            if match := PATTERN.search(format_spec):
                format_spec = format_spec[:match.start()] + format_spec[match.end():]
                value = value.hex().upper()
                if width := match.group("width"):
                    align = Trim.LEFT
                    align = {
                        "<": Trim.LEFT,
                        ">": Trim.RIGHT,
                        "^": Trim.CENTER,
                        None: Trim.LEFT,
                    }[match.group("align")]
                    value = format_overflow(value, int(width), align, print_total = match.group("alternate") is None)
        return super().format_field(value, format_spec)


from collections import UserString


class Template(UserString):
    """
    inspired in https://github.com/mkdocs/mkdocs/blob/53fec50e57f6bad152ad589a83ae83d1cd72b2f5/mkdocs/config/config_options.py#L640
    """

    def format(self_, *args, **kwargs):
        fmt = Formatter()
        return fmt.format(str(self_), *args, **kwargs)


def test_formatter():
    fmt = Formatter()
    assert "0x0102" == fmt.format("0x{:X}", b"\x01\x02")

    b = bytes.fromhex("30313233343536373839")
    assert "0x" + format_overflow(b.hex().upper(), 18, print_total=True) == fmt.format("0x{:18X}", b)
    assert "0x" + format_overflow(b.hex().upper(), 18, print_total=False) == fmt.format("0x{:#18X}", b)
    assert "0x" + format_overflow(b.hex().upper(), 18, 'right', print_total=True) == fmt.format("0x{:>18X}", b)


def test_regex():
    m = PATTERN.match("50")
    assert m is None

    m = PATTERN.match("50X")
    assert m.group("align") is None
    assert m.group("width") == "50"
    assert m.group("alternate") is None

    m = PATTERN.match("<#50X")
    assert m.group("align") == '<'
    assert m.group("width") == "50"
    assert m.group("alternate") == "#"

from rich.highlighter import RegexHighlighter, _combine_regex
class ReprHighlighter(RegexHighlighter):
    """Copied from rich source"""

    base_style = "repr."
    highlights = [
        r"(?P<tag_start><)(?P<tag_name>[-\w.:|]*)(?P<tag_contents>[\w\W]*)(?P<tag_end>>)",
        r'(?P<attrib_name>[\w_\.]{1,50})=(?P<attrib_value>"?[\w_]+"?)?',
        r"(?P<brace>[][{}()])",
        r"(?P<call>[\w.]*?)\(",
        r"(?P<number>0x[a-fA-F0-9]*(\<\.*[+=] *\d+ *\.*\>)?[a-fA-F0-9]*)",
        r"(?<![\\\w])(?P<str>b?'''.*?(?<!\\)'''|b?'.*?(?<!\\)'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
        # r"(?P<ellipsis>\.\.\.)",
        r"\b(?P<bool_true>True)\b|\b(?P<bool_false>False)\b|\b(?P<none>None)\b",
        r"(^|\s)(?P<ret_arrow>->)[\s$]",
        r"(^|\s)(?P<ret_exc>-X)\s",
        # TODO: use _combine_regex as superclass?
    ]
