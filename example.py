import sys
import time
import contextlib
import enum
from datetime import datetime

class Source(enum.IntEnum):
    TIMESTAMP = 0
    KEY_VALUE = 1

# source: https://stackoverflow.com/questions/3670323/setting-smaller-buffer-size-for-sys-stdin#answer-34123854
import tty
import termios

from accumulator import Fortuna

fortuna = Fortuna(seed_file = './seed_file')

pool_counter = {
    Source.TIMESTAMP: 0,
    Source.KEY_VALUE: 0,
}
# pool_key_value = 0
# pool_timestamp = 0

@contextlib.contextmanager
def cbreak_mode():
    mode = tty.setcbreak(sys.stdin.fileno())
    yield
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, mode)

def add_entropy(timestamp=True, add_char=True):
    print('Send SIGINT (Ctrl+c) to stop adding entropy')
    with cbreak_mode():
        while True:
            try:
                char = sys.stdin.read(1)
            except KeyboardInterrupt:
                break
            if add_char:
                print('key: {!r}'.format(char))
                fortuna.add_random_event(Source.KEY_VALUE, pool_counter[Source.KEY_VALUE], char.encode())
                pool_counter[Source.KEY_VALUE]+=1
            if timestamp:
                now = datetime.now()
                print('timestamp: {:%H:%M:%S.%f}'.format(now))
                fortuna.add_random_event(Source.TIMESTAMP, pool_counter[Source.TIMESTAMP], now.microsecond.to_bytes(20, 'little') )
                pool_counter[Source.TIMESTAMP]+=1

def get_random(n=8):
    data = fortuna.random_data(n)
    print('0x%s' % data.hex().upper())

add_entropy()
get_random()
fortuna.update_seed_file()
test = input('press some key: ')
print(test)
fortuna.write_seed_file() # TODO: handle NotSeeded
