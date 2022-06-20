import io
import pickle
from enum import Enum
from PIL import Image
from collections import namedtuple

from PyQt5.QtCore import QAbstractListModel, QAbstractTableModel, Qt, QModelIndex
from PyQt5 import QtGui
from PyQt5 import QtCore

from util import images
from util.value import convert_to_title_format, wrap_text, pad_text
from gui.flags import AlignFlag, ItemFlag, ImageFp


class TableRowType(Enum):
    SS_TOP = 1
    SS_BOTTOM = 2
    EXER_EXEC = 3


# ----- Methods used in this module -----

def _get_icon_from_bytes(image_bytes):
    """Returns <QtGui.QIcon> object from image <byte> object"""
    qicon = QtGui.QIcon()
    pixmap = QtGui.QPixmap()
    pixmap.loadFromData(image_bytes)
    qicon.addPixmap(pixmap)
    return qicon


# ---------- Data objects for exporting,importing and DB ----------

# ----- For exporting/importing motfiles -----
PlanData = namedtuple('PlanData', ['id', 'name', 'type_id', 'workouts_data'])
WorkoutData = namedtuple('WorkoutData', ['name', 'type_id', 'rows_data', 'workout_time'])
ExerciseExecutionWorkData = namedtuple('ExerciseExecutionWorkData',
                                       ['sets', 'reps', 'pause', 'on_reps'])
# ----- For exporting plan to pdf -----
PlanPdfData = namedtuple('PlanPdfData', ['name', 'type', 'workouts', 'links'])
WorkoutPdfData = namedtuple('WorkoutPdfData', ['name', 'type', 'type_icon_bytes',
                                               'table_rows', 'workout_time'])

# ----- For inserting new exercise in DB -----
NewExerciseData = namedtuple('NewExerciseData',
                             ['name', 'type_id', 'body_part_id', 'main_muscle_id',
                              'minor_muscle_id', 'equipment_id', 'pos1', 'pos2',
                              'icons_dict_bytes', 'instructions', 'favorite', 'link',
                              'user_permission'])


class ExerciseData:
    """Used for storing and displaying all exercise data"""

    def __init__(self, exer_id, name, exer_type, body_part, main_muscle_group, minor_muscle_group,
                 equipment, main_muscle_group_image, minor_muscle_group_image, pos1_image, pos2_image,
                 instructions, icon_bytes, favorite, link, user_permission,
                 remove=None, pos1=None, icon_slice=None, edited=None):  # <-- only for editing(maybe not in use)
        """ Exercise object
        :param exer_id: <int>
        :param name: <str>
        :param exer_type: <str>
        :param body_part: <str>
        :param main_muscle_group: <str>
        :param minor_muscle_group: <str>
        :param equipment: <str>
        :param main_muscle_group_image: <bytes>
        :param minor_muscle_group_image: <bytes> or None
        :param equipment: <str>
        :param pos1_image: <bytes>
        :param pos2_image: <bytes>
        """
        # ----- Helper data -----
        self.icon_bytes = icon_bytes
        # ----- Exercise info -----
        self.exer_id = exer_id
        self.name = name
        self.exer_type = exer_type
        self.body_part = body_part
        self.main_muscle_group = main_muscle_group
        self.minor_muscle_group = minor_muscle_group
        self.equipment = equipment
        self.main_muscle_group_image = main_muscle_group_image
        self.minor_muscle_group_image = minor_muscle_group_image if minor_muscle_group_image else None
        self.pos1_image = pos1_image
        self.pos2_image = pos2_image
        self.instructions = instructions
        self.icon = _get_icon_from_bytes(self.icon_bytes)
        self.favorite = True if favorite else False
        self.link = link
        self.user_permission = user_permission
        # below attrs used only for editing and NOT in normal use
        self.remove = remove
        self.pos1 = pos1
        self.icon_slice = icon_slice
        self.edited = edited

    @classmethod
    def get_empty_exercise_data(cls):
        no_image_bytes = images.get_file_binary(ImageFp.NO_IMAGE)
        return cls(-1, '-', '-', '-', '-', '-', '-', no_image_bytes, no_image_bytes, no_image_bytes, no_image_bytes,
                   '', no_image_bytes, 0, None, 0)


