import logging
import math
from hashlib import sha256

from logdecorator import log_on_start, log_on_end

LOG = logging.getLogger(__name__)
from formatter import Template, log_trace, log_property

from cryptography.hazmat.primitives import ciphers


class FortunaNotSeeded(Exception): ...


def encrypt(key: bytes, counter: int) -> bytes:
    # TODO: separate construction and encryption to save time in key scheduling?
    # TODO: use https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/#cryptography.hazmat.primitives.ciphers.modes.CTR ?
    cipher = ciphers.Cipher(ciphers.algorithms.AES(key), mode=ciphers.modes.ECB())
    encryptor = cipher.encryptor()
    return encryptor.update(counter.to_bytes(16, "little"))


def sha_double_256(data: bytes) -> bytes:
    return sha256(sha256(data).digest()).digest()


class Generator(object):
    def __init__(self):
        self.key = b"\x00" * 32
        self.counter = 0

    def reseed(self, seed: bytes):
        self.key = sha_double_256(self.key + seed)
        self.counter += 1

    @log_trace('blocks={blocks}','0x{result:50X}')
    def generate_blocks(self, blocks: int) -> bytes:
        if self.counter == 0:
            raise FortunaNotSeeded("Generate error, PRNG not seeded yet")
        r = bytearray()
        for i in range(blocks):
            r += encrypt(self.key, self.counter)
            self.counter += 1
        return r

    @log_trace('bytes={nbytes}','0x{result:50X}')
    def pseudo_randomdata(self, nbytes: int) -> bytes:
        assert 0 <= nbytes <= 2**20
        r = self.generate_blocks(math.ceil(nbytes / 16))[:nbytes]
        self.key = self.generate_blocks(2)
        return r

    @property
    def key(self):
        return self._key

    @key.setter
    @log_property('0x{:50X}')
    def key(self, value: bytes):
        self._key = value

    @property
    def counter(self):
        return self._counter

    @counter.setter
    @log_property()
    def counter(self, value: int):
        self._counter = value


import contextlib


@contextlib.contextmanager
def log_known_exception():
    try:
        yield
    except FortunaNotSeeded as e:
        LOG.error(str(e))
