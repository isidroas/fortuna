import os
import contextlib
import enum
import sys
import termios
import tty
import cmd
import textwrap
from datetime import datetime
import readline


class Source(enum.IntEnum):
    TIMESTAMP = 0
    KEY_VALUE = 1


from accumulator import Fortuna
from generator import FortunaNotSeeded

fortuna = Fortuna(seed_file="./seed_file")

pool_counter = {
    Source.TIMESTAMP: 0,
    Source.KEY_VALUE: 0,
}

import subprocess
def get_columns():
    """
    variable $COLUMNS is not in the environment. It is a shell varible (see man bash)
    """
    return int(subprocess.run(['tput','cols'], capture_output=True).stdout)
    

@contextlib.contextmanager
def cbreak_mode():
    """
    source https://stackoverflow.com/a/42029045/16926605
    """
    print("Send SIGINT (Ctrl+c) to exit")
    if sys.version_info < (3, 12):
        mode = tty.tcgetattr(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
    else:
        mode = tty.setcbreak(sys.stdin.fileno())
    yield
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSAFLUSH, mode)


def add_entropy(source=Source.KEY_VALUE):
    with cbreak_mode():
        while True:
            try:
                char = sys.stdin.read(1)
            except KeyboardInterrupt:
                break
            if source is Source.KEY_VALUE:
                print("key: {!r}".format(char))
                fortuna.add_random_event(
                    Source.KEY_VALUE, pool_counter[Source.KEY_VALUE], char.encode()
                )
                pool_counter[Source.KEY_VALUE] += 1
                pool_counter[Source.KEY_VALUE] %= 32
            elif source is Source.TIMESTAMP:
                now = datetime.now()
                print("timestamp: {:%H:%M:%S.%f}".format(now))
                fortuna.add_random_event(
                    Source.TIMESTAMP,
                    pool_counter[Source.TIMESTAMP],
                    now.microsecond.to_bytes(20, "little"),  # log2(1e6) ≅ 20
                )
                pool_counter[Source.TIMESTAMP] += 1
                pool_counter[Source.TIMESTAMP] %= 32

        # TODO: call add_random_event here, only once?


class Cmd(cmd.Cmd):
    prompt = "(fortuna) "

    def do_random(self, arg):
        """
        random <n bytes>
        """
        nbytes = int(arg) if arg else 8
        try:
            data = fortuna.random_data(nbytes)
        except FortunaNotSeeded:
            print("Can not generate random data. Add entropy first")
        else:
            print("0x%s" % data.hex().upper())

    def do_add_entropy(self, arg):
        """
        add_entropy [timestamp|key_value]
        """
        source = Source[arg.upper()] if arg else Source.KEY_VALUE
        add_entropy(source)

    def do_update_seed_file(self, arg):
        fortuna.update_seed_file()

    def do_EOF(self, arg):
        return True

    def do_print_seed_file(self, arg):
        file = fortuna.seed_file
        file.seek(0)
        for line in textwrap.wrap(file.read().hex(' ', 2).upper(), width=40):
            print(line)

    def do_print_pools(self, arg):
        from test_format import format_pools
        print(format_pools(fortuna.pools,width = get_columns() ))

    def complete_add_entropy(self, text, line, begidx, endidx):
        if not text:
            return ["key_value", "timestamp"]
        elif text in "key_value":
            return ["key_value"]
        elif text in "timestamp":
            return ["timestamp"]
        return []


if __name__ == "__main__":
    # fortuna.update_seed_file()
    Cmd().cmdloop()
    try:
        fortuna.write_seed_file()
    except FortunaNotSeeded:
        print("not writing seed file")