# ---------- Data Model Rows ----------

class ExerciseListRow:
    """Exercise data row for <ExerciseListModel> """

    def __init__(self, exer_id, name, icon_bytes):
        # Data attributes
        self.icon_bytes = icon_bytes
        # Data model attributes
        self.exer_id = exer_id
        self.name = name
        self.icon = _get_icon_from_bytes(icon_bytes)


class _TableRow:
    """Base class for all table rows used for storing row type"""

    def __init__(self, row_type):
        self.row_type = row_type


class SupersetRow(_TableRow):
    """Base class for <SupersetTopRow> and <SupersetBottomRow>"""

    POINT_SIZE = 9
    ROW_HEIGHT = 15

    def __init__(self, row_type, numb):
        super().__init__(row_type)
        self.numb = numb


class SupersetTopRow(SupersetRow):
    def __init__(self, numb):
        super().__init__(TableRowType.SS_TOP, numb)

    @property
    def text(self):
        return f'SUPERSET {self.numb}'

    def __getitem__(self, item):
        if item == 0:
            return self.text
        else:
            return ''

    def to_data(self):
        """For database serialization """
        return str(TableRowType.SS_TOP), self.numb


class SupersetBottomRow(SupersetRow):
    def __init__(self, numb, sets, pause):
        super().__init__(TableRowType.SS_BOTTOM, numb)
        self.sets = sets
        self.reps = ''  # always empty(it's not editable)
        self.pause = pause

    def __getitem__(self, item):
        if item in (0, 2):
            return ''
        elif item == 1:
            return self.sets
        elif item == 3:
            return self.pause

    def __setitem__(self, key, value):
        if key == 1:
            self.sets = value
        elif key == 3:
            self.pause = value

    def to_data(self):
        """For serialization """
        return str(TableRowType.SS_BOTTOM), self.numb, self.sets, self.pause


class ExerciseExecutionRow(_TableRow):
    """Table row data class for exercises in tables <WorkoutTableViewer>
    and <_WorkoutTableEditor>
    """

    def __init__(self, exer_id, icon_bytes, name, sets, reps, pause, on_reps):
        """Data type class for Table Model object.

        :param exer_id: <int> Exercise id from DB(*)
        :param icon_bytes: <bytes> Icon image in bytes(*)
        :param name: <str> Exercise name
        :param sets: <str> Exercise execution number of sets
        :param reps: <str> Exercise execution number of reps
        :param pause: <str> Exercise execution pause(min) after execution
        :param on_reps: <bool> Is exercise executed in reps. If not, in time(min)
        NOTE: *is not used in table. It doesn't have an index(see self.__getitem__)
        """
        super().__init__(TableRowType.EXER_EXEC)
        # ----- Row attributes -----
        self.exer_id = exer_id
        self.icon_bytes = icon_bytes
        self.on_reps = on_reps
        self.superset_numb = None
        # ----- Row Data(displayed in table) ----
        self.icon_and_name = (_get_icon_from_bytes(icon_bytes), name)
        self.sets = sets
        self.reps = reps
        self.pause = pause

    def __getitem__(self, index):
        if type(index) != int:
            raise TypeError(f'TypeError: list indices must be integers, not {type(index)}')
        if index not in (0, 1, 2, 3):
            raise IndexError(f'List index(={index}) out of range([0, 3]) !')
        return self._value_for_index(index)

    def __setitem__(self, index, value):
        if type(index) != int:
            raise TypeError(f'TypeError: list indices must be integers, not {type(index)}')
        if index not in (0, 1, 2, 3):
            raise IndexError(f'List index(={index}) out of range([0, 3]) !')
        setattr(self, self._attr_name_for_index(index), value)

    def to_data(self):
        """For serialization """
        return str(TableRowType.EXER_EXEC), self.exer_id, self.icon_and_name[1], self.sets, \
               self.reps, self.pause, self.on_reps

    def _value_for_index(self, index):
        value_for_index = {
            0: self.icon_and_name,
            1: self.sets,
            2: self.reps,
            3: self.pause,
        }
        return value_for_index[index]

    @staticmethod
    def _attr_name_for_index(index):
        attr_name_for_index = {
            0: 'icon_and_name',
            1: 'sets',
            2: 'reps',
            3: 'pause',
        }
        return attr_name_for_index[index]


