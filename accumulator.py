import logging

from io import IOBase
from pathlib import Path
from time import time

import generator
from generator import Generator, sha_double_256
from logdecorator import log_on_start, log_on_end, log_on_error
from formatter import Template

MINPOOLSIZE = 64

LOG = logging.getLogger(__name__)


class FortunaSeedFileError(Exception): ...


class FortunaSeedFileEmpty(FortunaSeedFileError): ...


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
            if not isinstance(seed_file, Path):
                seed_file = Path(seed_file)
            if not seed_file.exists():
                seed_file.touch()
                LOG.info('Created seed file "%s"', seed_file)
            else:
                LOG.info('Loading existing seed file "%s"', seed_file)
            self.seed_file = open(
                seed_file, "r+b"
            )  # if using r+, the stream is positioned at the end (depends on platforms), but the file is not created if it does't exist. I would need `flags = O_RDWR | O_CREAT`

        if self.seed_file is not None:
            try:
                self.update_seed_file()
            except FortunaSeedFileEmpty:
                LOG.info('seed file ("%s") is empty', seed_file)

    def random_data(self, nbytes: int):
        if len(self.pools[0]) >= MINPOOLSIZE and (time() - self.last_seed) > 0.1:
            self.reseed_cnt += 1
            s = bytearray()
            for i in range(32):
                if self.reseed_cnt % 2**i == 0:
                    s += sha_double_256(self.pools[i])
                    del self.pools[i][:]
                else:
                    break  # optimization sugested by the book
            self.generator.reseed(s)
            self.last_seed = time()

        # # commented because the exception will be already raised in generator.pseudo_randomdata
        # if self.reseed_cnt == 0:
        #     raise FortunaNotSeeded("Generate error, PRNG not seeded yet")

        return self.generator.pseudo_randomdata(nbytes)

    @log_on_end(logging.INFO, Template("added {source!r} to pool {pool}: 0x{data:X}"))
    def add_random_event(self, source: int, pool: int, data: bytes):
        assert 1 <= len(data) <= 32
        assert 0 <= source <= 255
        assert 0 <= pool <= 31
        self.pools[pool] += bytes([source, len(data)]) + data
        # not doing the hash here:
        #  x it is a waste of memory
        #  ✓ save time to entropy sources, which are typically real-time drivers
        #  ✓ simpler because you don't have to maintain a counter, just do `len(pool)`

    def write_seed_file(self):
        """
        IMO this should only called by APP when seed file is empty, the first time that is seeded at least at the end
        """
        # TODO: add __del__ method that call this or update depending on existence?
        self._overwrite_seed_file(self.random_data(64))

    def update_seed_file(self):
        """
        IMO this should be called periodically or at the end
        """
        s = self._read_seed_file()
        self.generator.reseed(s)
        self._overwrite_seed_file(self.random_data(64))

    # @log_on_end(logging.DEBUG, Template("read seed file 0x{result:50X}"))
    @log_on_end(logging.DEBUG, Template("{self.__class__.__name__}.{callable.__name__}() -> 0x{result:50X}"))
    @log_on_error(logging.DEBUG, Template("{self.__class__.__name__}.{callable.__name__}() -> ''"), on_exceptions=FortunaSeedFileEmpty)
    def _read_seed_file(self):
        self.seed_file.seek(0)
        s = self.seed_file.read()
        if len(s) == 0:
            raise FortunaSeedFileEmpty()
        elif len(s) != 64:
            msg = "file size is %d instead of 64" % len(s)
            raise FortunaSeedFileError(msg)
        return s

    # @log_on_end(logging.DEBUG, Template("write seed file 0x{data:50X}"))
    @log_on_end(logging.DEBUG, Template("{self.__class__.__name__}.{callable.__name__}('0x{data:50X}')"))
    def _overwrite_seed_file(self, data):
        self.seed_file.seek(0)
        self.seed_file.write(data)


import contextlib


@contextlib.contextmanager
def log_known_exception():
    try:
        with generator.log_known_exception():
            yield
    except FortunaSeedFileError as e:
        LOG.error(str(e))
