import pickle
from pathlib import Path
from enum import Enum
from functools import partial

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from gui.widgets import (
    RoundPushButton, VLine, BookmarkButton, ScrollArea, MyLabel,
    HBoxPane, LineEdit, ImageButton, ValidatedLineEdit,
    ImageWithText, RadiobuttonBox, DialogButtonBox, CropImageDialog,
    ChoiceDialog,
)
from gui.editors_NEW import TextBrowserEditor, InputImageWithText
from gui.editors import ExerciseListViewer, ExerciseDataViewer, InfoGrid
from gui.dialogs import BaseDialog, ErrorMessage, InfoMessage, QuestionDialog
from gui.font import Font, FontFlag
from gui.colors import Colors
from gui.flags import ImageFp, AlignFlag, SizePolicy, Orientation, PermissionType
from gui.util import get_value, set_value, find_widget_by_attr
from database.db_obj import DB
from database.data_model import ExerciseData, NewExerciseData
from util import images
from config import APP_MODE, AppMode, DAYS, BOOKMARKS_FILE
from settings import ICON_SIZES
from workout import exercise_name_valid, EXERCISE_NAME_CHECK_ERROR_MSG, \
    get_available_generic_exer_name

db = DB()


class NewExerciseDialog(BaseDialog):
    def __init__(self):
        super().__init__('Create new Exercise', ImageFp.EXERCISE)
        self.setMinimumWidth(1500)
        self.setMaximumWidth(1900)
        self.setMinimumHeight(800)
        self.setMaximumHeight(1000)
        # ----- Data -----
        self.new_exer_id = None
        self.new_exer_name = None
        # ----- GUI children -----
        self.vbox_layout = None
        self.rb_box_exer_permission = None
        self.edit_name = None
        self.info_grid = None
        self.image_pos1 = None
        self.image_pos2 = None
        self.browser_editor = None
        self.diagram_main_muscle = None
        self.diagram_minor_muscle = None
        self.button_box = None
        # ----- Init UI -----
        self._init_ui()
        # ----- Post init actions -----
        self.info_grid.setFocus()
        # Connect events to slots
        self.info_grid.label_main_muscles_value.edit_widget.currentTextChanged.connect(
            partial(self._muscle_group_changed, True))
        self.info_grid.label_minor_muscles_value.edit_widget.currentTextChanged.connect(
            partial(self._muscle_group_changed, False))
        self.image_pos1.signal_image_set.connect(self._pos1_image_set)

    def _init_ui(self):
        # ----- Title row -----
        _type_visible = True if APP_MODE == AppMode.DEVELOPMENT_MODE else False
        self.type_label = MyLabel(self, 'label', 'Exercise Permission type: ',
                                  visible=_type_visible)
        _rb_data = ((0, 'System'),
                    (1, 'User'))
        _checked_rb_index = 0 if APP_MODE == AppMode.DEVELOPMENT_MODE else 1
        self.rb_box_exer_permission = RadiobuttonBox(
            self, 'rb_box', _rb_data, visible=_type_visible, checked_rb_index=_checked_rb_index,
            orientation=Orientation.HORIZONTAL)
        _exer_name = get_available_generic_exer_name()
        self.edit_name = ValidatedLineEdit(
            self, 'exer_name', _exer_name, exercise_name_valid,
            EXERCISE_NAME_CHECK_ERROR_MSG, bg_color=Colors.EXERCISE_TITLE.hex,
            text_color='white', border_radius=10, place_holder_text='Input exercise name...',
            retain_msg_size=False, font_flag=FontFlag.BIG_TITLE_BOLD)
        title_row = HBoxPane(self, (self.type_label, self.rb_box_exer_permission, None, self.edit_name, None),
                             align_flags=(AlignFlag.Left, AlignFlag.Left, AlignFlag.Center),
                             cont_margins=(10, 10, 10, 10))
        # ----- Basic Exercise info row -----
        self.info_grid = InfoGrid(self, ExerciseData.get_empty_exercise_data())
        for edit_widget in self.info_grid.edit_widgets:
            edit_widget.activate_edit_mode()
        self.image_pos1 = InputImageWithText(self, 'image_pos1', 'Position 1', min_height=images.MIN_IMAGE_HEIGHT)
        self.image_pos2 = InputImageWithText(self, 'image_pos2', 'Position 2', enabled=False,
                                             min_height=images.MIN_IMAGE_HEIGHT, create_bttn_delete=True)
        info_row = HBoxPane(self,
                            (self.info_grid, self.image_pos1, self.image_pos2),
                            cont_margins=(5, 5, 5, 5))
        info_row.setStyleSheet("""
            HBoxPane {background-color: green;}
        """)
        # ----- Additional Exercise info row -----
        self.browser_editor = TextBrowserEditor(self, 'browser', 'Instructions', '')
        self.browser_editor.activate_edit_mode()
        _main_muscle_group_id = self.info_grid.label_main_muscles_value.edit_widget.get_item_db_id()
        _main_muscle_image_bytes = db.select_from_table('muscle_group', 'image',
                                                        {'id': _main_muscle_group_id})
        self.diagram_main_muscle = ImageWithText(
            self, 'image_muscle1', 'Main muscle group', _main_muscle_image_bytes)
        _minor_muscle_group_id = self.info_grid.label_minor_muscles_value.edit_widget.get_item_db_id()
        _minor_muscle_image_bytes = db.select_from_table('muscle_group', 'image',
                                                         {'id': _minor_muscle_group_id}, get_none=True)
        self.diagram_minor_muscle = ImageWithText(
            self, 'image_muscle2', 'Minor muscle group', _minor_muscle_image_bytes)
        additional_info_row = HBoxPane(
            self, (self.browser_editor, self.diagram_main_muscle, self.diagram_minor_muscle), cont_margins=(0, 0, 0, 0))
        # ----- Button box -----
        self.button_box = DialogButtonBox(self, 'Create new Exercise', bttn_reject_text='Close')
        self.button_box.signal_accepted.connect(self._create_new_exer_clicked)
        self.button_box.signal_rejected.connect(self.reject)
        # ----- Set layout -----
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setAlignment(AlignFlag.Top)
        self.vbox_layout.addWidget(title_row)
        self.vbox_layout.addWidget(info_row)
        self.vbox_layout.addWidget(additional_info_row)
        self.vbox_layout.addStretch()
        self.vbox_layout.addWidget(self.button_box)
        self.vbox_layout.setAlignment(self.button_box, AlignFlag.Bottom)
        self.setLayout(self.vbox_layout)

    def _create_new_exer(self):
        # ----- New exercise data checks -----
        if not self.edit_name.valid:
            _msg = 'Exercise name is not valid'
            ErrorMessage('Create new exercise failed', _msg).exec()
            return False
        if not self.image_pos1.image_with_text.image_set:
            _msg = 'Position 1 image must be set'
            ErrorMessage('Create new exercise failed', _msg).exec()
            return False
        exer_name = get_value(self.edit_name)
        all_exer_names = db.select_from_table('exercises', 'name')
        if exer_name in all_exer_names:
            _msg = f'Exercise name "{exer_name}" already exist. Change the name.'
            ErrorMessage('Create new exercise failed', _msg).exec()
            return False
        if not self.browser_editor.browser_edit.text_valid:
            _msg = 'Instructions text is not valid'
            ErrorMessage('Create new exercise failed', _msg).exec()
            return False
        # ----- Collect new exercise data -----
        exer_type_id = self.info_grid.label_type_value.edit_widget.get_item_db_id()
        body_part_id = self.info_grid.label_body_part_value.edit_widget.get_item_db_id()
        main_muscle_id = self.info_grid.label_main_muscles_value.edit_widget.get_item_db_id()
        minor_muscle_id = self.info_grid.label_minor_muscles_value.edit_widget.get_item_db_id()
        equipment_id = self.info_grid.label_equipment_value.edit_widget.get_item_db_id()
        link = self.info_grid.label_link_value.edit_widget.url
        pos1_image = get_value(self.image_pos1)
        pos2_image = get_value(self.image_pos2) if self.image_pos2.image_with_text.image_set \
            else None
        instructions = get_value(self.browser_editor)
        favorite = False  # A default value
        user_permission = self.rb_box_exer_permission.checked_value
        # ----- Create base(bigger) icon -----
        crop_dialog = CropImageDialog(
            'Crop icon image', get_value(self.image_pos1), images.MAX_IMAGE_HEIGHT - 1,
            images.MAX_IMAGE_HEIGHT - 1, reject_bttn=False)
        crop_icon = crop_dialog.exec()
        if not crop_icon:
            return False  # Cropping icon cancelled
        # ----- Create icons dict bytes(for DB) -----
        base_icon_bytes = crop_dialog.get_cropped_image_bytes()
        icons_dict = images.get_icons_dict(base_icon_bytes)
        icons_dict_bytes = pickle.dumps(icons_dict)
        # ----- Create new Exercise data object and insert into DB -----
        new_exer_data = NewExerciseData(
            exer_name, exer_type_id, body_part_id, main_muscle_id, minor_muscle_id,
            equipment_id, pos1_image, pos2_image, icons_dict_bytes, instructions,
            favorite, link, user_permission
        )
        inserted = db.insert_exercise(new_exer_data)
        if not inserted:
            ErrorMessage('Create new exercise failed', 'New exercise couldnt be created').exec()
            return False
        # ----- Set new exer id and name(for bookmarks) -----
        _new_exer_id = DB().select_from_table('exercises', 'id', {'name': exer_name})
        self.new_exer_id = _new_exer_id
        self.new_exer_name = exer_name
        return True

    # ----- SLOTS -----

    def _create_new_exer_clicked(self):
        new_exer_created = self._create_new_exer()
        if new_exer_created:
            _msg = f'New exercise "{self.new_exer_name}" was created.\n\n ' \
                   f'NOTE: It was added in Bookmarks'
            InfoMessage('New exercise', _msg).exec()
            self.close()

    def _pos1_image_set(self):
        self.image_pos2.setEnabled(True)

    def _muscle_group_changed(self, is_main):
        cb = self.sender()
        if get_value(cb) == '-':
            _muscle_image_bytes = None
        else:
            _muscle_group_id = cb.get_item_db_id()
            _muscle_image_bytes = db.select_from_table('muscle_group', 'image', {'id': _muscle_group_id})
        diagram = self.diagram_main_muscle if is_main else self.diagram_minor_muscle
        set_value(diagram, _muscle_image_bytes)