class PlanListRow:
    """Row data class for list <PlanListView>"""

    def __init__(self, plan_id, name, plan_type_id, plan_type, icon, user_permission):
        # ----- Attributes -----
        self.plan_type_id = plan_type_id
        self.user_permission = user_permission
        # ----- Row data -----
        self.plan_id = plan_id
        self.name = name
        self.plan_type = plan_type
        # TODO: Fix is assignment !
        self.icon = _get_icon_from_bytes(icon) if type(icon) == bytes else icon


class WorkoutListRow:
    """Row data object for list <WorkoutListView>"""

    def __init__(self, workout_id, name, workout_type, icon_bytes, user_permission):
        # ----- Attributes -----
        self.workout_id = workout_id
        self.icon_bytes = icon_bytes
        self.user_permission = user_permission
        # ----- Row data  -----
        self.name = name
        self.workout_type = workout_type
        self.icon = _get_icon_from_bytes(icon_bytes)


# ----- Data Models -----

class ExerciseListModel(QAbstractListModel):
    """ Data model class for list <ExerciseListView>"""

    def __init__(self, exercise_rows):
        """
        :param exercise_rows: [<ExerciseListRow>, ]
        """
        super().__init__()
        self.rows = exercise_rows

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            row = self.rows[index.row()]
            return row.name

        if role == Qt.ItemDataRole.DecorationRole:
            row = self.rows[index.row()]
            return row.icon

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            self.rows[index.row()] = value
            return True
        return False

    def removeRows(self, row, count=1, parent=None):
        start_numb_rows = len(self.rows)
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for row_to_del in range(row + count - 1, row - 1, -1):
            del self.rows[row_to_del]
        self.endRemoveRows()
        numb_rows_removed = start_numb_rows - len(self.rows)
        rows_removed = True if numb_rows_removed == count else False
        if rows_removed:
            return True
        else:
            return False

    def rowCount(self, index=None):
        return len(self.rows)

    def flags(self, index):
        return ItemFlag.Selectable | ItemFlag.Enabled | ItemFlag.Editable


class PlanListModel(QAbstractListModel):
    """ Data model class for list <PlanListView>"""

    ICON_TEXT_LEN = 18

    def __init__(self, rows, *args, **kwargs):
        """
        :param plan_rows: [<PlanListRow>, ]
        """
        super().__init__(*args, **kwargs)
        self.rows = rows or []

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            row = self.rows[index.row()]
            if len(row.name) < self.ICON_TEXT_LEN:
                text = pad_text(row.name, min_len=self.ICON_TEXT_LEN)
            elif len(row.name) > self.ICON_TEXT_LEN:
                text = wrap_text(row.name, line_length=self.ICON_TEXT_LEN)
            else:
                text = row.name
            return text
        if role == Qt.ItemDataRole.DecorationRole:
            row = self.rows[index.row()]
            return row.icon
        if role == Qt.ItemDataRole.ToolTipRole:
            row = self.rows[index.row()]
            return convert_to_title_format(row.name)

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            self.rows[index.row()].name = value
            return True
        return False

    def removeRows(self, row, count, parent=None):
        start_numb_rows = len(self.rows)
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for row_to_del in range(row + count - 1, row - 1, -1):
            del self.rows[row_to_del]
        self.endRemoveRows()
        numb_rows_removed = start_numb_rows - len(self.rows)
        rows_removed = True if numb_rows_removed == count else False
        if rows_removed:
            return True
        else:
            return False

    def rowCount(self, index=None):
        return len(self.rows)

    def flags(self, index):
        return ItemFlag.Selectable | ItemFlag.Enabled


