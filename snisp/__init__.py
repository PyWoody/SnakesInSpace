import os
import logging
import threading

from snisp import agent, cache, database, utils  # noqa: F401


logging.basicConfig(
    format='%(asctime)s %(levelname)s %(name)s | %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    encoding='utf-8',
    filename=os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'snisp.log'
    ),
    filemode='w',
    level=logging.INFO,
)


threading.excepthook = utils.thread_exception_hook_logger
