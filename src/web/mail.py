import json
import smtplib
import ssl
import logging
import datetime
import traceback
import requests
import base64
from os import path
from enum import Enum
from pathlib import Path
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from session import Session
from gui.dialogs import ErrorMessage
from config import APP_MODE, AppMode


# ----- Constants -----
MAX_EMAILS_PER_DAY = 20
MAX_ATTACHMENT_SIZE = 20  # MB

# NOTE: I creted a web api for sending mail
MOTUS_API_URL = r'http://Markors.pythonanywhere.com/api/send_mail/'


class EMailType(Enum):
    DEFECT = 0
    ENHANCEMENT = 1
    CRASH_REPORT = 2


def _get_file_size_mb(fp):
    file_size_bytes = path.getsize(fp)
    return int(file_size_bytes / 1024 / 1024)


def _email_type_to_subject(email_type):
    _user_id = Session.get_user_id()
    email_type_to_str_dict = {
        EMailType.DEFECT: f'[Defect] User: {_user_id}',
        EMailType.ENHANCEMENT: f'[Enhancement] User: {_user_id}',
        EMailType.CRASH_REPORT: f'[Crash Report] User: {_user_id}',
    }
    return email_type_to_str_dict[email_type]


def _update_email_sent_count():
    session_json = Session.get_session_json()
    emails_sent_per_day = session_json['emails_sent_per_day']
    today_iso = datetime.date.today().isoformat()
    if today_iso in emails_sent_per_day.keys():
        emails_sent_per_day[today_iso] += 1
    else:
        emails_sent_per_day[today_iso] = 0
    Session.write_to_session(session_json)


def _email_day_count_maxed():
    session_json = Session.get_session_json()
    emails_sent_per_day = session_json['emails_sent_per_day']
    today_iso = datetime.date.today().isoformat()
    if today_iso in emails_sent_per_day.keys() and \
            emails_sent_per_day[today_iso] > MAX_EMAILS_PER_DAY:
        return True
    return False


def _log_and_show_error(action_fail_msg, error_msg='', exc=None):
    logging.error(action_fail_msg, exc_info=exc)
    if APP_MODE == AppMode.DEVELOPMENT_MODE and exc:
        text = f'{error_msg}\n\n'\
               f'Traceback:\n' + \
               ''.join(traceback.format_tb(exc.__traceback__))
    else:
        text = error_msg
    ErrorMessage('Sending e-mail failed', text).exec()


def send_email(email_type, body, attachment_fp=None):
    """Sends an e-mail to Motus App official address

    :param email_type: <EMailType>
    :param body: <str>
    :param attachment_fp: <str> or None
    """
    # ---- Check file size and mails per day count -----
    if _email_day_count_maxed():
        _msg = f'Maximum sent e-mails per day(max={MAX_EMAILS_PER_DAY}) reached\n' \
               f'Wait for tommorow to send a new e-mail'
        _log_and_show_error('Sending e-mail failed', error_msg=_msg)
        return False
    if attachment_fp and _get_file_size_mb(attachment_fp) > MAX_ATTACHMENT_SIZE:
        _msg = f'Attached file size is to big(max={MAX_ATTACHMENT_SIZE} MB)\n' \
                'Attach some other file'
        _log_and_show_error('Sending e-mail failed', error_msg=_msg)
        return False
    # ----- Add attachment, if it exists .....
    attached_image_dict = None
    if attachment_fp:
        try:
            with open(attachment_fp, "rb") as attachment:
                image_bytes = attachment.read()
        except IOError as ex:
            _log_and_show_error('Sending e-mail failed', exc=ex)
            return False
        attached_image_dict = {}
        image_base64_bytes = base64.b64encode(image_bytes)
        attached_image_dict['image_base64_str'] = image_base64_bytes.decode('ascii')
        attached_image_dict['image_filename'] = str(Path(attachment_fp).parts[-1])
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        "subject": _email_type_to_subject(email_type),
        "body": body,
        "image_dict": attached_image_dict,
    }
    try:
        resp = requests.post(MOTUS_API_URL, headers=headers, data=json.dumps(data), timeout=5)
        if resp.status_code == 200:
            logging.info('E-Mail sent to Motus developers')
            return True
        else:
            _msg = r'Sending e-mail failed\n\
                   HTTP status code: {resp.status_code}\n' \
                   fr'Error message: {resp.text}'
            logging.error(_msg)
            ErrorMessage('Sending e-mail failed', 'Something went wrong').exec()
            return False
    except requests.exceptions.RequestException as ex:
        logging.error('Sending e-mail failed', exc_info=ex)
        ErrorMessage('Sending e-mail failed', 'Something went wrong').exec()
        return False
