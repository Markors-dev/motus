import pdb

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from database.db_obj import DB
from database.data_model import PlanListRow, WorkoutListRow, WorkoutListModel, PlanListModel
from config import DAYS_TITLE, AppMode, APP_MODE
from settings import Settings
from gui.dialogs import ErrorMessage, QuestionDialog, InfoMessage
from gui.colors import Colors
from gui.flags import PermissionType
from gui.util import find_widget_by_attr, get_parent
from ._scroll import MyScrollBar


class _ListViewBase(QtWidgets.QListView):
    def __init__(self, parent):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollBar(MyScrollBar(self))
        self.horizontalScrollBar().setEnabled(False)

    def select_index(self, index_row):
        """Selects index with given index row.

        :param index_row: int
        :return bool
        """
        index = self.model().index(index_row, 0)
        sel_model = self.selectionModel()
        sel_model.clearSelection()
        sel_model.select(index, sel_model.SelectionFlag.Select)

    def get_selected_item_id(self):
        """Returns data id from the selected index.

        The data obj on the selected index must have an attribute 'id'
        :return <int>
        """
        indexes = self.selectedIndexes()
        if not indexes:
            raise ValueError(f'No rows are selected in "{self.objectName()}"')
        item_data = self.model().rows[indexes[0].row()]
        list_class_to_id_dict = {
            'ExerciseListView': 'exer_id',
            'PlanListView': 'plan_id',
            'WorkoutListView': 'workout_id',
        }
        id_attr_name = list_class_to_id_dict[self.__class__.__name__]
        item_id = getattr(item_data, id_attr_name)
        return item_id


