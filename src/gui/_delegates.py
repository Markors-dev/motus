import re

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui

from database.data_model import SupersetTopRow, SupersetBottomRow, SupersetRow
from gui.colors import Colors
from workout import execution_data_valid, get_error_msg_for_col, exercise_name_valid, \
                    EXERCISE_NAME_CHECK_ERROR_MSG
from gui.dialogs import ErrorMessage


class TableViewerItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self):
        super().__init__()

    def setModelData(self, label, model, index):
        model.setData(index, label.text(), QtCore.Qt.ItemDataRole.DisplayRole)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        model = index.model()
        table_row = model.exer_exec_rows[index.row()]
        # if not model:
        #     print(f'---> initStyleOption: index row= {index.row()}')
        if isinstance(table_row, SupersetRow):
            if type(table_row) == SupersetTopRow:
                # Set Superset row background and font style
                option.backgroundBrush = QtGui.QBrush(QtGui.QColor(*Colors.SUPERSET_TOP.rgb))
            else:  # == SupersetBottomRow
                option.backgroundBrush = QtGui.QBrush(QtGui.QColor(*Colors.SUPERSET_BOTTOM.rgb))
            option.font.setPointSize(SupersetRow.POINT_SIZE)
            option.font.setItalic(True)
            option.font.setBold(True)


class TableEditorItemDelegate(TableViewerItemDelegate):
    """Delegate for TableView '_WorkoutTableEditor'"""
    signal_table_data_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        return editor

    def setEditorData(self, editor, index):
        text = str(index.data())
        text = text[:text.index(' min')] if ' min' in text else text
        editor.setText(text)

    def setModelData(self, label, model, index):
        label_text = label.text()
        col = index.column()
        # header_text = model.HEADER_LABELS[col]
        if col == 0:  # Check exercise name value
            if exercise_name_valid(label_text):
                model.setData(index, label_text, QtCore.Qt.ItemDataRole.EditRole)
                self.signal_table_data_changed.emit()
            else:
                ErrorMessage('Exercise name invalid', EXERCISE_NAME_CHECK_ERROR_MSG).exec()
        else:  # Check values for sets, reps and pause
            if execution_data_valid(col, int(label_text)):
                model.setData(index, label_text, QtCore.Qt.ItemDataRole.EditRole)
                self.signal_table_data_changed.emit()
            else:
                ErrorMessage('Column value invalid', get_error_msg_for_col(col)).exec()
