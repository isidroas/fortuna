import io

import pytest

from accumulator import Fortuna, FortunaSeedFileError
from generator import FortunaNotSeeded


def test():
    f = Fortuna(seed_file=io.BytesIO())

    # the size is 0
    with pytest.raises(FortunaSeedFileError):
        f.update_seed_file()

    seed_file = io.BytesIO(b"\x00" * 64)
    f.seed_file = seed_file

    f.update_seed_file()

    assert seed_file.getvalue() != b"\x00" * 64
    assert len(seed_file.getvalue()) == 64

def test_autoupdate_if_not_empty():
    f = Fortuna(seed_file=io.BytesIO())

    with pytest.raises(FortunaNotSeeded):
        f.generator.generate_blocks(1)

    f = Fortuna(seed_file=io.BytesIO(b'\x00'*64))

    f.generator.generate_blocks(1) # it does not raise error