class BookmarkExercisesBar(QtWidgets.QFrame):
    signal_bttn_clicked = QtCore.pyqtSignal(int)
    signal_add_exercise_to_table = QtCore.pyqtSignal(int, str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setSizePolicy(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM)
        # ----- GUI children -----
        self.hbox_layout = None
        self.bttn_active_exercise = None
        self.vertical_line = None
        self.label_bookmarks = None
        self.bttns_exercises = []
        # ----- Initialize UI -----
        self._init_ui()
        # ----- Connect events to slots -----
        self.bttn_active_exercise.clicked.connect(self._bttn_clicked)

    def _init_ui(self):
        # ----- GUI children -----
        self.bttn_active_exercise = RoundPushButton(
            self, 'bttn_active_exercise', 'ACTIVE EXERCISE', size=(120, 40),
            enabled=False, checkable=True, checked=True)
        self.bttn_active_exercise.exer_id = None
        self.vertical_line = VLine(self, size=(2, 40))
        self.label_bookmarks = MyLabel(
            self, 'label_bookmarks', 'Bookmarks:', FontFlag.BIG_TEXT)
        self.label_bookmarks.setFixedWidth(120)
        # ----- Set Layout -----
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setAlignment(AlignFlag.Left)
        self.hbox_layout.addWidget(self.bttn_active_exercise)
        self.hbox_layout.addWidget(self.vertical_line)
        self.hbox_layout.addWidget(self.label_bookmarks)
        for _exer_id in self._get_bookmarked_exercises():
            exer_name = db.select_from_table('exercises', 'name',
                                             {'id': str(_exer_id)}, get_none=True)
            if exer_name:
                self.add_bookmark_bttn(_exer_id, exer_name)
        self.hbox_layout.setAlignment(AlignFlag.Left)
        self.setLayout(self.hbox_layout)

    def add_bookmark_bttn(self, exer_id, exer_name):
        # Check if that bttn already exists; if not, just check it and return
        bookmark_bttn = find_widget_by_attr(self.bttns_exercises, 'exer_id', exer_id, get_none=True)
        if bookmark_bttn:
            self._set_bttns_checked(bookmark_bttn)
            return
        # Create new bookmark button
        bookmark_bttn = BookmarkButton(
            self, f'bttn_{str(exer_id)}', exer_id, exer_name)
        self.bttns_exercises.append(bookmark_bttn)
        self.hbox_layout.insertWidget(3, bookmark_bttn)
        # Connect new bookmark button events to slots
        bookmark_bttn.signal_bttn_clicked.connect(self._bttn_clicked)
        bookmark_bttn.signal_close_bttn.connect(self._close_bttn_clicked)

    def delete_bttn(self, exer_id):
        bttn = find_widget_by_attr(self.bttns_exercises, 'exer_id', exer_id)
        self.bttns_exercises.remove(bttn)
        bttn.deleteLater()

    def get_clicked_bttn(self):
        for bttn in self.bttns_exercises + [self.bttn_active_exercise]:
            if not bttn.isEnabled():
                return bttn
        raise ValueError('No bookmarks button is pressed.')

    def _set_bttns_checked(self, bttn_clicked):
        """Sets checked staates of all bookmark buttons. """
        for bttn in self.bttns_exercises + [self.bttn_active_exercise]:
            if bttn is not bttn_clicked:
                bttn.setEnabled(True)
        bttn_clicked.setEnabled(False)

    @staticmethod
    def _get_bookmarked_exercises():
        if not Path(BOOKMARKS_FILE).exists():
            # just create text file for bookmarks
            with open(BOOKMARKS_FILE, 'w') as fwrite:
                pass
            return []
        file_exer_ids = []
        with open(BOOKMARKS_FILE, 'r') as file_open:
            for line in file_open:
                file_exer_ids.append(int(line.strip()))
        exer_ids = []
        for file_exer_id in file_exer_ids:
            # Check if bookmarked exercise exist in DB
            # It is possible that the exercise was deleted
            db_exer_name = DB().select_from_table(
                'exercises', 'name', filters={'id': file_exer_id}, get_none=True)
            if db_exer_name:
                exer_ids.append(file_exer_id)
        return exer_ids

    def write_to_file(self):
        exer_ids = [bt.exer_id for bt in self.bttns_exercises]
        with open(BOOKMARKS_FILE, 'w') as file_open:
            for exer_id in exer_ids:
                file_open.write(str(exer_id) + '\n')

    # ----- SLOTS -----

    def _bttn_clicked(self):
        bttn_clicked = self.sender()
        self._set_bttns_checked(bttn_clicked)
        self.signal_bttn_clicked.emit(bttn_clicked.exer_id)

    def _close_bttn_clicked(self):
        bttn_clicked = self.sender()
        self.delete_bttn(bttn_clicked.exer_id)

    def _add_to_planner_table(self, exer_id, table_name):
        self.signal_add_exercise_to_table.emit(exer_id, table_name)


class ExerciseToolbar(QtWidgets.QWidget):
    signal_toolbar_bttn_clicked = QtCore.pyqtSignal(str)
    signal_load_to_table = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('exercise_toolbar')
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MAXIMUM)
        # ----- Data -----
        self.exercise_permission_type = None
        # ----- Gui children -----
        self.hbox_layout = None
        self.load_to_planner = None
        self.bttn_add_exercise = None
        self.bttn_change_icon = None
        self.bttn_edit_exercise = None
        self.bttn_save_changes = None
        self.bttn_cancel_edit = None
        self.bttn_del_exercise = None
        # ----- Init  UI -----
        self._init_ui()

    def _init_ui(self):
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.bttn_load_to_planner = ImageButton(self, 'bttn_load', ImageFp.LOAD, 'Load to planner table:')
        menu_load_to_planner = QtWidgets.QMenu(self)
        for day in DAYS:
            action = menu_load_to_planner.addAction(f'{day.title()}')
            action.triggered.connect(partial(self._load_to_table, day))
        self.bttn_load_to_planner.setMenu(menu_load_to_planner)
        self.bttn_add_exercise = ImageButton(self, 'bttn_add', ImageFp.NEW, 'Add Exercise')
        self.bttn_change_icon = ImageButton(self, 'bttn_icon', ImageFp.ICON, 'Change exercise icon',
                                            for_user_tooltip=True)
        self.bttn_edit_exercise = ImageButton(self, 'bttn_edit', ImageFp.EDIT, 'Edit Exercise data',
                                              for_user_tooltip=True)
        self.bttn_save_changes = ImageButton(self, 'bttn_save', ImageFp.SAVE, 'Save changes',
                                             enabled=False, for_user_tooltip=True)
        self.bttn_cancel_edit = ImageButton(self, 'bttn_cancel', ImageFp.CANCEL, 'Cancel edit',
                                            enabled=False, for_user_tooltip=True)
        self.bttn_del_exercise = ImageButton(self, 'bttn_delete', ImageFp.DELETE, 'Delete Exercise',
                                             for_user_tooltip=True)

        self.hbox_layout.addWidget(self.bttn_load_to_planner)
        self.hbox_layout.addWidget(self.bttn_add_exercise)
        self.hbox_layout.addWidget(self.bttn_change_icon)
        self.hbox_layout.addWidget(self.bttn_edit_exercise)
        self.hbox_layout.addWidget(self.bttn_save_changes)
        self.hbox_layout.addWidget(self.bttn_cancel_edit)
        self.hbox_layout.addWidget(self.bttn_del_exercise)
        self.setLayout(self.hbox_layout)

    def activate_view_mode(self):
        """In view mode, buttons: 'Add...', 'Edit...' and 'Delete' are active"""
        self.bttn_load_to_planner.setEnabled(True)
        self.bttn_add_exercise.setEnabled(True)
        self.bttn_change_icon.setEnabled(True)
        self.bttn_edit_exercise.setEnabled(True)
        self.bttn_save_changes.setEnabled(False)
        self.bttn_cancel_edit.setEnabled(False)
        self.bttn_del_exercise.setEnabled(True)

    def activate_edit_mode(self):
        """In view mode, buttons 'Save...' and 'Cancel...' are active"""
        self.bttn_load_to_planner.setEnabled(False)
        self.bttn_add_exercise.setEnabled(False)
        self.bttn_change_icon.setEnabled(False)
        self.bttn_edit_exercise.setEnabled(False)
        self.bttn_save_changes.setEnabled(True)
        self.bttn_cancel_edit.setEnabled(True)
        self.bttn_del_exercise.setEnabled(False)

    def set_toolbar_availability(self, available):
        if available:
            self.activate_view_mode()
        else:
            for bttn in (self.bttn_change_icon, self.bttn_edit_exercise, self.bttn_save_changes,
                         self.bttn_cancel_edit, self.bttn_del_exercise):
                bttn.setEnabled(False)

    def _load_to_table(self, table):
        self.signal_load_to_table.emit(table)


