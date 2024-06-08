A didactic implementation of the Fortuna cryptographically secure pseudorandom number generator.

Examples only tested in Linux, but they should work also in macOS.

```
pip install .
python example.py
```

!(./docs/screenshot.png)

# Learn specification

- https://en.wikipedia.org/wiki/Fortuna_(PRNG)
- https://www.schneier.com/academic/paperfiles/fortuna.pdf

# Other implementations

- https://github.com/seehuhn/fortuna
  - Interface for entropy sources is easier for user/application.
    In `entropy.go` the following functions are defined:
    - `func (acc *Accumulator) addRandomEvent(source uint8, seq uint, data []byte)`
      It accepts a sequence number instead of pool index.
    - `func (acc *Accumulator) allocateSource() uint8`
      To ease that 2 sources doesn't share the same identifier.
      In line with the book: *allocate source numbers statically or dinamically*
    - `func (acc *Accumulator) NewEntropyDataSink() chan<- []byte`
    - `func (acc *Accumulator) NewEntropyTimeStampSink() chan<- time.Time`
- [pycrypto/Fortuna](https://github.com/pycrypto/pycrypto/tree/65b43bd4ffe2a48bdedae986b1a291f5a2cc7df7/lib/Crypto/Random/Fortuna)
  - pycrypto/lib/Crypto/Random/Fortuna/
    - FortunaAccumulator.py
    - FortunaGenerator.py
    - SHAd256.py
  - [SelfTest/Random/Fortuna](https://github.com/pycrypto/pycrypto/tree/65b43bd4ffe2a48bdedae986b1a291f5a2cc7df7/lib/Crypto/SelfTest/Random/Fortuna)
    - test_FortunaAccumulator.py
    - test_FortunaGenerator.py
    - test_SHAd256.py
  - https://nvd.nist.gov/vuln/detail/cve-2013-1445
  - `class FortunaPool`
  - `which_pool()` function separated from `random_data()` making it more testeable
  - seed file not supported
  - extensively commented
  - `class Util.Counter`
  - `FortunaGenerator.max_blocks_per_request` explanation
  - `AES` returns integers instead of bytes
- https://github.com/freebsd/freebsd-src/blob/main/sys/dev/random/fortuna.c
