import datetime
import json
import logging
import uuid
from contextlib import contextmanager
from enum import Enum
from pathlib import Path

from config import SESSION_JSON_FILE
from util.obj import SingletonDecorator
from settings import Settings


class TimeType(Enum):
    START_APP = 0
    END_APP = 1


class Session:

    @staticmethod
    def start_session():
        if not Path(SESSION_JSON_FILE).exists():
            # ----- Executed on initial run -----
            # Creates initial session dict and saves it
            date_time_now = datetime.datetime.now()
            init_session_dict = {
                'user_id': uuid.uuid4().hex,
                'last_loaded_plan': None,
                'emails_sent_per_day': {date_time_now.date().isoformat(): 0},
                'initial_run_time': date_time_now.isoformat(),
                'run_starts': [date_time_now.isoformat(), ],
                'run_finishes': [],
            }
            Session.write_to_session(init_session_dict)
        else:
            # ----- Executed on every(other) run -----
            Session.update_time(TimeType.START_APP)
        logging.info('######### Session START ...\n')

    @staticmethod
    def end_session():
        if not Path(SESSION_JSON_FILE).exists():
            return
        Session.update_time(TimeType.END_APP)
        SingletonDecorator.clean_instances()
        logging.info('... Session END #########\n\n')

    @staticmethod
    def get_user_id():
        session_json = Session.get_session_json()
        return session_json['user_id']

    @staticmethod
    def set_value(key, value):
        session_json = Session.get_session_json()
        session_json[key] = value
        Session.write_to_session(session_json)

    @staticmethod
    def get_value(key):
        session_json = Session.get_session_json()
        return session_json[key]

    @staticmethod
    def update_time(time_type):
        """ Updates run starts or finishes

        :param time_type: <TimeType>
        :return:
        """
        time_type_name = 'run_starts' if time_type == TimeType.START_APP else 'run_finishes'
        session_json = Session.get_session_json()
        if session_json:
            session_json[time_type_name].append(datetime.datetime.now().isoformat())
            Session.write_to_session(session_json)

    @staticmethod
    def update_emails():
        session_json = Session.get_session_json()
        if session_json:
            session_json['emails_sent'] += 1
            Session.write_to_session(session_json)

    @staticmethod
    def write_to_session(session_json):
        try:
            with open(SESSION_JSON_FILE, 'w') as wfile:
                json.dump(session_json, wfile, indent=4)
        except json.JSONDecodeError as exc:
            logging.error('Session file write failed', exc_info=exc)
        except IOError as exc:
            logging.error('Session file write failed', exc_info=exc)

    @staticmethod
    def get_session_json():
        session_json = None
        try:
            with open(SESSION_JSON_FILE, 'r') as fread:
                session_json = json.load(fread)
        except json.JSONDecodeError as ex:
            logging.error('Session file read failed', exc_info=ex)
        except IOError as ex:
            logging.error('Session file read failed', exc_info=ex)
        finally:
            if session_json:
                return session_json
            return False
