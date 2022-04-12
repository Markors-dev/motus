import logging
import requests

from util.exception import log_and_show_method_exception, ExceptionWithMsg
from gui.dialogs import ErrorMessage


@log_and_show_method_exception('Download content failed')
def get_content_from_url(url):
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as ex:
        return ExceptionWithMsg(ex, f'Request from "{url}" failed.')
    if response.status_code != 200:
        ErrorMessage(f'Download content failed',
                     f'Content from "{url}" couldn\'t be dowloaded.').exec()
        return False
    logging.info(f'Content from url "{url}" downloaded.')
    return response.content
