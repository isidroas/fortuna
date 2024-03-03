import contextlib
import enum
import sys
import termios
import tty
import cmd
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


@contextlib.contextmanager
def cbreak_mode():
    # source: https://stackoverflow.com/questions/3670323/setting-smaller-buffer-size-for-sys-stdin#answer-34123854
    print("Send SIGINT (Ctrl+c) to exit")
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
            elif source is Source.TIMESTAMP:
                now = datetime.now()
                print("timestamp: {:%H:%M:%S.%f}".format(now))
                fortuna.add_random_event(
                    Source.TIMESTAMP,
                    pool_counter[Source.TIMESTAMP],
                    now.microsecond.to_bytes(20, "little"), # log2(1e6) ≅ 20
                )
                pool_counter[Source.TIMESTAMP] += 1

        # TODO: call add_random_event here, only once?


class Cmd(cmd.Cmd):
    def do_random(self, arg):
        """
        random <n bytes>
        """
        nbytes = int(arg) if arg else 8
        try:
            data = fortuna.random_data(nbytes)
        except FortunaNotSeeded:
            print('Can not generate random data. Add entropy first')
        else:
            print("0x%s" % data.hex().upper())

    def do_add_entropy(self, arg):
        """
        add_entropy [timestamp|key_value]
        """
        source = Source[arg.upper()] if arg else Source.KEY_VALUE
        add_entropy(source)

    def complete_add_entropy(self, text, line, begidx, endidx):
        if not text:
            return ['key_value', 'timestamp']
        elif text in 'key_value':
            return ['key_value']
        elif text in 'timestamp':
            return ['timestamp']
        return []



if __name__ == "__main__":
    # fortuna.update_seed_file()
    Cmd().cmdloop()
    fortuna.write_seed_file()  # TODO: handle NotSeeded
