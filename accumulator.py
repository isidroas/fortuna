from io import IOBase
from pathlib import Path
from time import time

from generator import Generator, sha_double_256

MINPOOLSIZE = 64


class FortunaSeedFileError(Exception):
    ...

class FortunaSeedFileEmpty(FortunaSeedFileError):
    ...


class Fortuna(object):
    def __init__(self, seed_file: IOBase | Path | None = None):
        self.pools = [bytearray() for i in range(32)]
        self.reseed_cnt = 0
        self.generator = Generator()
        self.last_seed = 0  # timestamp to calculate time difference

        if seed_file is None:
            self.seed_file = None
        elif isinstance(seed_file, IOBase):
            self.seed_file = seed_file
        else:
            self.seed_file = open(seed_file, "bw+")

        if self.seed_file is not None:
            try:
                self.update_seed_file()
            except FortunaSeedFileEmpty:
                print('given seed file is empty')

    def random_data(self, n: int):
        # n: Number of bytes of random data to generate
        if len(self.pools[0]) >= MINPOOLSIZE and (time() - self.last_seed) > 0.1:
            self.reseed_cnt += 1
            s = bytearray()
            for i in range(32):
                if self.reseed_cnt % 2**i == 0:
                    s += sha_double_256(self.pools[i])
                    del self.pools[i][:]
            self.generator.reseed(s)
            self.last_seed = time()

        # # commented because the exception will be already raised in generator.pseudo_randomdata
        # if self.reseed_cnt == 0:
        #     raise FortunaNotSeeded("Generate error, PRNG not seeded yet")

        return self.generator.pseudo_randomdata(n)

    def add_random_event(self, s: int, i: int, e: bytes):
        """
        s: Source number in range(256)
        i: Pool number in range(32)
        e: Event data
        """
        assert 1 <= len(e) <= 32
        assert 0 <= s <= 255
        assert 0 <= i <= 31
        self.pools[i] += bytes([s, len(e)]) + e

    def write_seed_file(self):
        self.seed_file.write(self.random_data(64))

    def update_seed_file(self):
        self.seed_file.seek(0)
        s = self.seed_file.read()
        if len(s) == 0:
            raise FortunaSeedFileEmpty()
        elif len(s) != 64:
            msg = "file size is %d instead of 64" % len(s)
            raise FortunaSeedFileError(msg)
        self.generator.reseed(s)
        self.seed_file.seek(0)
        self.seed_file.write(self.random_data(64))