class WorkoutListModel(QAbstractListModel):
    """ Data model class for list <WorkoutListView>"""

    ICON_TEXT_LEN = 15

    def __init__(self, rows, *args, **kwargs):
        """
        :param rows: [<WorkoutListRow>, ]
        """
        super().__init__(*args, **kwargs)
        self.rows = rows or []

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            row = self.rows[index.row()]
            if len(row.name) < self.ICON_TEXT_LEN:
                text = pad_text(row.name, min_len=self.ICON_TEXT_LEN)
            elif len(row.name) > self.ICON_TEXT_LEN:
                text = wrap_text(row.name, line_length=self.ICON_TEXT_LEN)
            else:
                text = row.name
            return text
        if role == Qt.ItemDataRole.DecorationRole:
            row = self.rows[index.row()]
            return row.icon
        if role == Qt.ItemDataRole.ToolTipRole:
            row = self.rows[index.row()]
            return convert_to_title_format(row.name)

    def removeRows(self, row, count, parent=None):
        start_numb_rows = len(self.rows)
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for row_to_del in range(row + count - 1, row - 1, -1):
            del self.rows[row_to_del]
        self.endRemoveRows()
        numb_rows_removed = start_numb_rows - len(self.rows)
        rows_removed = True if numb_rows_removed == count else False
        if rows_removed:
            return True
        else:
            return False

    def rowCount(self, index=None):
        return len(self.rows)

    def flags(self, index):
        return ItemFlag.Selectable | ItemFlag.Enabled


class TableModel(QAbstractTableModel):
    """ Data model class for table <WorkoutTableViewer>"""

    HEADER_LABELS = ['Exercise', 'Sets', 'Reps/Time', 'Pause']

    def __init__(self, exer_exec_rows=None):
        """
        :param <[ExerciseExecutionRow]>
        """
        super().__init__()
        self.exer_exec_rows = exer_exec_rows or []

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and \
                orientation == Qt.Orientation.Horizontal:
            return self.HEADER_LABELS[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)

    def data(self, index, role):
        exer_exec_row = self.exer_exec_rows[index.row()]
        if isinstance(exer_exec_row, SupersetRow):
            return self._superset_data(index, role)
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                data = exer_exec_row[index.column()][1]
            else:  # col in (1, 2, 3)
                data = exer_exec_row[index.column()]
                if col == 2 and not exer_exec_row.on_reps:
                    data = f'{data} min'
                if col == 3 and data != '-':
                    data = f'{data} min'
            return data
        if role == Qt.ItemDataRole.DecorationRole:
            if index.column() == 0:
                return exer_exec_row[index.column()][0]

        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 0:
                return AlignFlag.VCenter | AlignFlag.Left
            else:
                return AlignFlag.Center

    def _superset_data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            table_row = self.exer_exec_rows[index.row()]
            if type(table_row) == SupersetTopRow:
                if index.column() == 0:
                    return table_row[index.column()]
                else:
                    return ''
            else:  # == SupersetBottomRow
                data = table_row[index.column()]
                if index.column() == 3:
                    data = f'{data} min'
                return data
        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 0:
                return AlignFlag.Right | AlignFlag.VCenter
            else:
                return AlignFlag.Center | AlignFlag.VCenter

    def flags(self, index):
        return ItemFlag.Enabled | ItemFlag.Selectable

    def rowCount(self, index=None):
        return len(self.exer_exec_rows)

    def columnCount(self, index=None):
        return len(self.HEADER_LABELS)


