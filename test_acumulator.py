import pytest
from accumulator import Fortuna
from generator import FortunaNotSeeded


def test():
    """FortunaAccumulator.FortunaAccumulator"""
    fa = Fortuna()

    # This should fail, because we haven't seeded the PRNG yet
    with pytest.raises(FortunaNotSeeded):
        fa.random_data(1)

    # Spread some test data across the pools (source number 42)
    # This would be horribly insecure in a real system.
    for p in range(32):
        fa.add_random_event(42, p, b"X" * 32)
        assert 32 + 2 == len(fa.pools[p])

    # This should still fail, because we haven't seeded the PRNG with 64 bytes yet
    with pytest.raises(FortunaNotSeeded):
        fa.random_data(1)

    # Add more data
    for p in range(32):
        fa.add_random_event(42, p, b"X" * 32)
        assert (32 + 2) * 2 == len(fa.pools[p])

    # The underlying RandomGenerator should get seeded with Pool 0
    #   s = SHAd256(chr(42) + chr(32) + "X"*32 + chr(42) + chr(32) + "X"*32)
    #     = SHA256(h'edd546f057b389155a31c32e3975e736c1dec030ddebb137014ecbfb32ed8c6f')
    #     = h'aef42a5dcbddab67e8efa118e1b47fde5d697f89beb971b99e6e8e5e89fbf064'
    # The counter and the key before reseeding is:
    #   C_0 = 0
    #   K_0 = "\x00" * 32
    # The counter after reseeding is 1, and the new key after reseeding is
    #   C_1 = 1
    #   K_1 = SHAd256(K_0 || s)
    #       = SHA256(h'0eae3e401389fab86640327ac919ecfcb067359d95469e18995ca889abc119a6')
    #       = h'aafe9d0409fbaaafeb0a1f2ef2014a20953349d3c1c6e6e3b962953bea6184dd'
    # The first block of random data, therefore, is
    #   r_1 = AES-256(K_1, 1)
    #       = AES-256(K_1, h'01000000000000000000000000000000')
    #       = h'b7b86bd9a27d96d7bb4add1b6b10d157'
    # The second block of random data is
    #   r_2 = AES-256(K_1, 2)
    #       = AES-256(K_1, h'02000000000000000000000000000000')
    #       = h'2350b1c61253db2f8da233be726dc15f'
    # The third and fourth blocks of random data (which become the new key) are
    #   r_3 = AES-256(K_1, 3)
    #       = AES-256(K_1, h'03000000000000000000000000000000')
    #       = h'f23ad749f33066ff53d307914fbf5b21'
    #   r_4 = AES-256(K_1, 4)
    #       = AES-256(K_1, h'04000000000000000000000000000000')
    #       = h'da9667c7e86ba247655c9490e9d94a7c'
    #   K_2 = r_3 || r_4
    #       = h'f23ad749f33066ff53d307914fbf5b21da9667c7e86ba247655c9490e9d94a7c'
    # The final counter value is 5.

    # # pycrypto has a Pool object which is in charge of generating the hash
    # assert (
    #     "aef42a5dcbddab67e8efa118e1b47fde5d697f89beb971b99e6e8e5e89fbf064"
    #     == fa.pools[0].digest().hex()
    # )

    # assert fa.generator.K is None
    assert fa.generator.C == 0

    assert (
        "b7b86bd9a27d96d7bb4add1b6b10d157" "2350b1c61253db2f8da233be726dc15f"
    ) == fa.random_data(32).hex()
    assert (
        "f23ad749f33066ff53d307914fbf5b21da9667c7e86ba247655c9490e9d94a7c"
        == fa.generator.K.hex()
    )
    assert fa.generator.C == 5
