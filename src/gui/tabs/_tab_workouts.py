from functools import partial

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui

from database.db_obj import DB
from database.data_model import \
    WorkoutListModel, TableModel, ExerciseData, WorkoutListRow, WorkoutData, WorkoutPdfData
from gui.widgets import (
    ImageButton, ScrollArea, PlanListView, MyLabel, WorkoutListView, TitleLabel,
    WorkoutListView, HBoxPane, DBTitleLabel, CheckBox, DialogButtonBox, HLine
)
from gui.dialogs import QuestionDialog, InfoMessage
from gui.editors import WorkoutTableViewer, InfoRow, WorkoutTableViewer, \
    WorkoutTimeBox
from gui.dialogs import InfoMessage, BaseDialog, ErrorMessage, \
    raise_missing_exercises_error_msg
from gui.flags import (
    PermissionType, ImageFp, AlignFlag, Orientation, SizePolicy, MotType,
)
from config import DAYS_TITLE, AppMode, APP_MODE
from settings import Settings
from gui.font import Font, FontFlag
from gui.util import set_value, get_value
from gui.colors import Colors
from workout import get_available_generic_workout_name, filter_existing_exercise_row_data
from export.pdf import create_workout_pdf


class WorkoutPdfSettingsDialog(BaseDialog):
    def __init__(self):
        super().__init__('Create workout PDF settings', icon_fp=ImageFp.PLAN_PDF)
        # ----- GUI children -----
        # ----- 1st row -----
        self.checkbox_create_title = CheckBox(
            self, 'checkbox_title', text='Create title', checked=True,
            direction=QtCore.Qt.LayoutDirection.LeftToRight)
        self.hline1 = HLine(self)
        # ----- 2nd row -----
        self.checkbox_links = CheckBox(
            self, 'checkbox_links', text='Create YouTube video links',
            direction=QtCore.Qt.LayoutDirection.LeftToRight, checked=True)
        self.hline2 = HLine(self)
        # ----- 4th row -----
        self.button_box = DialogButtonBox(self, 'Create workout PDF', bttn_reject_text='Cancel')
        self.button_box.signal_accepted.connect(self.accept)
        self.button_box.signal_rejected.connect(self.reject)
        # ----- Set layout -----
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setVerticalSpacing(30)
        self.grid_layout.setSpacing(10)
        self.grid_layout.addWidget(self.checkbox_create_title, 0, 0)
        self.grid_layout.addWidget(self.hline1, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.checkbox_links, 2, 0)
        self.grid_layout.addWidget(self.hline2, 3, 0, 1, 2)
        self.grid_layout.addWidget(self.button_box, 4, 1)
        self.setLayout(self.grid_layout)

    def get_pdf_settings(self):
        pdf_settings = self.exec()
        if pdf_settings:
            pdf_settings = {
                'title': self.checkbox_create_title.isChecked(),
                'links': self.checkbox_links.isChecked()
            }
            return pdf_settings
        return False


class _WorkoutViewerToolbar(QtWidgets.QWidget):
    signal_load_workout = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        # ----- GUI children -----
        self.hbox_layout = None
        # self.bttn_load_to_planner = None
        self.bttn_export = None
        self.create_pdf = None
        self.bttn_delete = None
        # ----- Init UI -----
        self._init_ui()

    def _init_ui(self):
        self.bttn_export = ImageButton(self, 'bttn', ImageFp.EXPORT, 'Export to motfile')
        self.bttn_create_pdf = ImageButton(self, 'bttn', ImageFp.PLAN_PDF, 'Create workout pdf')
        self.bttn_delete = ImageButton(self, 'bttn_delete', ImageFp.DELETE, 'Delete workout')
        # ----- Set Layout -----
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.hbox_layout.addWidget(self.bttn_export)
        self.hbox_layout.addWidget(self.bttn_create_pdf)
        self.hbox_layout.addWidget(self.bttn_delete)
        self.setLayout(self.hbox_layout)


