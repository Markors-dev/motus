import re

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui

from database.data_model import SupersetTopRow, SupersetBottomRow, SupersetRow
from gui.colors import Colors
from gui.dialogs import ErrorMessage
from util.value import is_str_int
from workout import execution_data_valid, get_error_msg_for_col, exercise_name_valid, \
                    EXERCISE_NAME_CHECK_ERROR_MSG


class TableViewerItemDelegate(QtWidgets.QStyledItemDelegate):
    """Item delegate class for editor 'WorkoutTableViewer'

    This class was created to change superset rows background color
    and font attributes.
    """
    def __init__(self):
        super().__init__()

    def initStyleOption(self, option, index):
        """Sets cell style for superset rows.

        Style attributes: bg color, font size, italic(True) and bold(True).

        :param option <QStyleOptionViewItem> Item style option object
        :param index <QModelIndex> Table cell index object
        :return <None>
        """
        super().initStyleOption(option, index)
        model = index.model()
        table_row = model.exer_exec_rows[index.row()]
        if isinstance(table_row, SupersetRow):
            if type(table_row) == SupersetTopRow:
                bg_brush = QtGui.QBrush(QtGui.QColor(*Colors.SUPERSET_TOP.rgb))
            else:  # == SupersetBottomRow
                bg_brush = QtGui.QBrush(QtGui.QColor(*Colors.SUPERSET_BOTTOM.rgb))
            option.backgroundBrush = bg_brush
            option.font.setPointSize(SupersetRow.POINT_SIZE)
            option.font.setItalic(True)
            option.font.setBold(True)


class TableEditorItemDelegate(TableViewerItemDelegate):
    """Item delegate class for editor '_WorkoutTableEditor'

    This class was created to handle editing of cell data.
    """
    signal_table_data_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

    def createEditor(self, parent, option, index):
        """Creates and returns editor for editing cell text

        :param parent <QWidget> Parent widget of editor
        :param option <QStyleOptionViewItem> Item style option object
        :param index <QModelIndex> Table cell index object
        :return <QLineEdit>
        """
        editor = super().createEditor(parent, option, index)
        return editor

    def setEditorData(self, editor, index):
        """Sets editor text by removing ' min'(from end), if it exists

        :param editor <QLineEdit> Editor for editing cell text
        :param index <QModelIndex> Table cell index object
        :return <None>
        """
        text = str(index.data())
        cell_on_reps = index.model().exer_exec_rows[index.row()].on_reps
        if index.column() == 3 or index.column() == 2 and not cell_on_reps:
            assert text.endswith(' min'), 'Cell text should end with " min"!'
            text = text[:text.index(' min')]
        editor.setText(text)

    def setModelData(self, label, model, index):
        """Sets cell model data from editor

        :param label <QLineEdit> Editor for editing cell text
        :param model <EditableTableModel> Model data object
        :param index <QModelIndex> Table cell index object
        :return <None>
        """
        label_text = label.text()
        col = index.column()
        if col == 0:  # Check exercise name value
            if exercise_name_valid(label_text):
                model.setData(index, label_text, QtCore.Qt.ItemDataRole.EditRole)
                self.signal_table_data_changed.emit()
            else:
                ErrorMessage('Exercise name invalid', EXERCISE_NAME_CHECK_ERROR_MSG).exec()
        else:  # Check values for sets, reps and pause
            if is_str_int(label_text) and execution_data_valid(col, int(label_text)):
                model.setData(index, label_text, QtCore.Qt.ItemDataRole.EditRole)
                self.signal_table_data_changed.emit()
            else:
                ErrorMessage('Column value invalid', get_error_msg_for_col(col)).exec()
