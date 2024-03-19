import argparse
import code
import importlib.metadata
import itertools
import logging
import os
import re
import threading

import snisp

try:
    VERSION = importlib.metadata.version("SnakesInSpace")
except Exception:
    VERSION = ''


def regex_colors(arg):
    try:
        args = arg.split(', ')
        regex = re.compile(rf'{args[0]}')
        colors = itertools.cycle(args[1:])
        return regex, colors
    except Exception as e:
        raise argparse.ArgumentTypeError(
            f'{str(e)}: "regexes" expects an input of "regex,color", etc.'
        )


LOG_LEVELS = {
    'NOTSET': logging.NOTSET,
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

parser = argparse.ArgumentParser(
    prog='Snakes in Space',
    allow_abbrev=False,
    formatter_class=argparse.RawTextHelpFormatter,
    description='Snakes in Space implementation of SpaceTraders.',
    epilog='Additional information and basic HOW-TOs can be found here: '
           'https://github.com/PyWoody/SnakesInSpace'
           '\n\n'
           'For information regarding SpaceTraders, please visit their '
           'website at https://spacetraders.io/'
)
parser.add_argument(
    '-v', '-version', action='version', version=f'%(prog)s {VERSION}'
)
subparsers = parser.add_subparsers(
    title='subcommands',
    dest='subparsers',
    metavar='',
    help='See sub-command -h/--help for additional information'
)

interactive_parser = subparsers.add_parser(
    'interactive',
    allow_abbrev=False,
    formatter_class=argparse.RawTextHelpFormatter,
    help='Drops you into an interactive console with "agent" and '
         'command "ship" pre-loaded',
    description='This will drop you into an interactive shell of your current '
                'game. '
                'If you have already logged in at this location, '
                'you will be able to access your Agent as "agent". '
                'Otherwise, you will be dropped into an interactive '
                'session with only "snisp" imported.\n\n'
                'This is only intended for testing, status checking, etc. and '
                'not for actual playing.\n',
)
interactive_parser.add_argument(
    '-s',
    '--symbol',
    help='The symbol will act a the username. If left blank, \n'
         'the program will attempt to use the last logged in account. \n'
         'If left blank and no account has been logged in at this location \n'
         'before, a SpaceUserError will be raised.'
         '\n'
         '\n'
)
interactive_parser.add_argument(
    '-f',
    '--faction',
    default='COSMIC',
    choices=snisp.utils.FACTION_SYMBOL,
    metavar='',
    help='Default is "COSMIC". \n'
         'Using the non-standard Faction may cause issues. \n'
         'Using a different Faction than the one used to the '
         'account may cause other issues.'
         '\n'
         '\n'
         f'Options are: {", ".join(snisp.utils.FACTION_SYMBOL)}'
         '\n'
         '\n'
)
interactive_parser.add_argument(
    '-e',
    '--email',
    help='Optional'
)
interactive_parser.add_argument(
    '-t',
    '--token',
    help='Existing SpaceTraders token. Optional.'
)

tail_parser = subparsers.add_parser(
    'tail',
    allow_abbrev=False,
    formatter_class=argparse.RawTextHelpFormatter,
    help='Options for tailing the command log. '
         'By default, logs by "httpx" will be ignored.',
    description='Options for tailling the command log. '
                'By default, logs made by "httpx" will be ignored. '
                '\n\nIf you have "rich" (https://github.com/Textualize/rich) '
                'installed, you can add additonal regex patterns for '
                'highlighting.\nOtherwise, '
                'default highlights will be attempted.',
)
tail_parser.add_argument(
    '-p',
    '--patterns',
    nargs='+',
    type=regex_colors,
    help='Regex patterns to pass to Rich. Requires "rich" to be installed.\n'
         r'e.g.,--paterns  "\d+,blue on white,red on green" "\w,red,green"'
         '\nThe pattern is "{regex}, {colors},..." where {colors} will be'
         'cycled over all matches.'
)
tail_parser.add_argument(
    '-m',
    '--matches',
    nargs='+',
    help='List of regexes to filter the logs. Only logs that match any of '
         'the conditions in the regexes will be shown.'
)
tail_parser.add_argument(
    '-f',
    '--filters',
    nargs='+',
    help='List of regexes to filter the logs. Logs that match any of '
         'the conditions in the regexes will be NOT shown.'
)
tail_parser.add_argument(
    '--show-httpx',
    default=False,
    action='store_true',
    help='Flag to enable showing logs created by "httpx" in the tail output.'
)

logger_group = parser.add_argument_group('Logger Options')
no_logging_arg = logger_group.add_argument(
    '--no-logging',
    default=False,
    action='store_true',
    help='Disables the logger for this operation'
)
logger_group.add_argument(
    '--file-mode',
    choices=['w', 'a'],
    default='w',
    help='Sets the file mode for the logger to either "w" '
         'for write or "a" for append. Default is "w"'
)
logger_group.add_argument('--filename', help='Default is "snisp.log"')
logger_group.add_argument(
    '--level',
    choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    metavar='NOTSET DEBUG INFO WARNING ERROR CRITICAL',
    default='INFO',
    help='Sets the logger level. Default is INFO'
)
logger_group.add_argument(
    '--exception-hook',
    choices=['thread_exception_hook_raiser', 'thread_exception_hook_logger'],
    metavar='thread_exception_hook_raiser thread_exception_hook_logger',
    default='thread_exception_hook_logger',
    help='The default, "thread_exception_hook_logger," will not raise '
         'exceptions that occur in threads\n'
         'but will merely log them as warnings.'
         '\n\n'
         '"thread_exception_hook_raiser" will print the error to terminal '
         'and attempt to raise it.'
)

args = parser.parse_args()

if args.filename:
    log_fname = args.filename
else:
    log_fname = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'snisp.log'
    )

if _subparser := args.subparsers:
    if args.exception_hook != 'thread_exception_hook_printer':
        threading.excepthook = snisp.utils.thread_exception_hook_raiser
    if args.no_logging:
        logging.getLogger().disabled = True
    else:
        logging.basicConfig(
            format='%(asctime)s %(levelname)s %(name)s | %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p',
            encoding='utf-8',
            filename=log_fname,
            filemode=args.file_mode,
            level=LOG_LEVELS[args.level],
            force=True,
        )
    if _subparser == 'tail':
        if args.no_logging:
            raise argparse.ArgumentError(
                no_logging_arg,
                'Cannot run tail if there is nothing to tail. '
                'Please run the command again and remove "--no-logging"'
            )
        from snisp import tail
        tail.tail(
            log_fname,
            color_regexes=args.patterns,
            match_regexes=args.matches,
            filter_regexes=args.filters,
            show_httpx=args.show_httpx,
        )
    elif _subparser == 'interactive':
        try:
            agent = snisp.agent.Agent(
                symbol=args.symbol,
                faction=args.faction,
                email=args.email,
                token=args.token,
            )
            ship = next(iter(agent.fleet))
        except snisp.exceptions.SpaceUserError as e:
            print(f'WARNING: Could not Access Agent. {str(e)}')
        import readline  # noqa: F401
        code.InteractiveConsole(locals=locals()).interact()