class ExerciseDataEditor(QtWidgets.QWidget):
    signal_edit_mode_activated = QtCore.pyqtSignal()
    signal_view_mode_activated = QtCore.pyqtSignal()
    signal_exercise_deleted = QtCore.pyqtSignal(int)
    signal_load_to_planner = QtCore.pyqtSignal(int, str)
    signal_refresh_exer_name_icon = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        # ----- Data -----
        self.exer_id = None
        self.new_exer_dialog = None
        # ----- GUI children -----
        self.vbox_layout = None
        self.bookmarks_bar = None
        self.toolbar = None
        self.exercise_data_viewer = None
        self.scroll_area = None
        self._init_ui()
        # ----- Connect events to slots -----
        self.bookmarks_bar.signal_bttn_clicked.connect(self._bookmark_exercise_selected)
        self.toolbar.signal_load_to_table.connect(self._load_to_planner)
        self.toolbar.bttn_add_exercise.clicked.connect(self._bttn_add_clicked)
        self.toolbar.bttn_change_icon.clicked.connect(self._bttn_change_icon_clicked)
        self.toolbar.bttn_edit_exercise.clicked.connect(self._bttn_edit_clicked)
        self.toolbar.bttn_edit_exercise.clicked.connect(self._bttn_edit_clicked)
        self.toolbar.bttn_save_changes.clicked.connect(self._bttn_save_clicked)
        self.toolbar.bttn_cancel_edit.clicked.connect(self._bttn_cancel_clicked)
        self.toolbar.bttn_del_exercise.clicked.connect(self._bttn_delete_clicked)

    def _init_ui(self):
        self.bookmarks_bar = BookmarkExercisesBar(self)
        self.toolbar = ExerciseToolbar(self)
        self.exercise_data_viewer = ExerciseDataViewer(self)
        self.scroll_area = ScrollArea(self, QtCore.Qt.Orientation.Horizontal)
        self.scroll_area.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MAXIMUM)
        self.scroll_area.setWidget(self.bookmarks_bar)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(self.scroll_area)
        self.vbox_layout.addWidget(self.toolbar)
        self.vbox_layout.addWidget(self.exercise_data_viewer)
        self.setLayout(self.vbox_layout)

    def set_active_exercise(self, exer_id):
        self._set_exer_and_toolbar(exer_id)
        self.bookmarks_bar.bttn_active_exercise.exer_id = exer_id
        self.bookmarks_bar.bttn_active_exercise.setEnabled(True)
        self.bookmarks_bar.bttn_active_exercise.click()

    def _set_exer_and_toolbar(self, exer_id):
        """ Sets editor exer_id and toolbar visibility """
        self.exer_id = exer_id
        if APP_MODE == AppMode.PRODUCTION_MODE:
            _user_permission = db.select_from_table('exercises', 'user_permission', {'id': exer_id})
            _visible = True if _user_permission else False
        else:
            _visible = True
        self.toolbar.set_toolbar_availability(_visible)

    # ----- SLOTS -----

    def _bookmark_exercise_selected(self, exer_id):
        # check_exer_id = db.select_from_table('exercises', 'name', {'id': exer_id}, get_none=True)
        # if check_exer_id:
        self._set_exer_and_toolbar(exer_id)
        self.exercise_data_viewer.set_data(exer_id)

    def _load_to_planner(self, table):
        self.signal_load_to_planner.emit(self.exer_id, table)

    def _bttn_add_clicked(self):
        self.new_exer_dialog = NewExerciseDialog()
        self.new_exer_dialog.exec()
        if self.new_exer_dialog.new_exer_id:
            self.bookmarks_bar.add_bookmark_bttn(
                self.new_exer_dialog.new_exer_id, self.new_exer_dialog.new_exer_name)
        self.new_exer_dialog = None

    def _bttn_change_icon_clicked(self):
        info_row = self.exercise_data_viewer.basic_info_row.row
        if info_row.pos2_image_text.view_widget.image_set:
            pos_choice_dialog = ChoiceDialog('Position 1', 'Position 2')
            pos_choice = pos_choice_dialog.get_choice()
            if not pos_choice:
                return False  # Exercise icon change cancelled
            pos_image = get_value(info_row.pos1_image_text.view_widget) if \
                pos_choice == 'Position 1' else get_value(info_row.pos2_image_text.view_widget)
        else:
            pos_image = get_value(info_row.pos1_image_text)
        crop_dialog = CropImageDialog(
            'Crop icon image', pos_image, images.MAX_IMAGE_HEIGHT - 1,
            images.MAX_IMAGE_HEIGHT - 1)
        image_cropped = crop_dialog.exec()
        if not image_cropped:
            return False  # Cropping icon cancelled
        cropped_pos_image = crop_dialog.get_cropped_image_bytes()
        icons_dict = images.get_icons_dict(cropped_pos_image)
        icons_dict_bytes = pickle.dumps(icons_dict)
        updated = DB().update_table(
            'exercises', {'icons_dict': icons_dict_bytes}, self.exer_id)
        if updated:
            self.signal_refresh_exer_name_icon.emit(self.exer_id)
            InfoMessage('Exercise update', 'Exercise icon updated.').exec()

    def _bttn_edit_clicked(self):
        self.signal_edit_mode_activated.emit()
        self.toolbar.activate_edit_mode()
        self.exercise_data_viewer.activate_edit_mode()

    def _bttn_save_clicked(self):
        # ----- Check data -----
        if not self.exercise_data_viewer.basic_info_row.title_row.title. \
                edit_widget.valid:
            ErrorMessage('Saving exercise info failed',
                         'Exercise name is not valid').exec()
            return
        instructions = self.exercise_data_viewer.additional_info_row.instructions
        if instructions.edit_mode and not instructions.browser_edit.text_valid:
            ErrorMessage('Saving exercise info failed',
                         'Instruction text is not valid').exec()
            return
        # ----- Update exercise data and activate view mode -----
        self.exercise_data_viewer.update_exercise()
        # --- If exercise name has changed, send signal to lists ---
        title = self.exercise_data_viewer.basic_info_row.title_row.title
        if get_value(title.view_widget) != get_value(title.edit_widget):
            self.signal_refresh_exer_name_icon.emit(self.exer_id)
        self.exercise_data_viewer.activate_view_mode(save=True)
        self.toolbar.activate_view_mode()
        self.signal_view_mode_activated.emit()

    def _bttn_cancel_clicked(self):
        self.exercise_data_viewer.activate_view_mode()
        self.toolbar.activate_view_mode()
        self.signal_view_mode_activated.emit()

    def _bttn_delete_clicked(self):
        exer_name = get_value(self.exercise_data_viewer.basic_info_row.title_row.
                              title.view_widget)
        _msg = f'Are you sure you want to delete exercise "{exer_name}"?'
        delete_exer = QuestionDialog('Delete exercise', _msg).exec()
        if delete_exer:
            deleted = DB().delete_exercise(self.exer_id)
            if not deleted:
                _msg = 'Exercise couldn\'t be deleted.'
                ErrorMessage('Exercise delete failed', _msg).exec()
                return
            # Delete exercise from bookmarks bar and send signal
            bttn = find_widget_by_attr(self.bookmarks_bar.bttns_exercises, 'exer_id',
                                       self.exer_id, get_none=True)
            if bttn:
                self.bookmarks_bar.delete_bttn(bttn.exer_id)
            self.signal_exercise_deleted.emit(self.exer_id)