class ExerciseListView(_ListViewBase):
    signal_exercise_changed = QtCore.pyqtSignal(int)
    signal_add_exercise_to_book = QtCore.pyqtSignal(int, str)
    signal_add_exercise_to_table = QtCore.pyqtSignal(int, str)
    signal_show_exercise_info = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('list_exercises')
        _size = Settings().getValue('icon_size')
        self.setIconSize(QtCore.QSize(_size[0], _size[1]))
        self.setStyleSheet('''
            .ExerciseListView {
                background-color: %s;
                alternate-background-color: %s;
            }
            .ExerciseListView::item {
                margin: 0px;
            }
        ''' % ('#FFFFFF', Colors.ROW_ALT.hex))
        self.setAlternatingRowColors(True)
        self.setWordWrap(True)
        self.setDragEnabled(True)

        # ----- Data -----
        self.context_menu = None  # For testing
        self.add_to_table_submenu = None  # For testing

    def get_selected_row(self):
        indexes = self.selectedIndexes()
        if not indexes:
            raise ValueError(f'No rows are selected in "{self.objectName()}"')
        return self.model().rows[indexes[0].row()]

    def run_tab_exercises_context_menu(self, event):
        self.context_menu = QtWidgets.QMenu(self)
        action_add_to_bookmarks = self.context_menu.addAction("Add to bookmarks")
        self.add_to_table_submenu = self.context_menu.addMenu("Add to Planner table: ")
        table_actions = []
        for table in DAYS_TITLE:
            table_actions.append(self.add_to_table_submenu.addAction(table))
        #
        action = self.context_menu.exec(self.mapToGlobal(event.pos()))
        if action == action_add_to_bookmarks:
            exer_row = self.get_selected_row()
            self.signal_add_exercise_to_book.emit(exer_row.exer_id, exer_row.name)
        elif action in table_actions:
            self.signal_add_exercise_to_table.emit(self.get_selected_item_id(), action.text().lower())

    def run_tab_planner_context_menu(self, event):
        self.context_menu = QtWidgets.QMenu(self)
        self.add_to_table_submenu = self.context_menu.addMenu("Add to table: ")
        table_actions = []
        for table in DAYS_TITLE:
            table_actions.append(self.add_to_table_submenu.addAction(table))
        go_to_info = self.context_menu.addAction("Go to info")
        action = self.context_menu.exec(self.mapToGlobal(event.pos()))
        exer_id = self.get_selected_item_id()
        if action == go_to_info:
            self.signal_show_exercise_info.emit(exer_id)
        elif action in table_actions:
            self.signal_add_exercise_to_table.emit(exer_id, action.text().lower())

    def remove_exercise(self, exer_id):
        exer_row = find_widget_by_attr(self.model().rows, 'exer_id', exer_id)
        sel_row = self.model().rows.index(exer_row)
        self.model().removeRows(sel_row)

    # ----- SLOTS -----

    def selectionChanged(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes:
            return  # no indexes present
        sel_row = indexes[0].row()
        exer_id = self.model().rows[sel_row].exer_id
        self.signal_exercise_changed.emit(exer_id)

    def mouseDoubleClickEvent(self, event):
        if get_parent(self, 'tab_planner'):
            self.signal_add_exercise_to_table.emit(self.get_selected_item_id(), '')
        elif get_parent(self, 'tab_exercises'):
            exer_row = self.get_selected_row()
            self.signal_add_exercise_to_book.emit(exer_row.exer_id, exer_row.name)

    def contextMenuEvent(self, event):
        if get_parent(self, 'tab_planner'):
            self.run_tab_planner_context_menu(event)
        elif get_parent(self, 'tab_exercises'):
            self.run_tab_exercises_context_menu(event)
        # <-- possible other tabs in the future
        return None

    def keyPressEvent(self, event):
        """
        :param event: <QtCore.QtGui.QKeyEvent>
        :return: None
        """
        super().keyPressEvent(event)
        sel_row = self.selectedIndexes()[0].row()
        self.signal_exercise_changed.emit(self.model().rows[sel_row].exer_id)


class PlanListView(_ListViewBase):
    signal_plan_selected = QtCore.pyqtSignal(PlanListRow)
    signal_select_next_plan = QtCore.pyqtSignal()
    signal_load_plan = QtCore.pyqtSignal(PlanListRow)

    def __init__(self, parent, perm_type=None):
        super().__init__(parent)
        self.setStyleSheet("""
        PlanListView {
            background-color: rgb%s;
        }
        """ % str(Colors.CONTAINER_2.rgba))
        self.setIconSize(QtCore.QSize(50, 50))
        self.setSpacing(10)
        self.setUniformItemSizes(True)
        self.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        # ----- Data -----
        self.perm_type = perm_type
        self.remove_action = self._check_action_remove()
        self.context_menu = None
        # ----- Set data -----
        self.set_model_from_db()

    def set_model_from_db(self):
        if self.perm_type:
            user_perm = 1 if self.perm_type == PermissionType.User else 0
            filters = {'user_permission': user_perm}
        else:
            filters = None
        _week_plan = DB().select_week_plan_info(filters=filters)
        self.setModel(PlanListModel(_week_plan))

    def get_selected_plan_row(self):
        indexes = self.selectedIndexes()
        if not indexes:
            return False
        plan_row = self.model().rows[indexes[0].row()]
        return plan_row

    def load_to_planner(self, index):
        plan_row = self.model().rows[index.row()]
        self.signal_load_plan.emit(plan_row)

    def _delete_plan(self, row):
        """Deletes workout from DB and list"""
        model = self.model()
        plan_row = model.rows[row]
        deleted = DB().delete_week_plan(plan_row.plan_id)
        if not deleted:
            _msg = f'Plan {plan_row.name} couldn\'t be deleted.'
            ErrorMessage(f'Delete plan failed', _msg).exec()
            return
        _msg = f'Plan "{plan_row.name}" was deleted.'
        InfoMessage('Plan deleted', _msg).exec()
        model.removeRows(row, 1)
        if model.rowCount() == 0:
            self.signal_select_next_plan.emit()

    def _check_action_remove(self):
        if self.perm_type == PermissionType.System and APP_MODE == AppMode.PRODUCTION_MODE:
            return False
        return True

    # ----- SLOTS -----

    def doubleClicked(self, index):
        # Set just to cancel the action
        pass

    def selectionChanged(self, selected, deselected):
        plan_row = self.get_selected_plan_row()
        if not plan_row:
            return
        self.signal_plan_selected.emit(plan_row)

    def contextMenuEvent(self, event):
        indexes = self.selectedIndexes()
        if not indexes:
            return
        sel_row = indexes[0].row()
        model = self.model()
        plan_row = model.rows[sel_row]
        self.context_menu = QtWidgets.QMenu(self)
        action_load_to_planner = self.context_menu.addAction("Load into Planner")
        action_remove = None
        if self.remove_action:
            self.context_menu.addSeparator()
            action_remove = self.context_menu.addAction("Remove")
        action = self.context_menu.exec(self.mapToGlobal(event.pos()))
        if action == action_load_to_planner:
            self.signal_load_plan.emit(plan_row)
        if self.remove_action and action == action_remove:
            _msg = f'Are you sure you want to remove plan "{plan_row.name}" ?'
            remove = QuestionDialog('Remove plan', _msg).exec()
            if not remove:
                return  # Plan deletion is cancelled
            self._delete_plan(sel_row)
            if model.rowCount() > 0:
                next_sel_row = 0 if sel_row == 0 else sel_row - 1
                self.select_index(next_sel_row)
            else:
                self.signal_select_next_plan.emit()


class WorkoutListView(_ListViewBase):
    signal_workout_selected = QtCore.pyqtSignal(WorkoutListRow)
    signal_select_next_workout = QtCore.pyqtSignal()
    signal_load_workout = QtCore.pyqtSignal(str)

    def __init__(self, parent, perm_type=None):
        super().__init__(parent)
        self.setStyleSheet("""
        WorkoutListView {
            background-color: #E5FFCC;
        }
        """)
        # --- Props ---
        self.setIconSize(QtCore.QSize(50, 50))
        self.setSpacing(10)
        self.setUniformItemSizes(True)
        self.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.setResizeMode(QtWidgets.QListView.ResizeMode.Fixed)
        # ----- Data -----
        self.perm_type = perm_type
        self.remove_action = self._check_action_remove()
        # ----- Post init actions -----
        self.set_model_from_db()

    def get_selected_workout_row(self):
        indexes = self.selectedIndexes()
        if not indexes:
            return False
        workout_row = self.model().rows[indexes[0].row()]
        return workout_row

    def set_model_from_db(self):
        if self.perm_type:
            user_perm = 1 if self.perm_type == PermissionType.User else 0
            _workout_rows = DB().select_workout_info(filters={'user_permission': user_perm})
        else:
            _workout_rows = DB().select_workout_info()
        self.setModel(WorkoutListModel(_workout_rows))

    def load_to_planner(self, table_name):
        self.signal_load_workout.emit(table_name)

    def _delete_workout(self, row):
        """Deletes workout from DB and list"""
        model = self.model()
        workout_row = model.rows[row]
        deleted = DB().delete_workout(workout_row.workout_id)
        if not deleted:
            _msg = f'Couldn\'t delete workout "{workout_row.name}"'
            ErrorMessage(f'Workout wasn\'t deleted', _msg).exec()
            return
        model.removeRows(row, 1)

    def _check_action_remove(self):
        if self.perm_type == PermissionType.System and APP_MODE == AppMode.PRODUCTION_MODE:
            return False
        return True

    # ----- SLOTS -----

    def doubleClicked(self, index):
        # Set just to cancel the action
        pass

    def selectionChanged(self, selected, deselected):
        indexes = selected.indexes()
        if len(indexes) == 0:
            return
        index = indexes[0]
        workout_row = self.model().rows[index.row()]
        self.signal_workout_selected.emit(workout_row)

    def contextMenuEvent(self, event):
        indexes = self.selectedIndexes()
        if not indexes:
            return
        sel_row = indexes[0].row()
        model = self.model()
        workout_row = model.rows[sel_row]
        # Create context menu
        context_menu = QtWidgets.QMenu(self)
        menu_load = context_menu.addMenu('Load into Planner table:')
        table_actions = []
        for table in DAYS_TITLE:
            table_actions.append(menu_load.addAction(table))
        action_remove = None
        if self.remove_action:
            context_menu.addSeparator()
            action_remove = context_menu.addAction("Remove")
        # ----- Execute context menu -----
        action = context_menu.exec(self.mapToGlobal(event.pos()))
        if action in table_actions:
            self.load_to_planner(action.text().lower())
        if self.remove_action and action == action_remove:
            _question = f'Are you sure you want to remove workout "{workout_row.name}" ?'
            remove = QuestionDialog('Remove workout', _question).exec()
            if not remove:
                return  # Workout deletion is cancelled
            self._delete_workout(sel_row)
            if model.rowCount() > 0:
                next_sel_row = 0 if sel_row == 0 else sel_row - 1
                self.select_index(next_sel_row)
            else:
                self.signal_select_next_workout.emit()
