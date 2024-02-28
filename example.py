import sys
import time
from datetime import datetime

# source: https://stackoverflow.com/questions/3670323/setting-smaller-buffer-size-for-sys-stdin#answer-34123854
import tty
tty.setcbreak(sys.stdin.fileno())

from accumulator import Fortuna

fortuna = Fortuna(seed_file = './seed_file')

while True:
    try:
        char = sys.stdin.read(1)
    except KeyboardInterrupt:
        break
    print('key: {!r}'.format(char))
    now = datetime.now()
    print('timestamp: {:%H:%M:%S.%f}'.format(now))

    # TODO: decide other pools
    fortuna.add_random_event(0, 0, char.encode())
    fortuna.add_random_event(0, 0, now.microsecond.to_bytes(20, 'little') )

fortna.write_seed_file()
