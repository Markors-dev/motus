import sys
import traceback
import logging

from session import Session
from gui.widgets import CrashReportErrorMessage


def my_exception_hook(type_, value, tb):
    """
    Intended to be assigned to sys.exception as a hook.
    Gives opportunity to do something useful
    with info from uncaught exceptions.

    :param type_ <type> Type of exception
    :param value <Exception> (Un)caught exception
    :param tb <traceback> Traceback object
    """
    tb_msg = 'Traceback:\n' + \
             ''.join(traceback.extract_tb(tb).format()) + \
             f'{type_.__name__}("{value}")'
    logging.error(f'App internal error\n {tb_msg}')
    CrashReportErrorMessage('App crashed',
                            f'Internal error has occured in App\n'
                            f'Send crash report e-mail(if you want)',
                            tb_msg).exec()
    Session.end_session()
    sys.exit(0)
