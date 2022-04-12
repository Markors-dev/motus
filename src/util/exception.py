import logging
import traceback
from collections import namedtuple

from config import APP_MODE, AppMode
from gui.dialogs import ErrorMessage
from gui.widgets import CrashReportErrorMessage


ExceptionWithMsg = namedtuple('ExceptionWithMsg', ('exc', 'msg'))


def get_tb_msg_from_exc(exc):
    tb_msg = f'Traceback:\n' + \
             ''.join(traceback.format_tb(exc.__traceback__))
    return tb_msg


def log_and_show_method_exception(action_fail_msg):
    """If decorated method returns object <ExceptionWithMsg>,
    this function logs error, shows error info dialog and returns
    'False'.
    Any other returned value is passed through.

    In PRODUCTION_MODE, it shows crash report dialog so that
    the user can send a crash report email to developers.
    """
    def deco_wrapper(func):
        def func_wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            if type(value) == ExceptionWithMsg:
                logging.error(action_fail_msg, exc_info=value.exc)
                _tb_msg = get_tb_msg_from_exc(value.exc)
                if APP_MODE == AppMode.DEVELOPMENT_MODE:
                    ErrorMessage(action_fail_msg, _tb_msg).exec()
                else:  # APP_MODE == AppMode.PRODUCTION_MODE
                    text = 'Internal error occured.\n\n' \
                           'Send crash report e-mail(if you want)'
                    CrashReportErrorMessage(action_fail_msg, text, _tb_msg).exec()
                return False
            return value
        return func_wrapper
    return deco_wrapper
