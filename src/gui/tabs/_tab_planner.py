import time

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui

from gui.editors import PlanAreaEditor, ExerciseListViewer, ExerciseBasicInfoViewer
from gui.dialogs import ErrorMessage, InfoMessage, QuestionDialog, get_filepath_from_dialog
from gui.util import get_parent, set_value, get_value, find_widget_by_attr
from gui.font import Font, FontFlag
from gui.widgets import (
    ImageButton, ScrollArea, PlanListView, MyLabel, LineEdit, MyComboBox,
    ResizePane, ValidatedLineEdit, DBComboBox, VLine, CheckBox,
    HLine, RadiobuttonBox, HBoxPane, LoadListItemDialog
)
from gui.colors import Colors
from gui.flags import ImageFp, LayoutOrientation, AlignFlag, SizePolicy
from database.db_obj import DB
from database.data_model import PlanData, ExerciseData, PlanPdfData
from config import DAYS, AppMode, APP_MODE, PLAN_FILE_EXTENSION
from settings import Settings
from session import Session
from export.motfile import import_plan
from export.pdf import create_plan_pdf
from workout import (
    get_available_generic_plan_name, plan_name_valid, PLAN_NAME_CHECK_ERROR_MSG,
)

# Global Vars
db = DB()


class _PlanEditorToolbar(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        # style_sheet = """
        #     border: 0;
        # """
        # self.setStyleSheet(style_sheet)
        # self.setFixedHeight(50)
        self.hbox_layout = None
        self.bttn_new = None
        self.bttn_save = None
        self.bttn_save_as = None
        self.bttn_load = None
        self.bttn_import = None
        self.bttn_export = None
        self.vline = None
        self.bttn_create_pdf = None
        self.init_ui()

    def init_ui(self):
        self.bttn_new = ImageButton(self, 'bttn_new', ImageFp.NEW, 'New plan')
        self.bttn_save = ImageButton(self, 'bttn_save', ImageFp.SAVE, 'Save plan', enabled=False)
        self.bttn_save_as = ImageButton(self, 'bttn_save_as', ImageFp.SAVE_AS, 'Save as new plan')
        self.bttn_load = ImageButton(self, 'bttn_load', ImageFp.LOAD, 'Load plan')
        self.bttn_import = ImageButton(self, 'bttn_import', ImageFp.IMPORT, 'Import plan from motfile')
        self.bttn_export = ImageButton(self, 'bttn_export', ImageFp.EXPORT, 'Export plan to motfile')
        self.vline = VLine(self, size=(2, 30))
        self.bttn_create_pdf = ImageButton(self, 'bttn_create_pdf', ImageFp.PLAN_PDF, 'Create plan pdf')

        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.addWidget(self.bttn_new)
        self.hbox_layout.addWidget(self.bttn_save)
        self.hbox_layout.addWidget(self.bttn_save_as)
        self.hbox_layout.addWidget(self.bttn_load)
        self.hbox_layout.addWidget(self.bttn_import)
        self.hbox_layout.addWidget(self.bttn_export)
        self.hbox_layout.addWidget(self.vline)
        self.hbox_layout.addWidget(self.bttn_create_pdf)
        self.hbox_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setLayout(self.hbox_layout)


class _PlanEditorTopRow(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        # GUI children
        self.hbox_layout = None
        self.toolbar = None
        self.title = None
        self.label_plan_type = None
        self.cb_plan_type = None
        # Initialize UI
        self._init_ui()

    def _init_ui(self):
        self.toolbar = _PlanEditorToolbar(self)
        plan_name = get_available_generic_plan_name()
        self.title = ValidatedLineEdit(
            self, 'plan_name', plan_name, plan_name_valid,
            PLAN_NAME_CHECK_ERROR_MSG, bg_color=Colors.PLAN_TITLE.hex,
            text_color='white', border_radius=6, font_flag=FontFlag.BIG_TITLE,
            align_flag=AlignFlag.Center)
        self.label_plan_type = MyLabel(self, 'label_cb_plan_type', 'Plan type ', FontFlag.SMALL_TEXT_BOLD,
                                       size_policy=(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM))
        _id_name_dict = dict(DB().select_from_table('plan_type', ('id', 'name')))
        self.cb_plan_type = DBComboBox(
            self, 'cb', _id_name_dict, first_item='-', font_flag=FontFlag.NORMAL_TEXT)
        plan_type_widget = HBoxPane(self, (self.label_plan_type, self.cb_plan_type),
                                    align_flags=(AlignFlag.Right, AlignFlag.Right))
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(5, 0, 0, 0)
        self.hbox_layout.addWidget(self.toolbar)
        self.hbox_layout.addStretch()
        self.hbox_layout.addWidget(self.title)
        self.hbox_layout.addStretch()
        # self.hbox_layout.addWidget(self.label_plan_type)
        # self.hbox_layout.addWidget(self.cb_plan_type)
        self.hbox_layout.addWidget(plan_type_widget)
        self.setLayout(self.hbox_layout)

    def reset_values(self):
        self.title.set_text(get_available_generic_plan_name())
        set_value(self.cb_plan_type, '-')


class PlanEditor(QtWidgets.QWidget):
    """
    Plan editor actions:
        - add row
        - delete row(s)
        - copy row(s)
        - move row(s)

    """
    signal_plans_changed = QtCore.pyqtSignal()
    signal_create_plan_pdf = QtCore.pyqtSignal(QtWidgets.QWidget, PlanPdfData)
    signal_export_plan = QtCore.pyqtSignal(QtWidgets.QWidget, PlanData)

    def __init__(self, parent, plan_id=None):
        super().__init__(parent)
        self.setObjectName('plan_editor')
        # Data
        self.unsaved_changes = False
        self.loaded_plan_id = plan_id if plan_id else None
        self.info_dialog = None  # for testing
        self.file_dialog = None  # for testing
        self.pdf_settings_dialog = None  # for testing
        # GUI children
        self.vbox_layout = None
        self.top_row = None
        self.plan_area = None
        self._init_ui()
        # Post init actions
        if plan_id:
            plan_name, plan_type_id = db.select_from_table('week_plan', ('name', 'plan_type_id'),
                                                           {'id': plan_id})
            workouts_data = db.select_plan_workouts_data(plan_id)
            self.set_plan(PlanData(plan_id, plan_name, plan_type_id, workouts_data))
            self.unsaved_changes = False
            self.loaded_plan_id = plan_id
            self.top_row.toolbar.bttn_save.setEnabled(False)
        # Connect evets to slots
        self.top_row.toolbar.bttn_new.clicked.connect(self._bttn_new_clicked)
        self.top_row.toolbar.bttn_save.clicked.connect(self._bttn_save_clicked)
        self.top_row.toolbar.bttn_save_as.clicked.connect(self._bttn_save_as_clicked)
        self.top_row.toolbar.bttn_load.clicked.connect(self._bttn_load_clicked)
        self.top_row.toolbar.bttn_export.clicked.connect(self._export_plan)
        self.top_row.toolbar.bttn_import.clicked.connect(self._import_plan)
        self.top_row.toolbar.bttn_create_pdf.clicked.connect(self._create_plan_pdf)
        self.top_row.title.line_edit.textEdited.connect(self._plan_changed)
        self.top_row.cb_plan_type.currentIndexChanged.connect(self._plan_changed)
        for workout_area in self.plan_area.workout_areas:
            workout_area.workout_info_row.workout_name.line_edit.textEdited.connect(self._plan_changed)
            workout_area.workout_info_row.workout_type.currentIndexChanged.connect(self._plan_changed)
            workout_area.table.signal_table_changed.connect(self._plan_changed)
            workout_area.table.item_delegate.signal_table_data_changed.connect(self._plan_changed)

    def _init_ui(self):
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.top_row = _PlanEditorTopRow(self)
        self.scroll_area = ScrollArea(self)
        self.plan_area = PlanAreaEditor(self)
        self.scroll_area.setWidget(self.plan_area)
        self.vbox_layout.addWidget(self.top_row)
        self.vbox_layout.addWidget(self.scroll_area)
        self.setLayout(self.vbox_layout)

    def set_plan(self, plan_data):
        self.top_row.title.set_text(plan_data.name)
        self.top_row.cb_plan_type.set_text_by_id(plan_data.type_id)
        self.plan_area.set_plan_workouts(plan_data.workouts_data)

    def add_table_row(self, exer_id, table_name=None):
        exercise_data = db.select_exercise_data(exer_id)
        self.plan_area.add_table_row(exercise_data, table_name=table_name)
        self.scroll_to_sel_table()

    def save_plan(self):
        plan_data = self._get_plan_data()
        updated = db.update_week_plan(plan_data)
        if not updated:
            _msg = f'Error occured. Plan "{plan_data.name}" wasnt saved.'
            ErrorMessage('Save plan error', _msg).exec()
            return
        InfoMessage(f'Plan saved', f'Plan "{plan_data.name}" saved in App').exec()
        self.unsaved_changes = False
        self.top_row.toolbar.bttn_save.setEnabled(False)
        self.signal_plans_changed.emit()

    def save_plan_as(self):
        plan_data = self._get_plan_data()
        user_permission = True
        if APP_MODE == AppMode.DEVELOPMENT_MODE:
            _msg = 'Save this plan as User plan?\n' \
                   'NOTE: Click "No" to save plan as System plan.'
            user_permission = QuestionDialog('Plan permission type(Development mode)',
                                             _msg).exec()
        inserted = db.insert_into_week_plan(plan_data, user_permission)
        if not inserted:
            ErrorMessage('Save new plan error', f'Error occured. Plan "{plan_data.name}" wasnt saved.').exec()
            return
        self.info_dialog = InfoMessage('New plan saved', f'New plan "{plan_data.name}" saved in App')
        self.info_dialog.exec()
        self.unsaved_changes = False
        self.loaded_plan_id = db.select_from_table('week_plan', 'id', {'name': plan_data.name})
        self.top_row.toolbar.bttn_save.setEnabled(False)
        self.signal_plans_changed.emit()
        self.info_dialog = None

    def load_plan(self, plan_row):
        self.check_for_changes_and_save()
        workouts_data = db.select_plan_workouts_data(plan_row.plan_id)
        plan_data = PlanData(plan_row.plan_id, plan_row.name, plan_row.plan_type_id,
                             workouts_data)
        self.set_plan(plan_data)
        # Reset object data
        self.unsaved_changes = False
        self.loaded_plan_id = plan_row.plan_id
        self.top_row.toolbar.bttn_save.setEnabled(False)

    def load_workout_to_table(self, table_name, workout_data):
        workout_area = find_widget_by_attr(self.plan_area.workout_areas, 'name', table_name)
        workout_area.load_workout(workout_data)

    def _create_plan_pdf(self):
        if not self._plan_data_set('Create plan pdf'):
            return  # abort - all plan data is not set
        plan_pdf_data = self._get_plan_pdf_data()
        self.signal_create_plan_pdf.emit(self, plan_pdf_data)

    def _export_plan(self):
        if not self._plan_data_set('Export plan'):
            return  # abort - all plan data is not set
        plan_data = self._get_plan_data()
        self.signal_export_plan.emit(self, plan_data)

    def _import_plan(self):
        _start_dir = Settings().getValue('motfiles_folderpath')
        plan_fp = get_filepath_from_dialog(
            self, 'Choose plan file from PC', start_dir=_start_dir,
            file_types=f'Plan files (*.{PLAN_FILE_EXTENSION})')
        if not plan_fp:
            return
        plan_data = import_plan(plan_fp)
        if not plan_data:
            return
        self.set_plan(plan_data)
        self.unsaved_changes = False
        self.loaded_plan_id = None
        self.top_row.toolbar.bttn_save.setEnabled(False)

    def scroll_to_sel_table(self):
        day_index = DAYS.index(self.plan_area.selected_table.name)
        if day_index in (0, 1):
            scroll_x_prop = 0.0
        elif day_index in (5, 6):
            scroll_x_prop = 1.0
        else:
            scroll_x_prop = day_index / 5
        hbar = self.scroll_area.horizontalScrollBar()
        hbar.setValue(int(hbar.maximum() * scroll_x_prop))

    def scroll_y(self, y):
        hbar = self.scroll_area.horizontalScrollBar()
        hbar.setValue(hbar.value() + y)

    def check_for_changes_and_save(self):
        if self.unsaved_changes:
            plan_name = get_value(self.top_row.title)
            if self.loaded_plan_id:
                _msg = f'Loaded plan "{plan_name}" was edited. Do you want to save it?'
                save_changes_dialog = QuestionDialog('Unsaved changes in plan', _msg).exec()
                if save_changes_dialog and self._plan_data_set('Save plan', check_plan_in_db=False):
                    self.save_plan()
                save_changes_dialog = None
            else:
                _msg = f'New plan "{plan_name}" is not saved. Do you want to save it?'
                save_changes_dialog = QuestionDialog(f'New plan "{plan_name}" not saved', _msg).exec()
                if save_changes_dialog and self._plan_data_set('Save new plan', check_plan_in_db=True):
                    self.save_plan_as()
                save_changes_dialog = None

    def _plan_data_set(self, action_name, check_plan_in_db=False):
        """Checks if all data is set: plan name, plan type and any exercise"""
        error_dialog_title = f'{action_name} failed'
        if self.top_row.cb_plan_type.currentText() == '-':
            ErrorMessage(error_dialog_title, 'Plan type is not set ').exec()
            return False
        if not self.top_row.title.valid:
            ErrorMessage(error_dialog_title, 'Plan name is not valid').exec()
            return False
        if not self.plan_area.workout_data_set(action_name):
            return False
        if check_plan_in_db:
            plan_name = self.top_row.title.line_edit.text()
            saved_plan_id = db.select_from_table('week_plan', 'id', {'name': plan_name}, get_none=True)
            if saved_plan_id:
                _msg = f'Plan with name "{plan_name}" already exists!\n ' \
                       f'Rename plan name if you want to save it as a new project.'
                ErrorMessage(error_dialog_title, _msg).exec()
                return False
        return True

    def _get_plan_data(self):
        plan_type_id = self.top_row.cb_plan_type.get_item_db_id()
        plan_name = self.top_row.title.line_edit.text()
        workouts_data = self.plan_area.get_workouts_data()
        return PlanData(self.loaded_plan_id, plan_name, plan_type_id, workouts_data)

    def _get_plan_pdf_data(self):
        plan_name = self.top_row.title.line_edit.text()
        plan_type = self.top_row.cb_plan_type.currentText()
        workouts_pdf_data = self.plan_area.get_workouts_pdf_data()
        links = self.plan_area.get_all_links()
        return PlanPdfData(plan_name, plan_type, workouts_pdf_data, links)

    # SLOTS

    def _plan_changed(self):
        self.unsaved_changes = True
        if self.loaded_plan_id:
            self.top_row.toolbar.bttn_save.setEnabled(True)

    def _bttn_new_clicked(self):
        self.check_for_changes_and_save()
        # Reseting plan editor data
        self.top_row.reset_values()
        self.plan_area.set_plan_workouts([None] * 7)
        # Reset object data
        self.unsaved_changes = False
        self.loaded_plan_id = None
        self.top_row.toolbar.bttn_save.setEnabled(False)

    def _bttn_save_clicked(self):
        if not self._plan_data_set('Save plan', check_plan_in_db=False):
            return
        self.save_plan()

    def _bttn_save_as_clicked(self):
        if not self._plan_data_set('Save new plan', check_plan_in_db=True):
            return
        self.save_plan_as()

    def _bttn_load_clicked(self):
        dialog = LoadListItemDialog('Load plan', PlanListView)
        plan_row = dialog.get_list_item()
        if plan_row:
            self.load_plan(plan_row)


class RightPane(QtWidgets.QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('right_pane')
        # GUI children
        self.vbox_layout = None
        self.plan_editor = None
        self.exer_info_viewer = None
        # Initialize GUI
        self.init_ui()
        # connect events to slots
        for table in self.plan_editor.plan_area.tables:
            table.signal_execise_selected.connect(self._row_selected)

    def init_ui(self):
        plan_id = None
        _last_loaded_plan_id = Session().get_value('last_loaded_plan')
        if Settings().getValue('reload_plan') and _last_loaded_plan_id:
            plan_id = _last_loaded_plan_id
        self.plan_editor = PlanEditor(self, plan_id=plan_id)
        # resize_pane = ResizePane(self)
        self.exer_info_viewer = ExerciseBasicInfoViewer(self)
        resize_pane = ResizePane(self, self.exer_info_viewer, title='Basic exercise info')
        # resize_pane.set_widget(self.exer_info_viewer)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(self.plan_editor)
        self.vbox_layout.addWidget(resize_pane)
        self.setLayout(self.vbox_layout)

    def show_exer_info(self, exer_id):
        raise NotImplemented('Implement this methos!')

    # SLOTS #

    def _row_selected(self, table_obj_name, exer_id):
        self.plan_editor.plan_area.set_selected_table(table_obj_name)
        self.exer_info_viewer.set_data(exer_id)


class TabPlanner(QtWidgets.QWidget):
    def __init__(self, parent, index):
        super().__init__(parent)
        self.setObjectName('tab_planner')
        self.index = index
        # ----- GUI children -----
        self.exercise_list_viewer = None
        self.right = None
        self.hbox_layout = None
        # ----- Initialize UI -----
        self.init_ui()
        # ----- Connect events to slots -----
        self.exercise_list_viewer.exercises_box.list_exercises.signal_add_exercise_to_table.connect(self._add_exercise)
        self.exercise_list_viewer.exercises_box.list_exercises.signal_exercise_changed.connect(self._show_exercise_info)
        # ----- Post init actions -----
        self.exercise_list_viewer.exercises_box.list_exercises.select_index(0)

    def init_ui(self):
        self.exercise_list_viewer = ExerciseListViewer(self)
        self.right = RightPane(self)
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.addWidget(self.exercise_list_viewer)
        self.hbox_layout.addWidget(self.right)
        self.hbox_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.setLayout(self.hbox_layout)

    def _add_exercise(self, exer_id, table_name=None):
        """ Adds exercise execution row to the selected table.

        :param exer_id: <int> Exercise id
        :param table_name: <str>
        :return: None
        """
        self.right.plan_editor.add_table_row(exer_id, table_name=table_name)

    def _show_exercise_info(self, exer_id):
        self.right.exer_info_viewer.set_data(exer_id)
