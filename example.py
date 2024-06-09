import cmd
import contextlib
import enum
import logging
import math
import subprocess
import sys
import termios
import textwrap
import time
import tty

from fortuna import Fortuna, FortunaSeedFileError
from fortuna.generator import FortunaNotSeeded
from fortuna.pool_formatter import format_pools

LOG = logging.getLogger(__name__)


class Source(enum.IntEnum):
    TIMESTAMP = 0
    KEY_VALUE = 1


pool_counter = {
    Source.TIMESTAMP: 0,
    Source.KEY_VALUE: 0,
}


def configure_logging():
    from rich.console import Console
    from rich.logging import RichHandler

    from fortuna.tracer_highligher import ReprHighlighter, theme

    console = Console(theme=theme)
    handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        log_time_format="[%X]",
        tracebacks_show_locals=True,
        highlighter=ReprHighlighter(),
        console=console,
        show_path=False,  # it has less info using logdecorator. I can't overwirte %(module)s:%(lineno) even with functools.wrap
    )
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[handler],
        # format="%(relativeCreated)d %(message)s",
        format="%(message)s",
    )


def get_columns():
    """
    variable $COLUMNS is not in the environment. It is a shell varible (see man bash)
    """
    return int(subprocess.run(["tput", "cols"], capture_output=True).stdout)


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
                fortuna.add_random_event(
                    Source.KEY_VALUE, pool_counter[Source.KEY_VALUE], char.encode()
                )
                pool_counter[Source.KEY_VALUE] += 1
                pool_counter[Source.KEY_VALUE] %= 32
            elif source is Source.TIMESTAMP:
                assert time.clock_getres(time.CLOCK_MONOTONIC_RAW) >= 1e-9
                nanoseconds = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
                seconds = int(nanoseconds / 1e9)
                nbytes = math.ceil(int(1e9).bit_length() / 8)

                fortuna.add_random_event(
                    Source.TIMESTAMP,
                    pool_counter[Source.TIMESTAMP],
                    # only add nanosecond portion
                    int(nanoseconds - seconds * 1e9).to_bytes(nbytes, "little"),
                )
                pool_counter[Source.TIMESTAMP] += 1
                pool_counter[Source.TIMESTAMP] %= 32


@contextlib.contextmanager
def log_known_exception():
    try:
        yield
    except (FortunaNotSeeded, FortunaSeedFileError) as e:
        LOG.error(str(e))


class Cmd(cmd.Cmd):
    prompt = "(fortuna) "

    def do_random(self, arg):
        """
        random <n bytes>
        """
        nbytes = int(arg) if arg else 8

        # TODO: use this in all commands. Common place: cmd.Cmd.cmdloop. Also pop last frame from backtrace
        with log_known_exception():
            # don't doing anything with the return value because library
            # logging already displays it
            fortuna.random_data(nbytes)

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
        for line in textwrap.wrap(file.read().hex(" ", 2).upper(), width=40):
            print(line)

    def do_print_pools(self, arg):
        print(
            format_pools(
                fortuna.pools, list(pool_counter.values()), width=get_columns()
            )
        )

    def complete_add_entropy(self, text, line, begidx, endidx):
        if not text:
            return ["key_value", "timestamp"]
        elif text in "key_value":
            return ["key_value"]
        elif text in "timestamp":
            return ["timestamp"]
        return []


if __name__ == "__main__":
    configure_logging()
    fortuna = Fortuna(seed_file="./seed_file")
    Cmd().cmdloop()
    try:
        fortuna.write_seed_file()
    except FortunaNotSeeded:
        LOG.info("not writing seed file since not seeded")
