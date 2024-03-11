import argparse
import code
import logging
import threading

import snisp


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
    description='Snakes in Space implementation of SpaceTraders.\n\n'
                'This will drop you into an interactive shell of your current '
                'game. '
                'You will be able to access your Agent as "agent".\n'
                'This is only intended for testing, status checking, etc. and '
                'not for actual playing.\n',
    epilog='Additional information and basic HOW-TOs can be found here: ....'
           '\n\n'
           'For information regarding SpaceTraders, please visit their '
           'website at https://spacetraders.io/'
)
parser.add_argument(
    '-v', '-version', action='version', version='%(prog)s 0.0.1'
)

agent_group = parser.add_argument_group('Agent Options')
agent_group.add_argument(
    '-s',
    '--symbol',
    help='The symbol will act a the username. If left blank, \n'
         'the program will attempt to use the last logged in account. \n'
         'If left blank and no account has been logged in at this location \n'
         'before, a SpaceUserError will be raised.'
         '\n'
         '\n'
)
agent_group.add_argument(
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
agent_group.add_argument(
    '-e',
    '--email',
    help='Optional'
)

log_group = parser.add_argument_group('Logging Options')
log_group.add_argument(
    '--no-logging',
    default=False,
    action='store_true',
    help='Disables the logger for this operation'
)
log_group.add_argument(
    '--file-mode',
    choices=['w', 'a'],
    default='w',
    help='Sets the file mode for the logger to either "w" '
         'for write or "a" for append. Default is "w"'
)
log_group.add_argument(
    '--filename', default='snisp.log', help='Default is "snisp.log"'
)
log_group.add_argument(
    '--level',
    choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    metavar='NOTSET DEBUG INFO WARNING ERROR CRITICAL',
    default='INFO',
    help='Sets the logger level. Default is INFO'
)
log_group.add_argument(
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

if args.no_logging:
    logging.getLogger().disabled = True
else:
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(name)s | %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        encoding='utf-8',
        filename=args.filename,
        filemode=args.file_mode,
        level=LOG_LEVELS[args.level],
        force=True,
    )

if args.exception_hook != 'thread_exception_hook_printer':
    threading.excepthook = snisp.utils.thread_exception_hook_raiser

agent = snisp.agent.Agent(
    symbol=args.symbol, faction=args.faction, email=args.email
)

code.InteractiveConsole(locals=locals()).interact()
