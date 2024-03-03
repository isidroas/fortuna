import io

import pytest


@pytest.fixture
def seed_file(tmp_path):
    return tmp_path / "seed_file"


@pytest.fixture
def seed_file_empty(seed_file):
    seed_file.touch()
    return seed_file


@pytest.fixture
def seed_file_filled(seed_file):
    seed_file.write_bytes(b"\x00" * 64)
    return seed_file


def test_std_fopen(seed_file):
    file = open(seed_file, "ba+")
    assert file.read() == b""


def test_std_fopen2(seed_file_empty):
    file = open(seed_file_empty, "ba+")
    assert file.read() == b""


def test_std_fopen3(seed_file_filled):
    file = open(seed_file_filled, "ba+")
    print(file.tell())
    assert file.read() == b""
    file.seek(0)
    assert file.read() == b"\x00" * 64

    # this will be ignored since. man (2) open: "Before each write(2), the file offset is positioned at the end of the file"
    file.seek(0)
    file.write(b"\x01" * 64)
    # breakpoint()
    assert file.tell() == 128  #

    file.seek(0)
    # I expected this:
    # assert file.read() == b'\x01' * 64
    assert file.read() == b"\x00" * 64 + b"\x01" * 64

    file.seek(0)
    file.truncate()
    file.write(b"\x02" * 64)
    file.seek(0)
    assert file.read() == b"\x02" * 64


def test_std_fopen_strange(seed_file_filled):
    file = open(seed_file_filled, "ba+")
    print(file.tell())
    assert file.read() == b""
    file.seek(0)
    assert file.read() == b"\x00" * 64

    # this will be ignored since. man (2) open: "Before each write(2), the file offset is positioned at the end of the file"
    file.seek(0)
    file.write(b"\x01" * 64)
    assert file.tell() == 128  #

    file.seek(0)
    # I expected this:
    # assert file.read() == b'\x01' * 64
    assert file.read() == b"\x00" * 64 + b"\x01" * 64

    file.seek(0)
    file.truncate()
    file.write(b"\x02" * 64)
    file.seek(0)
    assert file.read() == b"\x02" * 64


def test_std_fopen4(seed_file):
    with pytest.raises(OSError):
        open(seed_file, "br+")


def test_std_fopen5(seed_file_empty):
    file = open(seed_file_empty, "br+")
    assert file.read() == b""


def test_std_fopen6(seed_file_filled):
    file = open(seed_file_filled, "br+")
    assert file.tell() == 0
    assert file.read() == b"\x00" * 64
    assert file.tell() == 64

    file.seek(0)
    file.write(b"\x01" * 64)

    file.seek(0)
    assert file.read() == b"\x01" * 64
    # assert file.read() == b'\x00' * 64 + b'\x01' * 64

    file.seek(0)
    # file.truncate()
    file.write(b"\x02" * 64)

    file.seek(0)
    assert file.read() == b"\x02" * 64

    file.write(b"\x03" * 64)
    assert file.tell() == 128

    file.seek(64)
    assert file.read() == b"\x03" * 64
