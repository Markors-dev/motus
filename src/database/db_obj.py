import pickle
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from functools import wraps

from database.data_model import (
    ExerciseData, ExerciseListRow, PlanListRow, ExerciseExecutionRow, TableRowType,
    SupersetTopRow, SupersetBottomRow, WorkoutListRow
)
from config import DAYS, DB_PATH
from settings import Settings
from util import images
from util.obj import SingletonDecorator
from util.value import wrap_text


@SingletonDecorator
class DB:

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        # Attribute for development
        self.exercises_table = 'exercises'

    def execute_statement(self, statement, params=None):
        """Executes SQL statement"""
        # ----- Statement checks -----
        if statement.split(' ')[0] not in \
                ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'VACUUM'):
            raise NotImplementedError('Implement return value for this SQL statement type')
        if '?' in statement and params is None:
            raise ValueError('Parameters are not provided')
        # ----- Execute SQL statement -----
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if params:
                cursor.execute(statement, params)
            else:
                cursor.execute(statement)
            if statement.startswith('SELECT'):
                _return_value = cursor.fetchall()
            else:
                cursor.execute('SELECT changes();')
                res = cursor.fetchall()
                numb_of_changes = True if res[0][0] > 0 else False
                _return_value = True if numb_of_changes > 0 else False
            conn.commit()
            return _return_value
        except sqlite3.Error as ex:
            logging.error(f'(Database) Failed execution:\n'
                          f'  -> Statement:\n{wrap_text(statement, 100)}\n'
                          f'  -> Params: {params}', exc_info=ex)
            return False
        except OSError as ex:
            logging.error(f'(Database) Failed execution statement:\n{wrap_text(statement, 100)}', exc_info=ex)
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def _create_filter_statement(filters):
        """Creates filter segment of statement

        :param filters <dict> Format= Key<str>:Value<object>
        """
        statement_filter = ' WHERE'
        counter = 1
        params = []
        for column_name, column_value in filters.items():
            statement_filter += ' AND' if counter > 1 else ''
            if type(column_value) == str and '%' in column_value:
                statement_filter += f' {column_name} LIKE ?'
                params.append(column_value)
            else:
                statement_filter += f' {column_name} = ?'
                params.append(column_value)
            counter += 1
        return statement_filter, tuple(params)

    def _select_exercises(self, columns, filters=None, order_by=None):
        """ Selects rows from table 'exercises'.

        :param columns: <list(<str>)> or <tuple(<str>)>
        :param filters: <dict> Example - 'exercise_type.name: Strength'
        :param order_by: <str> or None
        :return: <tuple(lists)>
        """
        column_names_str = ', '.join(columns)
        statement = f'SELECT {column_names_str} ' \
                    f'FROM {self.exercises_table} ' \
                    f'INNER JOIN exercise_type ON exercise_type.id = {self.exercises_table}.type_id ' \
                    f'INNER JOIN body_part ON body_part.id = {self.exercises_table}.body_part_id ' \
                    f'INNER JOIN muscle_group ON {self.exercises_table}.main_muscle_group_id = muscle_group.id ' \
                    f'LEFT JOIN muscle_group mg2 ON {self.exercises_table}.minor_muscle_group_id = mg2.id ' \
                    f'INNER JOIN equipment ON {self.exercises_table}.equipment_id = equipment.id'
        params = None
        if filters:
            statement_filter, params = self._create_filter_statement(filters)
            statement += statement_filter
        if order_by:
            statement += f' ORDER BY {order_by} ASC'
        result_set = self.execute_statement(statement, params=params)
        return result_set

    @staticmethod
    def get_icon_bytes_from_icons_dict(icons_dict_bytes):
        """Returns icon of set icon size from 'icons_dict' row in DB

        :param icons_dict_bytes <bytes> Serialized dict containing 3 <QtGui.QIcon> objects
        :return <bytes> Icon image bytes
        """
        icons_dict = pickle.loads(icons_dict_bytes)
        return icons_dict[Settings().getValue('icon_size')[0]]

    def select_exercise_list_rows(self, filters=None):
        """Select exercise list rows using set filters

        :param filters <dict> or None
        """
        columns = [
            f'{self.exercises_table}.id',
            f'{self.exercises_table}.name',
            f'{self.exercises_table}.icons_dict'
        ]
        result_set = self._select_exercises(columns, filters=filters,
                                            order_by=f'{self.exercises_table}.name')
        if result_set:
            exer_list_rows = []
            for row in result_set:
                _icon_bytes = self.get_icon_bytes_from_icons_dict(row[2])
                exer_list_rows.append(ExerciseListRow(row[0], row[1], _icon_bytes))
            return exer_list_rows
        return False

    def select_exercise_data(self, exer_id, get_none=False):
        """Gets exercise data.

        :param exer_id <int> Exercise id
        :param get_none <bool> If True return None when no results
        :return <ExerciseData>
        """
        columns = [
            f'{self.exercises_table}.id', f'{self.exercises_table}.name', 'exercise_type.name',
            'body_part.name', 'muscle_group.name', 'mg2.name', 'equipment.name',
            'muscle_group.image', 'mg2.image', 'position_1', 'position_2',
            'instructions', 'icons_dict', 'favorite', 'link', 'user_permission'
        ]
        filters = {f'{self.exercises_table}.id': exer_id}
        result_set = self._select_exercises(columns, filters)
        if not result_set:
            if get_none:
                return None
            else:
                raise ValueError(f'Exercise data not found for exer_id={exer_id}')
        result_set = list(result_set[0])
        _icon_index = columns.index('icons_dict')
        result_set[_icon_index] = self.get_icon_bytes_from_icons_dict(result_set[_icon_index])
        exercise_data = ExerciseData(*result_set)
        return exercise_data

    def select_exercise_icon(self, exer_id):
        stat = f'SELECT icons_dict FROM {self.exercises_table} WHERE id = ?'
        params = (exer_id, )
        result_set = self.execute_statement(stat, params=params)
        if not result_set:
            raise ValueError(f'Exercise with id "{exer_id}" not found')
        icons_dict = result_set[0][0]
        icon_bytes = self.get_icon_bytes_from_icons_dict(icons_dict)
        return icon_bytes

    def select_from_table(self, table_name, columns, filters=None, get_none=False):
        """Selects columns from any table with set filters

        If result set has 1 value, then it returns that result tuple
        If result set has 1 value, then it returns that result tuple
        :param table_name <str>
        :param columns <str> or list(<str>) List of column names or column name
        :param filters: <dict> or None
        :param get_none: <bool>
        :return List(<tuple<object>>) or <tuple<object>> or <object>
        """
        columns = (columns,) if type(columns) not in (tuple, list) else columns
        columns_str = ', '.join(columns)
        statement = f'SELECT {columns_str} FROM {table_name}'
        params = None
        if filters:
            statement_filter, params = self._create_filter_statement(filters)
            statement += statement_filter
        results_set = self.execute_statement(statement, params=params)
        if not results_set:
            if get_none:
                return None
            raise ValueError(f'Statement="{statement}", '
                             f'with params="{params}" found no results.')
        if len(results_set[0]) == 1:
            # If every row in results set has 1 value, return tuple of these values
            results_set = tuple([res[0] for res in results_set])
        if len(results_set) == 1:
            # If only 1 row exists in results set, return only that 1 row
            results_set = results_set[0]
        return results_set

    def insert_exercise(self, exer_data):
        """Inserts exercise into table 'exercises'
        :param exer_data <ExerciseData>
        :returns <bool>
        """
        stat = f'INSERT INTO {self.exercises_table}(name, type_id, body_part_id, ' \
               f'main_muscle_group_id, minor_muscle_group_id, equipment_id, ' \
               f'position_1, position_2, icons_dict, instructions, favorite, ' \
               f'link, user_permission) ' \
               'VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        params = (exer_data.name, exer_data.type_id, exer_data.body_part_id,
                  exer_data.main_muscle_id, exer_data.minor_muscle_id,
                  exer_data.equipment_id, exer_data.pos1, exer_data.pos2,
                  exer_data.icons_dict_bytes, exer_data.instructions,
                  exer_data.favorite, exer_data.link, exer_data.user_permission)
        inserted = self.execute_statement(stat, params=params)
        return inserted

    def update_exercise(self, exer_id, new_column_values):
        """Updates exercise row in 'exercises'

        :param exer_id <ExerciseData>
        :param new_column_values <dict> Key=%column%, Value=%value%
        :returns <bool>
        """
        keys = tuple(new_column_values.keys())
        set_stat = f'SET {keys[0]} = ?'
        for i in range(1, len(keys)):
            set_stat += f', {keys[i]} = ?'
        stat = f'UPDATE {self.exercises_table} ' + set_stat + ' WHERE id = ?'
        params = tuple(new_column_values.values()) + (exer_id,)
        updated = self.execute_statement(stat, params=params)
        return updated

    def delete_exercise(self, exer_id):
        stat = 'DELETE FROM exercises WHERE id = ?'
        deleted = self.execute_statement(stat, params=(exer_id,))
        return deleted

    def update_table(self, table_name, column_values, exer_id):
        statement = f"UPDATE {table_name} SET "
        for i, column_name in enumerate(column_values.keys()):
            statement += f"{column_name} = ?"
            statement += ', ' if i < (len(column_values) - 1) else ' '
        params = tuple([self._format_column_value(col_value) for col_value in column_values.values()])
        statement += f'WHERE id = {exer_id};'
        updated = self.execute_statement(statement, params=params)
        return updated

    def select_week_plan_info(self, filters=None):
        stat = 'SELECT week_plan.id, week_plan.name, week_plan.plan_type_id, plan_type.name, ' \
               'plan_type.icon, week_plan.user_permission ' \
               'FROM week_plan ' \
               'LEFT JOIN plan_type ON week_plan.plan_type_id = plan_type.id '
        params = None
        if filters:
            statement_filter, params = self._create_filter_statement(filters)
            stat += statement_filter
        result_set = self.execute_statement(stat, params=params)
        # assert result_set, 'Week plan doent exist!'
        week_plan_info = [PlanListRow(*res) for res in result_set] if result_set else []
        return week_plan_info

    def select_plan_workouts_data(self, plan_id):
        stat = f'SELECT workouts FROM week_plan WHERE id = ?;'
        params = (plan_id,)
        result_set = self.execute_statement(stat, params=params)
        assert result_set, 'Week plan doesnt exist!'
        # week_plan_bytes = pickle.loads(result_set[0][0])
        workouts_data = pickle.loads(result_set[0][0])
        return workouts_data

    def insert_into_week_plan(self, plan_data, user_permission):
        """Inserts new plan into table 'week_plan'

        @:param plan_data: <PlanData>
        """
        stat = f'INSERT INTO week_plan(name, plan_type_id, workouts, user_permission) ' \
               f'VALUES(?, ?, ?, ?)'
        workouts_data_bytes = pickle.dumps(plan_data.workouts_data)
        params = (plan_data.name, plan_data.type_id, workouts_data_bytes, user_permission)
        inserted = self.execute_statement(stat, params=params)
        if inserted:
            logging.info(f'New plan with name {plan_data.name} inserted!')
        return inserted

    def delete_week_plan(self, plan_id):
        # TODO: maybe remove "plan_name"?
        stat = 'DELETE FROM week_plan WHERE id = ?'
        return self.execute_statement(stat, params=(plan_id,))

    def update_week_plan(self, plan_data):
        stat = 'UPDATE week_plan SET ' \
               'name = ?, plan_type_id = ?, workouts = ? ' \
               'WHERE id = ?;'
        workouts_data_bytes = pickle.dumps(plan_data.workouts_data)
        params = (plan_data.name, plan_data.type_id, workouts_data_bytes, plan_data.id)
        updated = self.execute_statement(stat, params=params)
        return updated

    def insert_into_workout(self, workout_data, user_permission):
        stat = f'INSERT INTO workout' \
               f'(name, type_id, data, workout_time, user_permission) ' \
               f'VALUES(?, ?, ?, ?, ?)'
        workout_rows_bytes = pickle.dumps(workout_data.rows_data)
        params = (workout_data.name, workout_data.type_id, workout_rows_bytes,
                  workout_data.workout_time, user_permission)
        inserted = self.execute_statement(stat, params=params)
        return inserted

    def select_workout_info(self, filters=None):
        stat = 'SELECT workout.id, workout.name, plan_type.name, plan_type.icon, ' \
               'workout.user_permission ' \
               'FROM workout ' \
               'LEFT JOIN plan_type ON workout.type_id = plan_type.id '
        params = None
        if filters:
            statement_filter, params = self._create_filter_statement(filters)
            stat += statement_filter
        result_set = self.execute_statement(stat, params=params)
        # assert result_set, 'Week plan doent exist!'
        workout_info = [WorkoutListRow(*res) for res in result_set] if result_set else []
        return workout_info

    def update_workout(self, workout_id, workout_data):
        stat = 'UPDATE workout SET ' \
               'name = ?, type_id = ?, data = ?, workout_time = ? ' \
               'WHERE id = ?;'
        workout_rows_bytes = pickle.dumps(workout_data.rows_data)
        params = (workout_data.name, workout_data.type_id, workout_rows_bytes,
                  workout_data.workout_time, workout_id)
        updated = self.execute_statement(stat, params=params)
        return updated

    def delete_workout(self, workout_id):
        stat = 'DELETE FROM workout WHERE id = ?'
        deleted = self.execute_statement(stat, params=(workout_id,))
        return deleted

    def get_table_row_obj_from_data(self, table_row_data):
        row_type_str_to_class = {
            str(TableRowType.SS_TOP): SupersetTopRow,
            str(TableRowType.SS_BOTTOM): SupersetBottomRow,
            str(TableRowType.EXER_EXEC): ExerciseExecutionRow,
        }
        table_row_class = row_type_str_to_class[table_row_data[0]]
        if table_row_class == ExerciseExecutionRow:
            exer_id = table_row_data[1]
            icon_bytes = self.select_exercise_icon(exer_id)
            table_row_data = (exer_id, icon_bytes) + table_row_data[2:]
        else:
            table_row_data = table_row_data[1:]
        return table_row_class(*table_row_data)

    def select_workout_rows_data(self, workout_id):
        stat = f'SELECT data ' \
               'FROM workout ' \
               'WHERE id = ?'
        params = (workout_id,)
        result_set = self.execute_statement(stat, params=params)
        workout_rows_data = pickle.loads(result_set[0][0])
        return workout_rows_data

    @staticmethod
    def _format_column_value(value):
        if type(value) == str:
            value = value.replace("'", "''")
        return value
