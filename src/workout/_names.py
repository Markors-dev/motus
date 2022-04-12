# -*- coding: utf-8 -*-
import re

from database.data_model import SupersetRow
from database.db_obj import DB
# from gui.dialogs import ErrorMessage

MIN_FILTERED_EXERCISE_NAME_LEN = 0
MIN_EXERCISE_NAME_LEN = 3
MAX_EXERCISE_NAME_LEN = 50
MIN_WORKOUT_NAME_LEN = 5
MAX_WORKOUT_NAME_LEN = 40
MIN_PLAN_NAME_LEN = 5
MAX_PLAN_NAME_LEN = 50
MIN_INSTRUCTION_STEP_TEXT_LEN = 0
MAX_INSTRUCTION_STEP_TEXT_LEN = 500

# ---- Regex patterns -----
_BASE_PATTERN = r"[a-zA-Z0-9čćđšžČĆĐŠŽ,_'\-\(\) ]{%s,%s}"
EXERCISE_NAME_PATTERN = _BASE_PATTERN % (MIN_EXERCISE_NAME_LEN, MAX_EXERCISE_NAME_LEN)
EXERCISE_FILTERED_NAME_PATTERN = _BASE_PATTERN % (MIN_FILTERED_EXERCISE_NAME_LEN, MAX_EXERCISE_NAME_LEN)
WORKOUT_NAME_PATTERN = _BASE_PATTERN % (MIN_WORKOUT_NAME_LEN, MAX_WORKOUT_NAME_LEN)
PLAN_NAME_PATTERN = _BASE_PATTERN % (MIN_PLAN_NAME_LEN, MAX_PLAN_NAME_LEN)
INSTRUCTION_STEP_TEXT_PATTERN = r"[a-zA-Z0-9čćđšžČĆĐŠŽ,.;_'\?\!\-\\\/\-\(\) ]{%s,%s}" % \
                            (MIN_INSTRUCTION_STEP_TEXT_LEN, MAX_INSTRUCTION_STEP_TEXT_LEN)

# ---- Regex check error messages -----
_BASE_NAME_CHECK_ERROR_MSG = \
    '%s name:\n' \
    f'\t- must be minimum %s characters long\n' \
    f'\t- must be maximum %s characters long\n' \
    f'\t- can contain english alphabet: a-z(upper/lower case)\n' \
    f'\t- can contain croatian letters: "č ć đ š ž"(upper/lower case)\n' \
    f'\t- can contain other characters: " , _ - \' ( )"\n'.expandtabs(4)

EXERCISE_NAME_CHECK_ERROR_MSG = _BASE_NAME_CHECK_ERROR_MSG % \
                                ('Exercise', MIN_EXERCISE_NAME_LEN, MAX_EXERCISE_NAME_LEN)

EXERCISE_FILTERED_NAME_CHECK_ERROR_MSG = _BASE_NAME_CHECK_ERROR_MSG % \
                                ('Filtered Exercise', MIN_FILTERED_EXERCISE_NAME_LEN, MAX_EXERCISE_NAME_LEN)

WORKOUT_NAME_CHECK_ERROR_MSG = _BASE_NAME_CHECK_ERROR_MSG % \
                               ('Workout', MIN_WORKOUT_NAME_LEN, MAX_WORKOUT_NAME_LEN)

PLAN_NAME_CHECK_ERROR_MSG = _BASE_NAME_CHECK_ERROR_MSG % \
                            ('Plan', MIN_PLAN_NAME_LEN, MAX_PLAN_NAME_LEN)


INSTRUCTION_STEP_TEXT_CHECK_ERROR_MSG = \
    'Instruction step text:\n' \
    f'\t- must be minimum %s characters long\n' \
    f'\t- must be maximum %s characters long\n' \
    f'\t- can contain english alphabet: a-z(upper/lower case)\n' \
    f'\t- can contain croatian letters: "č ć đ š ž"(upper/lower case)\n' \
    f'\t- can contain other characters: " , . ! ? ; _ - \' \\ / ( ) \n'.expandtabs(4) % \
    (MIN_INSTRUCTION_STEP_TEXT_LEN, MAX_INSTRUCTION_STEP_TEXT_LEN)


# ----- Methods -----

def generate_workout_name(exer_exec_rows=None):
    # TODO: write this
    """
    Workout name generator bluprint:
    - (workout goal/type) (Body part) (type of intensity) workout
        -> Workout goal: Strength|Cardio|Recovery|Stretching
        -> Body part: Push|Pull|Legs
        -> Type of intensity: Weights|Body only|

    """
    raise NotImplemented(f'Method "{generate_workout_name}" is on TODO')


def get_available_generic_exer_name():
    name_base = 'Exercise'
    exer_name = name_base
    for numb in range(1, 1000):
        if not DB().select_from_table(
                'exercises', 'name', {'name': exer_name}, get_none=True):
            break
        exer_name = name_base + f' {numb}'
    return exer_name


def get_available_generic_workout_name(table_name=''):
    name_base = f'Workout for {table_name}'if table_name else 'Workout'
    workout_name = name_base
    for numb in range(1, 1000):
        if not DB().select_from_table(
                'workout', 'id', {'name': workout_name}, get_none=True):
            break
        workout_name = name_base + f' {numb}'
    return workout_name


def get_available_generic_plan_name(prefix=''):
    name_base = f'{prefix}Plan'
    plan_name = name_base
    for numb in range(1, 1000):
        plan_name = name_base + f' {numb}'
        if not DB().select_from_table(
                'week_plan', 'id', {'name': plan_name}, get_none=True):
            break
    return plan_name


def _text_validator(regex_pattern, text):
    match = re.match(regex_pattern, text)
    if match and len(match.group()) == len(text):
        return True
    return False


def exercise_name_valid(exer_name):
    return _text_validator(EXERCISE_NAME_PATTERN, exer_name)


def exercise_filtered_name_valid(exer_name):
    return _text_validator(EXERCISE_FILTERED_NAME_PATTERN, exer_name)


def workout_name_valid(workout_name):
    return _text_validator(WORKOUT_NAME_PATTERN, workout_name)


def plan_name_valid(plan_name):
    return _text_validator(PLAN_NAME_PATTERN, plan_name)


def instruction_text_valid(step_text):
    if not _text_validator(INSTRUCTION_STEP_TEXT_PATTERN, step_text):
        return False
    return True
