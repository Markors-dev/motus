from functools import partial

from PyQt5 import QtWidgets
from PyQt5 import QtCore

from config import APP_MODE, AppMode
from database.db_obj import DB
from database.data_model import PlanListRow, PlanData, PlanPdfData
from gui.editors import PlanAreaViewer
from gui.widgets import (
    ScrollArea, PlanListView, TitleLabel, HBoxPane, ImageButton,
    DBTitleLabel,
)
from gui.dialogs import ErrorMessage, QuestionDialog, InfoMessage
from gui.font import Font, FontFlag
from gui.colors import Colors
from gui.util import set_value, get_value
from gui.flags import ImageFp, AlignFlag, PermissionType, SizePolicy


db = DB()


class _PlanViewerToolbar(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        # style_sheet = """
        #     border: 0;
        # """
        # self.setStyleSheet(style_sheet)
        # self.setFixedHeight(50)
        self.hbox_layout = None
        self.bttn_load = None
        self.bttn_export = None
        self.bttn_create_pdf = None
        self.bttn_delete = None
        # ----- Init UI -----
        self.init_ui()
        # ----- Connect events to slots -----
        # self.bttn_load.clicked.connect(self._load_plan_to_planner)

    def init_ui(self):
        self.bttn_load = ImageButton(self, 'bttn_load', ImageFp.LOAD, 'Load plan to Planner')
        self.bttn_export = ImageButton(self, 'bttn_export', ImageFp.EXPORT, 'Export plan to motfile')
        self.bttn_create_pdf = ImageButton(self, 'bttn_create_pdf', ImageFp.PLAN_PDF, 'Create plan pdf')
        self.bttn_delete = ImageButton(self, 'bttn_delete', ImageFp.DELETE, 'Delete plan')
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.hbox_layout.addWidget(self.bttn_load)
        self.hbox_layout.addWidget(self.bttn_export)
        self.hbox_layout.addWidget(self.bttn_create_pdf)
        self.hbox_layout.addWidget(self.bttn_delete)
        self.hbox_layout.setAlignment(AlignFlag.Left)
        self.setLayout(self.hbox_layout)


class _PlanViewerTopRow(QtWidgets.QFrame):
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
        self.toolbar = _PlanViewerToolbar(self)
        self.title = TitleLabel(
            self, 'plan_name', '-', font_flag=FontFlag.TITLE_BOLD,
            bg_color=Colors.PLAN_TITLE.hex,
            size_policy=(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM))
        _id_name_dict = dict(DB().select_from_table('plan_type', ('id', 'name')))
        self.label_plan_type = DBTitleLabel(
            self, 'plan_type', _id_name_dict, font_flag=FontFlag.NORMAL_TEXT_BOLD,
            bg_color=Colors.PLAN_TYPE.hex, text_color='black',
            size_policy=(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM))
        self.label_plan_type.setToolTip('Plan type')
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.hbox_layout.addWidget(self.toolbar)
        self.hbox_layout.addStretch(10)
        self.hbox_layout.addWidget(self.title)
        self.hbox_layout.addStretch(10)
        self.hbox_layout.addWidget(self.label_plan_type)
        self.hbox_layout.addStretch(1)
        self.hbox_layout.setAlignment(self.title, AlignFlag.Center)
        self.hbox_layout.setAlignment(self.title, AlignFlag.Right)
        self.setLayout(self.hbox_layout)


class PlanViewer(QtWidgets.QWidget):
    signal_create_plan_pdf = QtCore.pyqtSignal(QtWidgets.QWidget, PlanPdfData)
    signal_export_plan = QtCore.pyqtSignal(PlanData)

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('plan_viewer')
        # Data
        self.loaded_plan_id = None
        # ----- GUI children -----
        self.vbox_layout = None
        self.top_row = None
        self.plan_area_viewer = None
        # ----- Init UI -----
        self._init_ui()
        # ----- Connect events to slots -----
        self.top_row.toolbar.bttn_export.clicked.connect(self._export_to_json_file)
        self.top_row.toolbar.bttn_create_pdf.clicked.connect(self._create_plan_pdf)

    def _init_ui(self):
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.top_row = _PlanViewerTopRow(self)
        self.plan_area_viewer = PlanAreaViewer(self)
        self.scroll_area = ScrollArea(self)
        self.scroll_area.setWidget(self.plan_area_viewer)
        # ----- Set Layout -----
        self.vbox_layout.addWidget(self.top_row)
        self.vbox_layout.addWidget(self.scroll_area)
        self.setLayout(self.vbox_layout)

    def set_plan(self, plan_row=None):
        if plan_row:
            self.loaded_plan_id = plan_row.plan_id
            set_value(self.top_row.title, plan_row.name)
            set_value(self.top_row.label_plan_type, plan_row.plan_type)
            workouts_data = db.select_plan_workouts_data(plan_row.plan_id)
            self.plan_area_viewer.set_plan_workouts(workouts_data)
            bttn_delete_enabled = True if plan_row.user_permission else False
            self.top_row.toolbar.bttn_delete.setEnabled(bttn_delete_enabled)
        else:
            self.loaded_plan_id = None
            set_value(self.top_row.title, '-')
            set_value(self.top_row.label_plan_type, '-')
            self.plan_area_viewer.set_plan_workouts([None] * 7)
            self.top_row.toolbar.bttn_delete.setEnabled(False)

    def _export_to_json_file(self):
        plan_data = self._get_plan_data()
        self.signal_export_plan.emit(self, plan_data)

    def _create_plan_pdf(self):
        plan_pdf_data = self._get_plan_pdf_data()
        self.signal_create_plan_pdf.emit(self, plan_pdf_data)

    def _get_plan_data(self):
        plan_name = get_value(self.top_row.title)
        plan_type_id = self.top_row.label_plan_type.get_item_db_id()
        workouts_data = self.plan_area_viewer.get_workouts_data()
        return PlanData(self.loaded_plan_id, plan_name, plan_type_id, workouts_data)

    def _get_plan_pdf_data(self):
        plan_name = get_value(self.top_row.title)
        plan_type = get_value(self.top_row.label_plan_type)
        workouts_pdf_data = self.plan_area_viewer.get_workouts_pdf_data()
        links = self.plan_area_viewer.get_all_links()
        return PlanPdfData(plan_name, plan_type, workouts_pdf_data, links)


class PlanListViewer(QtWidgets.QFrame):
    def __init__(self, parent, title, perm_type):
        super().__init__(parent)
        self.setFixedHeight(350)
        # GUI children
        self.vbox_layout = None
        self.title = None
        self.plan_list = None
        # Initilize GUI
        self.init_ui(title, perm_type)

    def init_ui(self, title, perm_type):
        self.title = TitleLabel(self, 'title', title,
                                font_flag=FontFlag.BIG_TEXT_BOLD, round_bottom=False)
        self.plan_list = PlanListView(self, perm_type=perm_type)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.addWidget(self.title)
        self.vbox_layout.addWidget(self.plan_list)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbox_layout)

    def refresh_from_db(self):
        indexes = self.plan_list.selectedIndexes()
        sel_row = indexes[0].row() if indexes else None
        self.plan_list.set_model_from_db()
        if sel_row is not None:
            self.plan_list.select_index(sel_row)

    def _get_plan_pdf_data(self):
        pass


