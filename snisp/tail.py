import itertools
import logging
import os
import re
import time


logger = logging.getLogger(__name__)


try:
    from rich import print
    from snisp.utils import RichHighlighter as LogHighlighter
except ModuleNotFoundError:
    from snisp.utils import DummyHighlighter as LogHighlighter
    logger.warning('"rich" not installed. Defaulting to standard print.')


def tail(
    log_file,
    *,
    color_regexes=None,
    match_regexes=None,
    filter_regexes=None,
    show_httpx=False,
    sleep=1
):
    highlighter = LogHighlighter()
    if color_regexes is not None:
        for regex, colors in color_regexes:
            highlighter.regexes.append((regex, colors))
    if match_regexes is None:
        match_regexes = []
    else:
        match_regexes = [re.compile(r) for r in match_regexes]
    if filter_regexes is None:
        filter_regexes = []
    else:
        filter_regexes = [re.compile(r) for r in filter_regexes]
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
        try:
            while True:
                last_write_pos = f.tell()
                if data := f.readline():
                    line = data.decode('utf8', errors='ignore').strip()
                    if not show_httpx and ' httpx |' in line:
                        continue
                    if any(r.search(line) for r in filter_regexes):
                        continue
                    if match_regexes:
                        if not any(r.search(line) for r in match_regexes):
                            continue
                    print(highlighter(line))
                else:
                    f.seek(last_write_pos)
                    time.sleep(sleep)
        except KeyboardInterrupt:
            pass


def regex_colors(arg):
    try:
        args = arg.split(',')
        regex = re.compile(rf'{args[0]}')
        colors = itertools.cycle(args[1:])
        return regex, colors
    except Exception as e:
        raise argparse.ArgumentTypeError(
            f'{str(e)}: "regexes" expects an input of "regex,color", etc.'
        )


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'log_file', help='Full path for the log file to be tailed.'
    )
    parser.add_argument(
        '-p',
        '--patterns',
        nargs='+',
        type=regex_colors,
        help='Regex patterns to pass to Rich. Requires "rich" to be '
             r'installed.\ne.g.,--paterns  "\d+, blue on white,red on green" '
             r'"\w, red,green"\nThe pattern is "{regex}, {colors},..." where '
             '{colors} will be cycled over all matches.'
    )
    parser.add_argument(
        '-m',
        '--matches',
        nargs='+',
        help='List of regexes to filter the logs. Only logs that match any of '
             'the conditions in the regexes will be shown.'
    )
    parser.add_argument(
        '-f',
        '--filters',
        nargs='+',
        help='List of regexes to filter the logs. Logs that match any of '
             'the conditions in the regexes will be NOT shown.'
    )
    parser.add_argument(
        '--show-httpx',
        default=False,
        action='store_true',
        help='Flag to enable showing logs created '
             'by "httpx" in the tail output.'
    )
    args = parser.parse_args()

    tail(
        args.log_file,
        color_regexes=args.patterns,
        match_regexes=args.matches,
        filter_regexes=args.filters,
        show_httpx=args.show_httpx,
    )
