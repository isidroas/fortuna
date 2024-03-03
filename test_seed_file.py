import io

import pytest

from accumulator import Fortuna, FortunaSeedFileError
from generator import FortunaNotSeeded
# TODO: make test more unitary. Create fixture of Fortuna with preadded entrypy


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

def test_write():
    """
    test that it is called to seek(0)
    """
    seed_file = io.BytesIO(b"\x00" * 64)
    f = Fortuna(seed_file=seed_file)
    f.write_seed_file()
    f.write_seed_file()
    assert seed_file.getvalue() != b"\x00" * 64
    assert len(seed_file.getvalue()) == 64

def test_autoupdate_if_not_empty():
    f = Fortuna(seed_file=io.BytesIO())

    with pytest.raises(FortunaNotSeeded):
        f.generator.generate_blocks(1)

    f = Fortuna(seed_file=io.BytesIO(b'\x00'*64))

    f.generator.generate_blocks(1) # it does not raise error

# def test_real_file(tmp_path):
#     """
#     file is overwrited in each updated, not appended
#     in other words, call open(mode='r+')
#     """
#     seed_path = tmp_path / 'seed_file'
#     seed_path.touch()

#     f = Fortuna(seed_file=seed_path)
#     with pytest.raises(FortunaNotSeeded):
#         f.generator.generate_blocks(1)

#     seed_path.write_bytes(b'\x00' * 64)
#     f.update_seed_file()
#     f.generator.generate_blocks(1)
#     f.write_seed_file()
#     f.write_seed_file()

#     del f
#     f = Fortuna(seed_file=seed_path)
#     f.generator.generate_blocks(1)
#     f.write_seed_file()
#     # f.seed_file.close()
#     # f.update_seed_file()

#     # del f
#     # f = Fortuna(seed_file=seed_path)
#     # f.generator.generate_blocks(1)

#     assert seed_path.lstat().st_size == 64
