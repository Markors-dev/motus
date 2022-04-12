# import logging
#
# @deco_wrapper
# def func():
#     print('print ')
from gui.dialogs import ErrorMessage


# NOTE: This function is NOT used in the project(at the moment)
def log_action_execution(action_type, action_desc, arg_name=None):
    """Decorator for logging the execution of functions/methods.

    This deco logs INFO message if the func/meth returns True-like
    object (True, int, str, ...) or ERROR message if returns
    False-like object(False, None)

    :param action_type: <str> - e.g. 'Database', 'File handling', ...
    :param action_desc: <str> - Description of action. e.g. 'Delete row', 'Write to motfile', ...
    :param arg_name: <str> or None - Name of arg which is logged in message
    :return <function> or <method>
    """
    failed_action_return_values = (Exception, False, None)

    def deco_wrapper(func):
        func_args = func.__code__.co_varnames

        def func_wrapper(*args, **kwargs):
            log_line_end = f" {args[func_args.index(arg_name)]}'" if arg_name else "'"
            value = func(*args, **kwargs)
            for fail_value in failed_action_return_values:
                if isinstance(value, fail_value):
                    logging.error(f"({action_type}) Action '{action_desc}{log_line_end} FAILED.")
                    break
            else:
                logging.info(f"({action_type}) Action '{action_desc}{log_line_end} DONE.")
            return value
        return func_wrapper
    return deco_wrapper



