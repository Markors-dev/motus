import re

from database.data_model import SupersetRow, ExerciseExecutionWorkData, SupersetTopRow, SupersetBottomRow, \
    TableRowType, ExerciseExecutionRow, TableRowType
from database.db_obj import DB
# from gui.dialogs import ErrorMessage


REP_EXEC_TIME = 3  # seconds


# TODO: (IMPORTANT !) Change exercise name "34 situps"

DEFAULT_EXER_EXEC_DATA = {
    # key=column; value=sets or reps pr pause
    'reps': {
        1: 3,
        2: 10,
        3: 2,
    },
    'non_reps': {
        1: 3,
        2: 1,
        3: 2,
    }

}

COL_VAL_CONSTRAINTS = {
    1: tuple(range(1, 11)),  # sets
    2: tuple(range(1, 121)),  # reps or time(min)
    3: tuple(range(0, 11)),  # time(min)
}

_COL_VALUE_CHECK_ERROR_MSG = \
    'Column value for %s:\n' \
    f'\t- must be minimum %s\n' \
    f'\t- must be maximum %s\n'.expandtabs(4)

# .expandtabs(4)
SETS_COL_VALUE_CHECK_ERROR_MSG = _COL_VALUE_CHECK_ERROR_MSG % \
                                 ('Sets', COL_VAL_CONSTRAINTS[1][0], COL_VAL_CONSTRAINTS[1][-1])

REPS_COL_VALUE_CHECK_ERROR_MSG = _COL_VALUE_CHECK_ERROR_MSG % \
                                 ('Reps', COL_VAL_CONSTRAINTS[2][0], COL_VAL_CONSTRAINTS[2][-1])

PAUSE_COL_VALUE_CHECK_ERROR_MSG = _COL_VALUE_CHECK_ERROR_MSG % \
                                 ('Pause', COL_VAL_CONSTRAINTS[3][0], COL_VAL_CONSTRAINTS[3][-1])


def execution_data_valid(column, value):
    if value in COL_VAL_CONSTRAINTS[column]:
        return True
    return False


def get_error_msg_for_col(col):
    if col == 1:
        return SETS_COL_VALUE_CHECK_ERROR_MSG
    elif col == 2:
        return REPS_COL_VALUE_CHECK_ERROR_MSG
    elif col == 3:
        return PAUSE_COL_VALUE_CHECK_ERROR_MSG


def get_default_exer_exec_data(exer_type):
    if exer_type in ('Cardio', 'Stretching'):
        sets_reps_pause = tuple(DEFAULT_EXER_EXEC_DATA['non_reps'].values())
        on_reps = False
    else:
        sets_reps_pause = tuple(DEFAULT_EXER_EXEC_DATA['reps'].values())
        on_reps = True
    row_data = ExerciseExecutionWorkData(*sets_reps_pause, on_reps)
    return row_data


def get_default_ss_bottom_data():
    return DEFAULT_EXER_EXEC_DATA['reps'][1], DEFAULT_EXER_EXEC_DATA['reps'][3]


def get_default_col_value(col, on_reps):
    reps_key = 'reps' if on_reps else 'non_reps'
    return DEFAULT_EXER_EXEC_DATA[reps_key][col]


def calc_workout_time(table_rows):
    """Calculates and returns workout time in minutes"""
    total_workout_time_sec = 0  # seconds
    in_superset_exec_time_sec = 0  # seconds
    for table_row in table_rows:
        if type(table_row) == ExerciseExecutionRow:
            if not table_row.superset_numb:
                if table_row.on_reps:
                    set_time = table_row.reps * REP_EXEC_TIME + table_row.pause * 60
                else:
                    set_time = table_row.reps * 60 + table_row.pause * 60
                total_workout_time_sec += table_row.sets * set_time
            else:
                exex_time_sec = table_row.reps * REP_EXEC_TIME if table_row.on_reps else \
                    table_row.reps * 60
                in_superset_exec_time_sec += exex_time_sec
        else:  # == SupersetRow
            if type(table_row) == SupersetBottomRow:
                superset_exec_time = table_row.sets * (in_superset_exec_time_sec + table_row.pause * 60)
                total_workout_time_sec += superset_exec_time
                in_superset_exec_time_sec = 0
    return total_workout_time_sec // 60


def filter_existing_exercise_row_data(rows_data):
    missing_exercises = []
    ok_rows_data = []
    for row_data in rows_data:
        if row_data[0] == str(TableRowType.EXER_EXEC):
            # --- Check if exercise exists in DB ---
            exer_data = DB().select_exercise_data(row_data[1], get_none=True)
            if not exer_data:
                missing_exercises.append(row_data[2])
                continue
        ok_rows_data.append(row_data)
    return ok_rows_data, missing_exercises
