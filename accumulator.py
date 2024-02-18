from time import time

from generator import Generator, sha_double_256, FortunaNotSeeded

MINPOOLSIZE = 64



class Fortuna(object):
    def __init__(self):
        self.pools = [bytearray() for i in range(32)]
        self.reseed_cnt = 0
        self.generator = Generator()
        self.last_seed = 0  # timestamp to calculate time difference

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

    def write_seedfile(self, f):
        with open(f, "wb") as fp:
            fp.write(self.randomdata(64))

    def update_seedfile(
        self, f
    ):  # TODO: for tests is better to accept abstract io.StringIO. Open file with open(.., '+'). Inspirado en la implementación en go
        s = open(f).read()
        assert len(s) == 64
        self.generator.reseed(s)
        with open(f, "wb") as fp:
            fp.write(self.randomdata(64))