class _WorkoutViewerTopRow(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        # ----- GUI children -----
        self.vbox_layout = None
        self.workout_name = None
        self.toolbar = None
        self.workout_type = None
        # --- Initialize UI ---
        self._init_ui()

    def _init_ui(self):
        self.workout_name = TitleLabel(
            self, 'title_name', '-', bg_color=Colors.WORKOUT_TITLE.hex,
            font_flag=FontFlag.BIG_TEXT_BOLD)
        self.toolbar = _WorkoutViewerToolbar(self)
        _id_name_dict = dict(DB().select_from_table('plan_type', ('id', 'name')))
        self.workout_type = DBTitleLabel(
            self, 'title_type', _id_name_dict, font_flag=FontFlag.NORMAL_TEXT_BOLD,
            bg_color=Colors.PLAN_TYPE.hex, text_color='black',
            size_policy=(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM))
        self.workout_type.setToolTip('Workout type')
        toolbar_row = HBoxPane(self, (self.toolbar, None, self.workout_type),
                               align_flags=(AlignFlag.Left, AlignFlag.Right),
                               cont_margins=(0, 5, 0, 0))
        # ----- Set Layout -----
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(self.workout_name)
        self.vbox_layout.addWidget(toolbar_row)
        self.vbox_layout.setAlignment(self.workout_name, AlignFlag.Center)
        self.setLayout(self.vbox_layout)


class WorkoutViewer(QtWidgets.QFrame):
    signal_export_workout = QtCore.pyqtSignal(WorkoutData)

    def __init__(self, parent):
        super().__init__(parent)
        # ----- Props -----
        self.setFixedWidth(450)
        self.setStyleSheet("""
        WorkoutViewer {
            background-color: %s;
            border: 1px solid %s;
            border-radius: 5px;
        }
        """ % (Colors.CONTAINER.hex, Colors.CONTAINER.hex))
        # ----- Data -----
        self.loaded_workout_id = None
        # ----- GUI children -----
        self.vbox_layout = None
        self.workout_name = None
        self.top_row = None
        self.table = None
        self.workout_time = None
        # ----- Initialize UI -----
        self._init_ui()
        # ----- Connect events to slots -----
        self.top_row.toolbar.bttn_export.clicked.connect(self._export_workout_to_file)
        self.top_row.toolbar.bttn_create_pdf.clicked.connect(self._create_workout_pdf)

    def _init_ui(self):
        self.top_row = _WorkoutViewerTopRow(self)
        self.table = WorkoutTableViewer(self, 'table')
        self.workout_time = WorkoutTimeBox(self)
        # ----- Set Layout -----
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(self.top_row)
        self.vbox_layout.addWidget(self.table)
        self.vbox_layout.addWidget(self.workout_time)
        # self.vbox_layout.setContentsMargins(0, 10, 0, 10)
        self.setLayout(self.vbox_layout)

    def get_workout_data(self):
        table_rows = self.table.model().exer_exec_rows
        if not table_rows:
            return None
        workout_name = get_value(self.top_row.workout_name)
        workout_type_id = self.top_row.workout_type.get_item_db_id()
        rows_data = []
        for table_row in table_rows:
            rows_data.append(table_row.to_data())
        workout_data = WorkoutData(workout_name,
                                   workout_type_id,
                                   rows_data,
                                   self.workout_time.time_min)
        return workout_data

    def set_workout(self, workout_row=None):
        if workout_row:
            self.loaded_workout_id = workout_row.workout_id
            set_value(self.top_row.workout_name, workout_row.name)
            set_value(self.top_row.workout_type, workout_row.workout_type)
            _rows_data = DB().select_workout_rows_data(workout_row.workout_id)
            rows_data, missing_exercises = filter_existing_exercise_row_data(_rows_data)
            table_rows = [DB().get_table_row_obj_from_data(row_data) for row_data in rows_data]
            self.table.setModel(TableModel(table_rows))
            workout_time = DB().select_from_table('workout', 'workout_time',
                                                  filters={'id': workout_row.workout_id})
            set_value(self.workout_time, workout_time)
            if missing_exercises:
                raise_missing_exercises_error_msg(missing_exercises, MotType.WORKOUT)
            bttn_delete_enabled = True if workout_row.user_permission else False
            self.top_row.toolbar.bttn_delete.setEnabled(bttn_delete_enabled)
        else:
            self.loaded_workout_id = None
            set_value(self.top_row.workout_name, '-')
            set_value(self.top_row.workout_type, '-')
            self.table.setModel(TableModel([]))
            set_value(self.workout_time, 0)
            self.top_row.toolbar.bttn_delete.setEnabled(False)

    def _export_workout_to_file(self):
        workout_data = self.get_workout_data()
        self.signal_export_workout.emit(workout_data)

    def _create_workout_pdf(self):
        # ----- Get workout PDF data -----
        workout_name = get_value(self.top_row.workout_name)
        workout_type = get_value(self.top_row.workout_type)
        workout_type_icon_bytes = DB().select_from_table(
            'plan_type', 'icon', {'name': workout_type})
        workout_pdf_data = WorkoutPdfData(
            workout_name,
            workout_type,
            workout_type_icon_bytes,
            self.table.model().exer_exec_rows,
            self.workout_time.time_min
        )
        pdf_settings = WorkoutPdfSettingsDialog().get_pdf_settings()
        if pdf_settings:
            links = self.table.get_links()
            exported = create_workout_pdf(workout_pdf_data, pdf_settings, links)
            if exported:
                _pdf_folderpath = Settings().getValue('pdf_folderpath')
                _msg = f'Created workout "{workout_name}" PDF in directory:\n ' \
                       f'{_pdf_folderpath}'
                InfoMessage('Created workout PDF', _msg).exec()


class WorkoutListViewer(QtWidgets.QWidget):
    def __init__(self, parent, title, perm_type):
        super().__init__(parent)
        self.setFixedWidth(400)
        # ----- GUI children -----
        self.vbox_layout = None
        self.title = None
        self.workout_list = None
        # --- Initialize UI ---
        self._init_ui(title, perm_type)

    def _init_ui(self, title, perm_type):
        self.title = TitleLabel(self, 'title', title, round_bottom=False)
        self.workout_list = WorkoutListView(self, perm_type=perm_type)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.addWidget(self.title)
        self.vbox_layout.addWidget(self.workout_list)
        self.setLayout(self.vbox_layout)


class TabWorkouts(QtWidgets.QFrame):
    signal_load_workout_to_planner = QtCore.pyqtSignal(str, WorkoutListRow)

    def __init__(self, parent, index):
        super().__init__(parent)
        self.setObjectName('tab_workouts')
        self.setSizePolicy(SizePolicy.MINIMUM, SizePolicy.EXPANDING)
        # ----- Data -----
        self.index = index
        # ----- GUI children -----
        self.hbox_layout = None
        self.system_workout_list_viewer = None
        self.user_workout_list_viewer = None
        self.workout_viewer = None
        self.info_row = None
        # ----- Initialize UI -----
        self.init_ui()
        # ----- Connect events to slots -----
        self.system_workout_list_viewer.workout_list.signal_select_next_workout.\
            connect(self._select_next_workout_triggered)
        self.user_workout_list_viewer.workout_list.signal_select_next_workout.\
            connect(self._select_next_workout_triggered)
        self.system_workout_list_viewer.workout_list.signal_load_workout.\
            connect(self._load_to_planner)
        self.user_workout_list_viewer.workout_list.signal_load_workout.\
            connect(self._load_to_planner)
        self.system_workout_list_viewer.workout_list.signal_workout_selected.connect(
            partial(self._set_workout_data, PermissionType.System))
        self.user_workout_list_viewer.workout_list.signal_workout_selected.connect(
            partial(self._set_workout_data, PermissionType.User))
        self.workout_viewer.table.signal_execise_selected.connect(self._set_exercise_info)
        self.workout_viewer.top_row.toolbar.bttn_delete.clicked.connect(self._bttn_delete_clicked)
        # ----- Post init actions -----
        self._select_next_workout()

    def init_ui(self):
        self.system_workout_list_viewer = WorkoutListViewer(
            self, 'System workouts', PermissionType.System)
        self.user_workout_list_viewer = WorkoutListViewer(
            self, 'User workouts', PermissionType.User)
        self.workout_viewer = WorkoutViewer(self)
        _exercise_data = ExerciseData.get_empty_exercise_data()
        self.info_row = InfoRow(self, _exercise_data, orientation=Orientation.VERTICAL)
        # ----- Set Layout -----
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.addWidget(self.system_workout_list_viewer)
        self.hbox_layout.addWidget(self.user_workout_list_viewer)
        self.hbox_layout.addWidget(self.workout_viewer)
        self.hbox_layout.addWidget(self.info_row)
        self.hbox_layout.setAlignment(AlignFlag.Left)
        self.setLayout(self.hbox_layout)

    def refresh_workouts(self):
        self.system_workout_list_viewer.workout_list.set_model_from_db()
        self.user_workout_list_viewer.workout_list.set_model_from_db()

    def _select_next_workout(self):
        for workout_list in (self.user_workout_list_viewer.workout_list,
                             self.system_workout_list_viewer.workout_list):
            if workout_list.model().rowCount() > 0:
                workout_list.select_index(0)
                return
        # No workout available, so workout table data is reset
        self.workout_viewer.set_workout()

    # ----- SLOTS -----

    def _load_to_planner(self, table_name):
        for workout_list in (self.system_workout_list_viewer.workout_list,
                             self.user_workout_list_viewer.workout_list):
            workout_row = workout_list.get_selected_workout_row()
            if workout_row:
                self.signal_load_workout_to_planner.emit(table_name, workout_row)

    def _set_exercise_info(self, table_name, exer_id):
        exercise_data = DB().select_exercise_data(exer_id)
        self.info_row.set_data(exercise_data)

    def _set_workout_data(self, perm_type, workout_row):
        self.workout_viewer.set_workout(workout_row)
        if perm_type == PermissionType.System:
            self.user_workout_list_viewer.workout_list.selectionModel().clearSelection()
        else:  # == PermissionType.System
            self.system_workout_list_viewer.workout_list.selectionModel().clearSelection()

    def _bttn_delete_clicked(self):
        _workout_name = get_value(self.workout_viewer.top_row.workout_name)
        _msg = f'Are you sure you want to delete workout "{_workout_name}"?'
        delete_workout = QuestionDialog('Delete workout', _msg).exec()
        if not delete_workout:
            return
        deleted = DB().delete_workout(self.workout_viewer.loaded_workout_id)
        if not deleted:
            _msg = f'Error occured: Workout "{_workout_name}" couldn\'t be deleted.'
            ErrorMessage('Delete plan failed', _msg).exec()
            return
        _msg = f'Workout "{_workout_name}" was deleted.'
        InfoMessage('Workout deleted', _msg).exec()
        self.workout_viewer.set_workout()
        if APP_MODE == AppMode.DEVELOPMENT_MODE:
            indexes = self.system_workout_list_viewer.workout_list.selectedIndexes()
            if indexes:
                self.system_workout_list_viewer.model().removeRows(indexes[0].row(), 1)
                return
        indexes = self.user_workout_list_viewer.workout_list.selectedIndexes()
        if indexes:
            self.user_workout_list_viewer.workout_list.model().removeRows(indexes[0].row(), 1)
        self._select_next_workout()

    def _select_next_workout_triggered(self):
        self._select_next_workout()
