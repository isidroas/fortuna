from rich.highlighter import RegexHighlighter
from rich.style import Style
from rich.theme import Theme


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
        r"(^|\s)(?P<ret_exc>-X)\s(?P<exc>\w+)?",
        # TODO: use _combine_regex as superclass?
    ]


theme = Theme(
    {
        "repr.ret_arrow": Style(color="blue"),
        "repr.ret_exc": Style(color="bright_red", bold=False),
        "repr.exc": Style(color="bright_red", bold=True),
    }
)
