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


from fortuna.byte_formatter import format_overflow


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

