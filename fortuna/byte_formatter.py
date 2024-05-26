
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

    fmt = "%s{: >%d}" % ("=" if print_total else "+", len(str(len_bytes)))
    if trim == Trim.LEFT:
        fmt = "<%s...>" % fmt
    else:
        fmt = "<...%s>" % fmt
    visible_length = max_width - len(fmt.format(0))

    if visible_length < 0:
        msg = "even trimmed descriptor with length %d does not fit in max width %d" % (
            len(fmt.format(0)),
            max_width,
        )
        raise ValueError(msg)

    visible_length_bytes, rest = divmod(visible_length, 2)
    # if max_width==6:
    #     print(locals())
    # breakpoint()
    if rest:
        # avoid unpair an hexa byte
        visible_length -= 1
        # downside: the whole max_width wont'b be leveraged

    # print(visible)
    # print(len(fmt.format(0)))
    trimmed_descriptor = fmt.format(
        len_bytes if print_total else len_bytes - visible_length_bytes
    )
    if trim == Trim.LEFT:
        return (
            trimmed_descriptor + data[len(data) - visible_length :]
        )  # https://stackoverflow.com/questions/11337941/python-negative-zero-slicing
    elif trim == Trim.CENTER:
        # avoid unpair an hexa byte
        half, rest = divmod(visible_length_bytes, 2)
        return data[: (half + rest) * 2] + trimmed_descriptor + data[-half * 2 :]
    return data[:visible_length] + trimmed_descriptor




import re
import string

PATTERN = re.compile(r"(?P<align><|\^|>)?(?P<alternate>#)?(?P<width>\d*)?X")


class Formatter(string.Formatter):
    def format_field(self, value, format_spec):
        if isinstance(value, (bytes, bytearray)):
            if match := PATTERN.search(format_spec):
                format_spec = format_spec[: match.start()] + format_spec[match.end() :]
                value = value.hex().upper()
                if width := match.group("width"):
                    align = Trim.LEFT
                    align = {
                        "<": Trim.LEFT,
                        ">": Trim.RIGHT,
                        "^": Trim.CENTER,
                        None: Trim.LEFT,
                    }[match.group("align")]
                    value = format_overflow(
                        value,
                        int(width),
                        align,
                        print_total=match.group("alternate") is None,
                    )
        return super().format_field(value, format_spec)


from collections import UserString


class Template(UserString):
    """
    inspired in https://github.com/mkdocs/mkdocs/blob/53fec50e57f6bad152ad589a83ae83d1cd72b2f5/mkdocs/config/config_options.py#L640
    """

    def format(self_, *args, **kwargs):
        fmt = Formatter()
        return fmt.format(str(self_), *args, **kwargs)