class TabExercises(QtWidgets.QFrame):
    def __init__(self, parent, index):
        super().__init__(parent)
        self.index = index
        self.setObjectName('tab_exercises')
        # ----- Data -----
        self.list_exercises = None  # <-- helper attr
        # ----- Gui children -----
        self.hbox_layout = None
        self.exercise_list_viewer = None
        self.exercise_data_editor = None
        # ----- Initialize UI -----
        self._init_ui()
        # ----- Connect events to slots -----
        self.list_exercises.signal_add_exercise_to_book.connect(self._add_bookmark_exercise)
        self.list_exercises.signal_exercise_changed.connect(self._list_exercise_selected)
        self.exercise_data_editor.signal_exercise_deleted.connect(self._exercise_deleted)
        # ----- Post init actions -----
        self.list_exercises.select_index(0)

    def _init_ui(self):
        self.exercise_list_viewer = ExerciseListViewer(self)
        self.list_exercises = self.exercise_list_viewer.exercises_box.list_exercises
        self.exercise_data_editor = ExerciseDataEditor(self)
        # ----- Set Layout -----
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.addWidget(self.exercise_list_viewer)
        self.hbox_layout.addWidget(self.exercise_data_editor)
        self.setLayout(self.hbox_layout)

    # ----- SLOTS -----

    def _add_bookmark_exercise(self, exer_id, exer_name):
        self.exercise_data_editor.bookmarks_bar.add_bookmark_bttn(exer_id, exer_name)

    def _list_exercise_selected(self, exer_id):
        """Slot for exercise list new selection"""
        self.exercise_data_editor.set_active_exercise(exer_id)

    def _exercise_deleted(self, exer_id):
        # Delete bookmarked exercise(if it exists)
        bookmark_bar = self.exercise_data_editor.bookmarks_bar
        bttn = find_widget_by_attr(bookmark_bar.bttns_exercises, 'exer_id', exer_id, get_none=True)
        if bttn:
            bookmark_bar.delete_bttn(bttn.exer_id)
