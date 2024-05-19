import logging
import math
from hashlib import sha256

LOG = logging.getLogger(__name__)
from formatter import Template
# from tracer import trace_method, trace_property, trace_function
from tracer2 import trace_method, trace_property, trace_function, TracedSet

from formatter import Template as T

from cryptography.hazmat.primitives import ciphers


class FortunaNotSeeded(Exception): ...

@trace_function(args_fmt=T('key=0x{key:25X}, plaintext=0x{plaintext:>25X}'), ret_fmt=T('0x{:^25X}'), merge=True)
def _encrypt(key: bytes, plaintext: bytes) -> bytes:
    # TODO: separate construction and encryption to save time in key scheduling?
    # TODO: use https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/#cryptography.hazmat.primitives.ciphers.modes.CTR ?
    cipher = ciphers.Cipher(ciphers.algorithms.AES(key), mode=ciphers.modes.ECB())
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext)

def encrypt(key: bytes, counter: int) -> bytes:
    return _encrypt(key, counter.to_bytes(16, "little"))


@trace_function(args_fmt=T('data=0x{data:25X}'), ret_fmt=T('0x{:25X}'), merge=True)
def sha_double_256(data: bytes) -> bytes:
    return sha256(sha256(data).digest()).digest()


class Generator(object):
    key = TracedSet(T('0x{:50X}'))
    counter = TracedSet()
    def __init__(self):
        self.key = b"\x00" * 32
        self.counter = 0

    @trace_function(args_fmt=T('seed=0x{seed:50X}'))
    def reseed(self, seed: bytes):
        self.key = sha_double_256(self.key + seed)
        self.counter += 1

    @trace_function(args_fmt='blocks={blocks}',ret_fmt=T('0x{:^50X}'))
    def generate_blocks(self, blocks: int) -> bytes:
        if self.counter == 0:
            raise FortunaNotSeeded("Generate error, PRNG not seeded yet")
        r = bytearray()
        for i in range(blocks):
            r += encrypt(self.key, self.counter)
            self.counter += 1
        return r

    @trace_function(args_fmt='bytes={nbytes}',ret_fmt=T('0x{:50X}'))
    def pseudo_randomdata(self, nbytes: int) -> bytes:
        assert 0 <= nbytes <= 2**20
        r = self.generate_blocks(math.ceil(nbytes / 16))[:nbytes]
        self.key = self.generate_blocks(2)
        return r


import contextlib


@contextlib.contextmanager
def log_known_exception():
    try:
        yield
    except FortunaNotSeeded as e:
        LOG.error(str(e))
