import itertools
import logging
import os
import re
import time


logger = logging.getLogger(__name__)


try:
    from rich import print
    from rich.highlighter import Highlighter
    from snisp.utils import RichHighlighter as LogHighlighter
except ModuleNotFoundError:
    from snisp.utils import DummyHighlighter as LogHighlighter
    logger.warning('"rich" not installed. Defaulting to standard print.')


def tail(log_file, *, regexes=None, sleep=1):
    highlighter = LogHighlighter()
    if regexes is None:
        regexes = [
            (
                re.compile(r'https://(api)\.(spacetraders)\.io\/.*$'),
                itertools.cycle(['blue on white', 'green'])
            )
        ]
    for regex, colors in regexes:
        highlighter.regexes.append((regex, colors))
    if not os.path.isfile(log_file):
        logger.error(f'Logfile {log_file} does not exist. Cannot tail.')
        return
    try:
        _ = open(log_file, 'rb')
    except PermissionError:
        logger.error(
            f'User does not have permission to open {log_file}. Cannot tail.'
        )
        return
    with open(log_file, 'rb') as f:
        f.seek(0, os.SEEK_END)
        while True:
            last_write_pos = f.tell()
            if data := f.readline():
                print(
                    highlighter(data.decode('utf8', errors='ignore').strip())
                )
            else:
                f.seek(last_write_pos)
                time.sleep(sleep)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('log_file')
    args = parser.parse_args()

    tail(args.log_file)