class EditableTableModel(QAbstractTableModel):
    """ Data model class for table <_WorkoutTableEditor>"""

    HEADER_LABELS = ['Exercise', 'Sets', 'Reps/Time', 'Pause']

    def __init__(self, exer_exec_rows=None):
        """
        :param <[ExerciseExecutionRow]>
        """
        super().__init__()
        self.exer_exec_rows = exer_exec_rows or []
        # self.superset_rows = []

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.HEADER_LABELS[section]
            else:
                return QAbstractTableModel.headerData(self, section, orientation, role)

    def data(self, index, role):
        # Superset row data - separate method used
        exer_exec_row = self.exer_exec_rows[index.row()]
        if isinstance(exer_exec_row, SupersetRow):
            return self._superset_data(index, role)
        #
        if role == Qt.ItemDataRole.EditRole:
            value = exer_exec_row[index.column()]
            return str(value)
        if role == Qt.ItemDataRole.DisplayRole:
            col = index.column()
            if col == 0:
                data = exer_exec_row[index.column()][1]
            else:  # col in (1, 2, 3)
                data = exer_exec_row[index.column()]
                if col == 2 and not exer_exec_row.on_reps:
                    data = f'{data} min'
                if col == 3 and data != '-':
                    data = f'{data} min'
            return data
        if role == Qt.ItemDataRole.DecorationRole:
            if index.column() == 0:
                return exer_exec_row[index.column()][0]
        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 0:
                return AlignFlag.VCenter | AlignFlag.Left
            else:
                return AlignFlag.Center

    def _superset_data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            table_row = self.exer_exec_rows[index.row()]
            if type(table_row) == SupersetTopRow:
                if index.column() == 0:
                    return table_row[index.column()]
                else:
                    return ''
            else:  # == SupersetBottomRow
                data = table_row[index.column()]
                if index.column() == 3:
                    data = f'{data} min'
                return data
        if role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == 0:
                return AlignFlag.Right | AlignFlag.VCenter
            else:
                return AlignFlag.Center | AlignFlag.VCenter

    def insertRows(self, row, count, new_row_data):
        start_numb_rows = len(self.exer_exec_rows)
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        self.exer_exec_rows.insert(row, new_row_data)
        self.endInsertRows()
        rows_inserted = start_numb_rows - len(self.exer_exec_rows)
        return rows_inserted

    def removeRows(self, row, count, parent=None):
        start_numb_rows = len(self.exer_exec_rows)
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for row_to_del in range(row + count - 1, row - 1, -1):
            del self.exer_exec_rows[row_to_del]
        self.endRemoveRows()
        numb_rows_removed = start_numb_rows - len(self.exer_exec_rows)
        rows_removed = True if numb_rows_removed == count else False
        return rows_removed

    def setData(self, index, value, role):
        exer_exec_row = self.exer_exec_rows[index.row()]
        if role == Qt.ItemDataRole.EditRole:
            if index.column() == 0:
                _icon = exer_exec_row[0][0]
                exer_exec_row[index.column()] = (_icon, value)
            else:
                exer_exec_row[index.column()] = int(value)
            return True
        return False

    def flags(self, index):
        exer_exec_row = self.exer_exec_rows[index.row()]
        if isinstance(exer_exec_row, SupersetRow):
            if type(exer_exec_row) == SupersetTopRow:
                return ItemFlag.Enabled | ItemFlag.Selectable
            else:  # == SupersetBottomRow
                if index.column() in (1, 3):
                    return ItemFlag.Enabled | ItemFlag.Selectable | ItemFlag.Editable
                else:
                    return ItemFlag.Enabled | ItemFlag.Selectable
        else:  # == ExerciseExecutionRow
            if exer_exec_row.superset_numb:
                if index.column() in (0, 2):
                    return ItemFlag.Enabled | ItemFlag.Selectable | ItemFlag.Editable
                else:
                    return ItemFlag.Enabled | ItemFlag.Selectable
            else:
                return ItemFlag.Enabled | ItemFlag.Selectable | ItemFlag.Editable

    def rowCount(self, index=None):
        return len(self.exer_exec_rows)

    def columnCount(self, index=None):
        return len(self.HEADER_LABELS)
