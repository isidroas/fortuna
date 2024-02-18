import io

import pytest

from accumulator import Fortuna, FortunaSeedFileError


def test():
    f = Fortuna()
    f.seed_file = io.BytesIO()

    # the size is 0
    with pytest.raises(FortunaSeedFileError):
        f.update_seed_file()

    seed_file = io.BytesIO(b"\x00" * 64)
    f.seed_file = seed_file

    f.update_seed_file()

    assert seed_file.getvalue() != b"\x00" * 64
