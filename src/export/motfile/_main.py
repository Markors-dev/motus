import json
import logging
from pathlib import Path
from collections import OrderedDict
from cryptography.fernet import Fernet

from PyQt5 import QtWidgets

from config import DAYS, PLAN_FILE_EXTENSION, WORKOUT_FILE_EXTENSION
from settings import Settings
from database.data_model import (
    PlanData, SupersetRow, TableRowType, WorkoutData,
)
from gui.dialogs import ErrorMessage, QuestionDialog, get_filepath_from_dialog


# Constants
KEY = b'nvaKNy8NMt61JDW4ob5Pd9CIAxBk6iUIlaRGDAUh8j4='


def _get_filepath(filename):
    """Creates export filepath and returns it(with file overwrite check)

    :param motus_object_name <str> Plan or workout name
    """
    export_folderpath = Settings().getValue('motfiles_folderpath')
    if not Path(export_folderpath).exists():
        _msg = f'Create folder "{export_folderpath}" or set other directory(in Settings)\n' \
               f'for motfile exports.'
        ErrorMessage('Exports folder not found', _msg).exec()
        return False
    filepath = str(Path(export_folderpath).joinpath(filename))
    if Path(filepath).exists():
        _msg = f'File "{filename}" already exists in directory: \n' \
               f'{export_folderpath}\n\n' \
               f'Do you want to overwrite it?'
        overwrite = QuestionDialog('Overwrite file', _msg)
        if not overwrite:
            return False
    return filepath


def _get_plan_filepath(plan_name):
    plan_filename = plan_name.replace(' ', '_').lower() + f'.{PLAN_FILE_EXTENSION}'
    return _get_filepath(plan_filename)


def _get_workout_filepath(workout_name):
    workout_filename = workout_name.replace(' ', '_').lower() + f'.{WORKOUT_FILE_EXTENSION}'
    return _get_filepath(workout_filename)


def _encrypt_dict(dict_):
    cipher = Fernet(KEY)
    dict_bytes = json.dumps(dict_).encode('utf8')
    encrypt_dict_bytes = cipher.encrypt(dict_bytes)
    return encrypt_dict_bytes


def _decrypt_dict(encrypt_dict_bytes):
    cipher = Fernet(KEY)
    dict_str = cipher.decrypt(encrypt_dict_bytes).decode('utf-8')
    dict_ = json.loads(dict_str)
    return dict_


def export_plan(plan_data):
    """Export week plan data to motfile motfile

    :param plan_data: <PlanData>
    """
    # ----- Get plan file path -----
    plan_fp = _get_plan_filepath(plan_data.name)
    if not plan_fp:
        return False
    # ----- Create plan dict object -----
    week_plan_dict = OrderedDict()
    week_plan_dict['plan_name'] = plan_data.name
    week_plan_dict['plan_type_id'] = plan_data.type_id
    for i, day in enumerate(DAYS):
        if not plan_data.workouts_data[i]:
            # NO workout on this day
            week_plan_dict[day] = None
            continue
        # Add workout
        workout_data = plan_data.workouts_data[i]
        week_plan_dict[day] = {}
        week_plan_dict[day]['workout_name'] = workout_data.name
        week_plan_dict[day]['workout_type_id'] = workout_data.type_id
        week_plan_dict[day]['rows'] = {}
        for row, row_data in enumerate(workout_data.rows_data):
            week_plan_dict[day]['rows'][str(row)] = row_data
        week_plan_dict[day]['workout_time'] = workout_data.workout_time
    # ----- Save plan dict object to motplan file -----
    encrypt_dict_bytes = _encrypt_dict(week_plan_dict)
    with open(plan_fp, 'wb') as outfile:
        outfile.write(encrypt_dict_bytes)
    return True


def export_workout(workout_data):
    # ----- Get workout file path -----
    workout_fp = _get_workout_filepath(workout_data.name)
    if not workout_fp:
        return False
    # ----- Create workout dict object -----
    workout_dict = {
        'workout_name': workout_data.name,
        'workout_type_id': workout_data.type_id,
        'rows': {},
    }
    for row, row_data in enumerate(workout_data.rows_data):
        workout_dict['rows'][str(row)] = row_data
    workout_dict['workout_time'] = workout_data.workout_time
    # ----- Save workout dict object to motplan file -----
    encrypt_dict_bytes = _encrypt_dict(workout_dict)
    with open(workout_fp, 'wb') as outfile:
        outfile.write(encrypt_dict_bytes)
        return True


def import_workout(workout_fp):
    # Open workout file and decrypt to workout data dict
    try:
        with open(workout_fp, 'rb') as infile:
            encrypt_dict_bytes = infile.read()
    except IOError:
        logging.error(f'Importing workout file "{workout_fp}" failed')
        return False
    workout_dict = _decrypt_dict(encrypt_dict_bytes)
    # Create workout data object and return it
    table_rows_data = []
    for row in workout_dict['rows'].keys():
        row_data = tuple(workout_dict['rows'][row])
        table_rows_data.append(row_data)
    workout_time = workout_dict['workout_time']
    workout_data = WorkoutData(workout_dict['workout_name'], workout_dict['workout_type_id'],
                               table_rows_data, workout_time)
    return workout_data


def import_plan(plan_fp):
    # Open plan file and decrypt to plan dict
    try:
        with open(plan_fp, 'rb') as infile:
            encrypt_dict_bytes = infile.read()
    except IOError:
        logging.error(f'Importing plan file "{plan_fp}" failed')
        return False
    week_plan_dict = _decrypt_dict(encrypt_dict_bytes)
    # Create plan data object and return it
    plan_name = week_plan_dict['plan_name']
    plan_type_id = week_plan_dict['plan_type_id']
    workouts_data = []
    for day in DAYS:
        if not week_plan_dict[day]:
            # No workout on this day
            workouts_data.append(None)
            continue
        workout_name = week_plan_dict[day]['workout_name']
        workout_type_id = week_plan_dict[day]['workout_type_id']
        table_rows_data = []
        for row in week_plan_dict[day]['rows'].keys():
            row_data = tuple(week_plan_dict[day]['rows'][row])
            table_rows_data.append(row_data)
        workout_time = week_plan_dict[day]['workout_time']
        workout_data = WorkoutData(workout_name, workout_type_id, table_rows_data, workout_time)
        workouts_data.append(workout_data)
    plan_data = PlanData(None, plan_name, plan_type_id, workouts_data)
    return plan_data