class TabPlans(QtWidgets.QWidget):
    signal_load_plan = QtCore.pyqtSignal(PlanListRow)
    signal_plan_deleted = QtCore.pyqtSignal(int)

    def __init__(self, parent, index):
        super().__init__(parent)
        self.index = index
        self.setObjectName('tab_plans')
        # ----- Data -----
        self.info_dialog = None  # For testing
        self.question_dialog = None  # For testing
        # ----- GUI chlderen -----
        self.vbox_layout = None
        self.system_plan_list_viewer = None
        self.user_plan_list_viewer = None
        self.plan_viewer = None
        # ----- Init UI -----
        self.init_ui()
        # ----- GUI chlderen -----
        # connect event to slots
        self.system_plan_list_viewer.plan_list.signal_select_next_plan.connect(self._select_next_plan)
        self.user_plan_list_viewer.plan_list.signal_select_next_plan.connect(self._select_next_plan)
        self.system_plan_list_viewer.plan_list.signal_plan_selected.connect(
            partial(self._set_plan_data, PermissionType.System))
        self.user_plan_list_viewer.plan_list.signal_plan_selected.connect(
            partial(self._set_plan_data, PermissionType.User))
        self.plan_viewer.top_row.toolbar.bttn_load.clicked.connect(self._bttn_load_clicked)
        self.plan_viewer.top_row.toolbar.bttn_delete.clicked.connect(self._bttn_delete_clicked)
        # Post actions
        self._select_next_plan()

    def init_ui(self):
        self.system_plan_list_viewer = PlanListViewer(self, 'System Plans', PermissionType.System)
        self.user_plan_list_viewer = PlanListViewer(self, 'User Plans', PermissionType.User)
        _row_plan_lists = HBoxPane(self, (self.system_plan_list_viewer, self.user_plan_list_viewer),
                                   cont_margins=(0, 0, 0, 0))
        self.plan_viewer = PlanViewer(self)
        # ----- Set Layout -----
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(self.plan_viewer)
        self.vbox_layout.addWidget(_row_plan_lists)
        self.vbox_layout.setAlignment(_row_plan_lists, AlignFlag.Top)
        self.setLayout(self.vbox_layout)

    def refresh_plans(self):
        self.system_plan_list_viewer.refresh_from_db()
        self.user_plan_list_viewer.refresh_from_db()

    def _select_next_plan(self):
        for plan_list in (self.user_plan_list_viewer.plan_list,
                          self.system_plan_list_viewer.plan_list):
            if plan_list.model().rowCount() > 0:
                plan_list.select_index(0)
                return
        # Not plan available, so plan table data is reset
        self.plan_viewer.set_plan()

    # ----- SLOTS -----

    def _bttn_load_clicked(self):
        system_plan_list = self.system_plan_list_viewer.plan_list
        user_plan_list = self.user_plan_list_viewer.plan_list
        plan_row = system_plan_list.get_selected_plan_row()
        if not plan_row:
            plan_row = user_plan_list.get_selected_plan_row()
        self.signal_load_plan.emit(plan_row)

    def _bttn_delete_clicked(self):
        loaded_plan_id = self.plan_viewer.loaded_plan_id
        if not loaded_plan_id:
            ErrorMessage('Delete plan failed', 'No plan is loaded').exec()
            return
        _plan_name = get_value(self.plan_viewer.top_row.title)
        _msg = f'Are you sure you want to delete plan "{_plan_name}"?'
        self.question_dialog = QuestionDialog('Delete plan', _msg)
        delete_plan = self.question_dialog.exec()
        if not delete_plan:
            return
        deleted = DB().delete_week_plan(loaded_plan_id)
        if not deleted:
            _msg = f'Error occured: Plan "{_plan_name}" couldn\'t be deleted.'
            ErrorMessage('Delete plan failed', _msg).exec()
            return
        self.plan_viewer.set_plan()
        if APP_MODE == AppMode.DEVELOPMENT_MODE:
            indexes = self.system_plan_list_viewer.plan_list.selectedIndexes()
            if indexes:
                plan_id = self.system_plan_list_viewer.get_selected_item_id()
                self.system_plan_list_viewer.model().removeRows(indexes[0].row(), 1)
                self.signal_plan_deleted.emit(plan_id)
                return
        indexes = self.user_plan_list_viewer.plan_list.selectedIndexes()
        if indexes:
            plan_id = self.user_plan_list_viewer.plan_list.get_selected_item_id()
            self.user_plan_list_viewer.plan_list.model().removeRows(indexes[0].row(), 1)
            self.signal_plan_deleted.emit(plan_id)
        self._select_next_plan()
        _msg = f'Plan "{_plan_name}" was deleted.'
        self.info_dialog = InfoMessage('Plan deleted', _msg)
        self.info_dialog.exec()
        self.info_dialog = None

    def _set_plan_data(self, perm_type, plan_row):
        self.plan_viewer.set_plan(plan_row)
        if perm_type == PermissionType.System:
            self.user_plan_list_viewer.plan_list.selectionModel().clearSelection()
        else:  # == PermissionType.User
            self.system_plan_list_viewer.plan_list.selectionModel().clearSelection()
