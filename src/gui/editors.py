import re
import pickle
import logging
from pathlib import Path
from functools import partial, wraps

import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui

from config import DAYS, DAYS_TITLE, APP_MODE, AppMode
from settings import Settings
from ._delegates import TableEditorItemDelegate, TableViewerItemDelegate
from database.db_obj import DB
from database.data_model import (
    ExerciseListModel, ExerciseListRow, TableModel,
    EditableTableModel, ExerciseExecutionRow, SupersetRow,
    ExerciseData, WorkoutData, SupersetTopRow, SupersetBottomRow,
    TableRowType, WorkoutPdfData,
)

from gui.widgets import (
    MyScrollBar, RoundPushButton,
    ExerciseListView, TitleLabel, MyLabel,
    MyComboBox, FilterButton, ImageWithText,
    CheckableImageButton, InfoGridLabel,
    YoutubeLinkLabel, ResizePane, ImageButton,
    LineEdit, HBoxPane, ValidatedLineEdit,
    DBComboBox, DBTitleLabel, CheckBox, ExerciseDataViewEditWidget,
    LinkInfoGridLabel, RadiobuttonBox,
    FilterDBComboBox, ScrollArea, WorkoutListView,
    InputTextDialog, Image, LoadListItemDialog,
)
from .editors_NEW import TextBrowserEditor, InputImageWithText
from .font import Font, FontFlag

from export.motfile import import_workout
from gui.dialogs import (
    ErrorMessage, InfoMessage, QuestionDialog, get_filepath_from_dialog,
    raise_missing_exercises_error_msg,
)
from gui.flags import ImageFp, LayoutOrientation, SizePolicy, Orientation, Key, AlignFlag, MotType
from gui.colors import Colors, ThemeType
from gui.util import get_parent, set_value, get_value, find_widget_by_attr
from util import images
from util.obj import AttrObject
from util.value import int_list_in_order
from workout import (
    workout_name_valid, exercise_filtered_name_valid, plan_name_valid,
    get_available_generic_workout_name, get_default_exer_exec_data,
    get_default_col_value, calc_workout_time,
    PLAN_NAME_CHECK_ERROR_MSG, WORKOUT_NAME_CHECK_ERROR_MSG,
    EXERCISE_FILTERED_NAME_CHECK_ERROR_MSG, filter_existing_exercise_row_data
)


# -------------- Methods -------------


def table_altered(func):
    """Used in class <_WorkoutTableEditor> and <_EditableTableModel>
    NOTE: In future could be moved in another dir
    """
    @wraps(func)
    def check_table(table, *args, **kwargs):
        # ----- Execute decorated method -----
        func(table, *args, **kwargs)
        # ----- Start vars -----
        post_actions = {}  # Key= method object; Value= args
        in_superset = False
        superset_numb = 1
        exercises_in_superset = 0
        # ----- Check every row in table and format it -----
        for row, table_row in enumerate(table.model().exer_exec_rows):
            if type(table_row) == ExerciseExecutionRow:
                table.setRowHeight(row, table.icon_size.height())
                if in_superset:
                    table_row.superset_numb = superset_numb
                    table_row[1] = '-'
                    table_row[3] = '-'
                    exercises_in_superset += 1
                elif table_row.superset_numb:
                    table_row.superset_numb = None
                    table_row.sets = get_default_col_value(1, table_row.on_reps)
                    table_row.pause = get_default_col_value(3, table_row.on_reps)
            else:  # type(table_row) == SupersetRow
                table.setRowHeight(row, table_row.ROW_HEIGHT)
                if type(table_row) == SupersetTopRow:
                    in_superset = True
                    table_row.numb = superset_numb
                elif type(table_row) == SupersetBottomRow:
                    table_row.numb = superset_numb
                    in_superset = False
                    if exercises_in_superset < 2:
                        post_actions[table.remove_superset] = (superset_numb, )
                    exercises_in_superset = 0
                    superset_numb += 1
        # Emit table change
        table.signal_table_changed.emit()
        # Post check actions
        for method, args in post_actions.items():
            method(*args)
    return check_table


# ----- Left pane -----


class _FilterBox(QtWidgets.QWidget):
    signal_filter_activated = QtCore.pyqtSignal(dict)

    def __init__(self, parent):
        super().__init__(parent)
        # self.setStyleSheet('''
        #     _FilterBox {
        #         border: 1px solid blue;
        #         border-top-right-radius: 15px;
        #         border-top-left-radius: 15px;
        #         border-bottom-right-radius: 0px;
        #         border-bottom-right-radius: 0px;
        #     }
        # ''')
        # ----- Data -----
        self.combo_boxes = None  # helper attr, set in init
        self.filtered_name = ''
        self.filtered_favorite = None
        # ----- Gui children -----
        self.grid_layout = None
        self.label_exer_type = None
        self.label_body_part = None
        self.label_muscle_group = None
        self.label_equipment = None
        self.label_name = None
        self.label_favorite = None
        self.label_user_exer = None
        self.cb_exer_type = None
        self.cb_body_part = None
        self.cb_muscle_group = None
        self.cb_equipment = None
        self.exer_name = None
        self.rb_box_favorite = None
        self.rb_box_user_exer = None
        self.bttn_reset = None
        self.bttn_filter = None
        # Initialize UI
        self.init_ui()
        # Connect events to slots
        self.bttn_reset.clicked.connect(self._bttn_reset_clicked)
        self.bttn_filter.clicked.connect(self._bttn_filter_clicked)

    def init_ui(self):
        self.label_exer_type = MyLabel(self, 'label_exer_type', 'Exercise type: ', FontFlag.NORMAL_TEXT)
        self.label_body_part = MyLabel(self, 'label_body_part', 'Body part: ', FontFlag.NORMAL_TEXT)
        self.label_muscle_group = MyLabel(self, 'label_muscle_group', 'Muscle group:', FontFlag.NORMAL_TEXT)
        self.label_equipment = MyLabel(self, 'label_equipment', 'Equipment: ', FontFlag.NORMAL_TEXT)
        self.label_name = MyLabel(self, 'label_name', 'Exercise name: ', FontFlag.NORMAL_TEXT)
        self.label_favorite = MyLabel(self, 'label_favorite', 'Favorite: ', FontFlag.NORMAL_TEXT)
        self.label_user_exer = MyLabel(self, 'label_user_exer', 'User exercise: ', FontFlag.NORMAL_TEXT)
        _id_name_dict = dict(DB().select_from_table('exercise_type', ('id', 'name')))
        self.cb_exer_type = FilterDBComboBox(
            self, 'cb_exer_type', _id_name_dict, 'exercises.type_id', first_item='All')
        _id_name_dict = dict(DB().select_from_table('body_part', ('id', 'name')))
        self.cb_body_part = FilterDBComboBox(
            self, 'cb_body_part', _id_name_dict, 'exercises.body_part_id', first_item='All')
        _id_name_dict = dict(DB().select_from_table('muscle_group', ('id', 'name')))
        self.cb_muscle_group = FilterDBComboBox(
            self, 'cb_muscle_group', _id_name_dict, 'exercises.main_muscle_group_id', first_item='All')
        _id_name_dict = dict(DB().select_from_table('equipment', ('id', 'name')))
        self.cb_equipment = FilterDBComboBox(
            self, 'cb_equipment', _id_name_dict, 'exercises.equipment_id', first_item='All')
        self.exer_name = ValidatedLineEdit(
            self, 'exer_name', '', exercise_filtered_name_valid, EXERCISE_FILTERED_NAME_CHECK_ERROR_MSG,
            retain_msg_size=False, font_flag=FontFlag.SMALL_TEXT)
        self.exer_name.line_edit.setFixedHeight(20)
        self.rb_box_favorite = RadiobuttonBox(
            self, 'rb_box_favorite', [(None, 'All'), (True, 'Yes'), (False, 'No')],
            checked_rb_index=0, orientation=LayoutOrientation.HORIZONTAL)
        self.rb_box_favorite.setContentsMargins(0, 0, 0, 0)
        self.rb_box_user_exer = RadiobuttonBox(
            self, 'rb_box_user_exer', [(None, 'All'), (True, 'Yes'), (False, 'No')], checked_rb_index=0,
            orientation=LayoutOrientation.HORIZONTAL)
        self.rb_box_user_exer.setContentsMargins(0, 0, 0, 0)
        self.bttn_reset = RoundPushButton(self, 'bttn', 'Reset')
        self.bttn_filter = FilterButton(self, 'bttn_filter', 'Filter', enabled=True)
        # help list for all combo boxes
        self.combo_boxes = [self.cb_exer_type, self.cb_body_part, self.cb_muscle_group, self.cb_equipment]
        # Layout
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setColumnStretch(0, 2)
        self.grid_layout.setColumnStretch(1, 3)
        self.grid_layout.addWidget(self.label_exer_type, 0, 0)
        self.grid_layout.addWidget(self.label_body_part, 1, 0)
        self.grid_layout.addWidget(self.label_muscle_group, 2, 0)
        self.grid_layout.addWidget(self.label_equipment, 3, 0)
        self.grid_layout.addWidget(self.label_name, 4, 0)
        self.grid_layout.addWidget(self.cb_exer_type, 0, 1)
        self.grid_layout.addWidget(self.cb_body_part, 1, 1)
        self.grid_layout.addWidget(self.cb_muscle_group, 2, 1)
        self.grid_layout.addWidget(self.cb_equipment, 3, 1)
        self.grid_layout.addWidget(self.exer_name, 4, 1)
        self.grid_layout.addWidget(self.label_favorite, 5, 0)
        self.grid_layout.addWidget(self.rb_box_favorite, 5, 1)
        self.grid_layout.addWidget(self.label_user_exer, 6, 0)
        self.grid_layout.addWidget(self.rb_box_user_exer, 6, 1)
        self.grid_layout.addWidget(self.bttn_reset, 7, 0)
        self.grid_layout.addWidget(self.bttn_filter, 7, 1)
        self.setLayout(self.grid_layout)

    # ----- SLOTS -----

    def keyPressEvent(self, event):
        """When key 'enter' is pressed, clicked event on filtet button is emited
        """
        if event.key() in (Key.ENTER, Key.RETURN):
            self.bttn_filter.clicked.emit()

    def _bttn_reset_clicked(self):
        for cb in self.combo_boxes:
            set_value(cb, 'All')
        set_value(self.exer_name, '')
        set_value(self.rb_box_favorite, None)
        set_value(self.rb_box_user_exer, None)

    def _bttn_filter_clicked(self):
        # ----- Check exercise name -----
        if not self.exer_name.valid:
            _msg = 'Exercise name is not valid'
            ErrorMessage('Filter exercises failed', _msg).exec()
            return
        # Create db filter dict
        filters = {}
        for cb in self.combo_boxes:
            filters.update(cb.get_db_filter_dict())
        exer_name = get_value(self.exer_name)
        # if exer_name and self.exer_name != self.filtered_name:
        if exer_name:
            filters.update({'exercises.name': f'%{exer_name}%'})
        favorite_value = self.rb_box_favorite.checked_value
        # if favorite_value is not None and self.filtered_favorite != favorite_value:
        if favorite_value is not None:
            filters.update({'favorite': favorite_value})
        user_exer_value = self.rb_box_user_exer.checked_value
        if user_exer_value is not None:
            filters.update({'user_permission': user_exer_value})
        self.signal_filter_activated.emit(filters)


# noinspection PyTypeChecker
class _PageSelector(QtWidgets.QWidget):
    signal_page_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent, numb_of_pages):
        """

        :param parent:
        :param numb_of_pages:
        """
        super().__init__(parent)
        # Data
        self.dots_needed = None
        self.numb_of_pages = numb_of_pages
        self.page_selected = 1
        # GUI children
        self.buttons_and_dots = []
        self.hbox_layout = None
        # Initialite UI
        self.init_ui()

    def init_ui(self):
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self._create_and_add_items()
        self.setLayout(self.hbox_layout)

    def reset_widgets(self, numb_of_pages):
        """Deletes all widgets(button and labels) and create new ones."""
        self.numb_of_pages = numb_of_pages
        for i in range(len(self.hbox_layout) - 1, -1, -1):
            item = self.hbox_layout.itemAt(i)
            item.widget().deleteLater()
            self.hbox_layout.removeItem(item)
        self.buttons_and_dots.clear()
        self._create_and_add_items()

    def select_page(self, page_numb):
        bttn_numbers = [w for w in self.buttons_and_dots if type(w) == RoundPushButton]
        bttn_to_click = [bt for bt in bttn_numbers if int(bt.text()) == page_numb][0]
        if bttn_to_click.isEnabled():
            bttn_to_click.click()

    def _set_widget_properties(self, bttn_clicked):
        """Sets properties of buttons, dots(if exist) and arrow image buttons,
        after a button has beeen clicked.
        """
        # Set properties of number buttons
        bttn_numbers = [w for w in self.buttons_and_dots if type(w) == RoundPushButton]
        bttn_clicked.setEnabled(False)
        numb_clicked = int(bttn_clicked.text())
        for bttn in bttn_numbers:
            if bttn is not bttn_clicked:
                # All buttons except the one clicked
                bttn.setEnabled(True)
                bttn.setChecked(False)
                numb = int(bttn.text())
                visible = True if numb in list(range(numb_clicked - 1, numb_clicked + 2)) + \
                                  [1, len(bttn_numbers)] else False
                bttn.setVisible(visible)
        # Set properties of 'dots' labels(if they exist)
        if self.dots_needed:
            label_dots = [w for w in self.buttons_and_dots if type(w) == MyLabel]
            dot1_visible = True if numb_clicked > 3 else False
            label_dots[0].setVisible(dot1_visible)
            dot2_visible = True if numb_clicked < len(bttn_numbers) - 2 else False
            label_dots[1].setVisible(dot2_visible)
        # Set properties of Image buttons 'previous' and 'next'
        bttn_prev_visible = True if numb_clicked > 1 else False
        self.bttn_prev.setEnabled(bttn_prev_visible)
        bttn_next_visible = True if numb_clicked < len(bttn_numbers) else False
        self.bttn_next.setEnabled(bttn_next_visible)

    def _create_and_add_items(self):
        self.dots_needed = True if self.numb_of_pages > 3 else False
        self.bttn_prev = ImageButton(self, 'bttn_prev', ImageFp.PREVIOUS, 'Previous page', enabled=False)
        self.bttn_prev.clicked.connect(self._arrow_bttn_clicked)
        self.hbox_layout.addWidget(self.bttn_prev)
        self.hbox_layout.setAlignment(self.bttn_prev, QtCore.Qt.AlignmentFlag.AlignLeft)
        for numb in range(1, self.numb_of_pages + 1):
            visible = False if 3 < numb < self.numb_of_pages else True
            checked = True if numb == 1 else False
            enabled = False if numb == 1 else True
            new_bttn = RoundPushButton(self, f'bttn_{numb}', str(numb), size=(30, 30), enabled=enabled,
                                       visible=visible, checkable=True, checked=checked)
            new_bttn.clicked.connect(self._numb_bttn_clicked)
            self.buttons_and_dots.append(new_bttn)
            if self.dots_needed:
                if numb == 1:
                    label_dots = MyLabel(
                        self, f'label_dots_1', '...', FontFlag.NORMAL_TEXT, visible=False,
                        size=(30, 30), align_flag=QtCore.Qt.AlignmentFlag.AlignCenter
                    )
                    self.buttons_and_dots.append(label_dots)
                if numb == (self.numb_of_pages - 1):
                    label_dots = MyLabel(
                        self, f'label_dots_2', '...', FontFlag.NORMAL_TEXT, size=(30, 30),
                        align_flag=QtCore.Qt.AlignmentFlag.AlignCenter
                    )
                    self.buttons_and_dots.append(label_dots)
        # Add all widgets to layout
        for item in self.buttons_and_dots:
            self.hbox_layout.addWidget(item)
        _bttn_next_enabled = True if self.numb_of_pages > 1 else False
        self.bttn_next = ImageButton(self, 'bttn_next', ImageFp.NEXT, 'Next page', enabled=_bttn_next_enabled)
        self.bttn_next.clicked.connect(self._arrow_bttn_clicked)
        self.hbox_layout.addWidget(self.bttn_next)
        self.hbox_layout.setAlignment(self.bttn_next, QtCore.Qt.AlignmentFlag.AlignRight)

    def _numb_bttn_clicked(self):
        bttn_clicked = self.sender()
        self.page_selected = int(bttn_clicked.text())
        # noinspection PyTypeChecker
        self._set_widget_properties(bttn_clicked)
        self.signal_page_changed.emit(int(bttn_clicked.text()))

    def _arrow_bttn_clicked(self):
        arrow_bttn_clicked = self.sender()
        curr_bttn_pressed = [bt for bt in self.buttons_and_dots if
                             type(bt) == RoundPushButton and bt.isChecked()][0]
        curr_numb_pressed = int(curr_bttn_pressed.text())
        numb_to_press = curr_numb_pressed - 1 if \
            arrow_bttn_clicked.objectName() == 'bttn_prev' else \
            curr_numb_pressed + 1
        bttn_to_press = [bt for bt in self.buttons_and_dots if
                         bt.objectName() == f'bttn_{numb_to_press}'][0]
        self.page_selected = numb_to_press
        bttn_to_press.click()


class _ExerciseListBox(QtWidgets.QFrame):

    def __init__(self, parent):
        super().__init__(parent)
        # Data
        self.exer_per_page = int(Settings().getValue('exer_per_page'))
        self.exercises = DB().select_exercise_list_rows()
        self.model = ExerciseListModel(self.exercises[:self.exer_per_page])
        # Gui children
        self.title = None
        self.page_selector = None
        self.list_exercises = None
        # Initialite UI
        numb_of_pages = len(self.exercises) // self.exer_per_page + 1
        self.init_ui(numb_of_pages)
        self.page_selector.signal_page_changed.connect(self._page_changed)

    def init_ui(self, numb_of_pages):
        self.title = TitleLabel(self, 'title', 'Exercises')
        self.page_selector = _PageSelector(self, numb_of_pages)
        self.list_exercises = ExerciseListView(self)
        self.list_exercises.setModel(self.model)
        # Layout
        vbox_layout = QtWidgets.QVBoxLayout(self)
        vbox_layout.addWidget(self.title)
        vbox_layout.addWidget(self.page_selector)
        vbox_layout.addWidget(self.list_exercises)
        self.setLayout(vbox_layout)

    # def delete_selected_exercise(self):
    #     sel_index = self.list_exercises.selectedIndexes()[0]
    #     self.list_exercises.model().removeRows(sel_index.row(), 1)

    def select_next_exercise(self):
        if not self.list_exercises.model().rows:
            numb_bttns = [bt for bt in self.page_selector.buttons_and_dots if
                          type(bt) == RoundPushButton]
            if len(numb_bttns) == 1:
                # Only 1 page left with no exercises
                # -> can't select any exercise
                return False
            numb_clicked = int(numb_bttns.text())
            prev_bttn = [bt for bt in self.page_selector.buttons_and_dots if
                         int(bt.text()) == (numb_clicked - 1)][0]
            prev_bttn.click()
            return True
        self.list_exercises.select_index(0)
        return True

    def change_selected_name(self, new_name):
        sel_exer_id = self.list_exercises.get_selected_item_id()
        index = self.list_exercises.selectedIndexes()[0]
        icon = self.model.rows[index.row()].icon
        # TODO: fix this: must change only name and not create new row
        new_row = ExerciseListRow(sel_exer_id, new_name, icon)
        self.model.rows[index.row()] = new_row

    def reset_pages_and_exercise_list(self, exercises):
        self.exercises = exercises
        numb_of_pages = len(self.exercises) // self.exer_per_page + 1
        self.page_selector.reset_widgets(numb_of_pages)
        self.model = ExerciseListModel(exercises[:self.exer_per_page])
        self.list_exercises.setModel(self.model)

    def refresh_icon_name(self, exer_id):
        icons_dict, name = DB().select_from_table('exercises', ('icons_dict', 'name'),
                                                  filters={'id': exer_id})
        icon_bytes = DB().get_icon_bytes_from_icons_dict(icons_dict)
        for exer_row in self.exercises:
            if exer_row.exer_id == exer_id:
                exer_row.icon_bytes = icon_bytes
                exer_row.name = name
                break
        list_model = self.list_exercises.model()
        for row, exer_row in enumerate(list_model.rows):
            if exer_row.exer_id == exer_id:
                new_row = ExerciseListRow(exer_id, name, icon_bytes)
                list_model.setData(list_model.index(row), new_row,
                                   QtCore.Qt.ItemDataRole.EditRole)
                break

    # ----- SLOTS -----

    def _page_changed(self, page_numb):
        first_index = self.exer_per_page * (page_numb - 1)
        last_index = first_index + self.exer_per_page
        self.model = ExerciseListModel(self.exercises[first_index:last_index])
        self.list_exercises.setModel(self.model)
        self.list_exercises.select_index(0)


class ExerciseListViewer(QtWidgets.QFrame):

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(350)
        self.setObjectName('exercise_editor')
        self.setStyleSheet('''
            .ExerciseListViewer {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 20px;
            }
        ''' % (Colors.CONTAINER.hex, Colors.CONTAINER.hex))
        self.setContentsMargins(5, 5, 5, 5)
        # ----- Data -----
        self.active_filters = None
        # ----- GUI children -----
        self.resize_pane = None
        self.filter_box = None
        self.exercises_box = None
        # ----- Initialize UI -----
        self.init_ui()
        # ----- Connect events to slots -----
        self.filter_box.signal_filter_activated.connect(self._filter_clicked)

    def init_ui(self):
        self.filter_box = _FilterBox(self)
        self.resize_pane = ResizePane(self, self.filter_box, title='Filters')
        self.exercises_box = _ExerciseListBox(self)
        vbox_layout = QtWidgets.QVBoxLayout(self)
        vbox_layout.setContentsMargins(5, 5, 5, 5)
        vbox_layout.addWidget(self.resize_pane)
        vbox_layout.addWidget(self.exercises_box)
        self.setLayout(vbox_layout)

    def refresh_exercises(self):
        page_selector = self.exercises_box.page_selector
        list_exercises = self.exercises_box.list_exercises
        page_selected = page_selector.page_selected
        row_sel = list_exercises.selectedIndexes()[0].row()
        filtered = self._filter_exercises(self.active_filters, show_msg=False)
        if not filtered:
            list_exercises.setModel(ExerciseListModel([]))
            return False
        page_to_select = page_selected if page_selected <= page_selector.numb_of_pages else \
            page_selected - 1
        row_to_select = row_sel if row_sel <= (list_exercises.model().rowCount() - 1) else \
            row_sel - 1
        page_selector.select_page(page_to_select)
        if row_to_select >= 0:
            list_exercises.select_index(row_to_select)

    def _filter_exercises(self, filters, show_msg=True):
        exercises = DB().select_exercise_list_rows(filters)
        if not exercises:
            if show_msg:
                InfoMessage('No exercises found!', 'Can\'t find any exercise using set filters!').exec()
            return False
        self.exercises_box.reset_pages_and_exercise_list(exercises)
        self.exercises_box.list_exercises.select_index(0)
        return True

    # ----- SLOTS -----

    def _filter_clicked(self, filters):
        filtered = self._filter_exercises(filters)
        if filtered:
            self.active_filters = filters


# -------------- Table editors_NEW ---------------

class MouseMoveTracker:
    # TODO: Add mouse tracker table title
    signal_mouse_moved = QtCore.pyqtSignal()

    def __init__(self):
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        self.signal_mouse_moved.emit()


class _WorkoutTableBase(QtWidgets.QTableView):
    signal_table_changed = QtCore.pyqtSignal()
    signal_execise_selected = QtCore.pyqtSignal(str, int)
    signal_mouse_moved = QtCore.pyqtSignal()

    def __init__(self, parent, name):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setStyleSheet("""
            _WorkoutTableBase {
                border: 1px solid %s;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 6px;
            }
        """ % (Colors.CONTAINER.hex, Colors.TABLE_HEADER.hex,
               Colors.TABLE_HEADER.hex))
        # ----- Data -----
        _size = Settings().getValue('icon_size')
        self.icon_size = QtCore.QSize(_size[0], _size[1])
        self.name = name
        # ----- Props -----
        self.setObjectName(f'table_{name}')
        self.setModel(self.class_table_model())
        self.setIconSize(self.icon_size)
        self.setShowGrid(False)
        self.setVerticalScrollBar(MyScrollBar(self))
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        h_header = self.horizontalHeader()
        h_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        h_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        h_header.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        h_header.setHighlightSections(False)
        self.v_header = self.verticalHeader()
        self.v_header.setVisible(False)
        self.v_header.setMinimumSectionSize(SupersetRow.ROW_HEIGHT)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.signal_mouse_moved.emit()

    @table_altered
    def setModel(self, model):
        super().setModel(model)

    def selectionChanged(self, selected, deselected):
        QtWidgets.QTableView.selectionChanged(self, selected, deselected)
        indexes = selected.indexes()
        if len(indexes) > 0:
            index = indexes[0]
            table_row = self.model().exer_exec_rows[index.row()]
            if isinstance(table_row, SupersetRow):
                return
            self.signal_execise_selected.emit(self.objectName(), table_row.exer_id)

    def get_links(self):
        """Collects YouTube video tutorial links(if they exist) and
        returns them in a dict with format {%Exercise name%: %url%}
        """
        links = {}
        for table_row in self.model().exer_exec_rows:
            if type(table_row) == ExerciseExecutionRow:
                exer_name = table_row.icon_and_name[1]
                if not links.get(exer_name):
                    link = DB().select_from_table('exercises', 'link', {'id': table_row.exer_id})
                    if link:
                        links[exer_name] = link
        return links


class WorkoutTableViewer(_WorkoutTableBase):
    signal_show_exercise_info = QtCore.pyqtSignal(int)

    def __init__(self, parent, name):
        self.class_table_model = TableModel
        super().__init__(parent, name)
        self.item_delegate = TableViewerItemDelegate()
        self.setItemDelegate(self.item_delegate)

    def contextMenuEvent(self, event):
        indexes = self.selectedIndexes()
        if len(indexes) == 0:
            return  # Context menu opened in empty table
        index = indexes[0]
        context_menu = QtWidgets.QMenu(self)
        action_show_info = context_menu.addAction('Show exercise info')
        action = context_menu.exec(self.mapToGlobal(event.pos()))
        if action == action_show_info:
            exer_id = self.model().exer_exec_rows[index.row()].exer_id
            plan_area_base = get_parent(self, 'week_plan_viewer')
            if plan_area_base:
                plan_area_base.signal_show_exercise_info.emit(exer_id)
            else:
                self.signal_show_exercise_info.emit(exer_id)


class _WorkoutTableEditor(_WorkoutTableBase):
    signal_copy_rows = QtCore.pyqtSignal(str, str, tuple)

    def __init__(self, parent, name):
        self.class_table_model = EditableTableModel
        super().__init__(parent, name)
        self.item_delegate = TableEditorItemDelegate()
        self.setItemDelegate(self.item_delegate)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems)

    @table_altered
    def add_row(self, table_row, row_index=None):
        """Inserts new exercise into table.

        :param table_row: <ExerciseExecutionRow> or <SupersetRow>
        :param row_index: <int>
        :return: None
        """
        row_index = self.model().rowCount() if row_index is None else row_index
        self.model().insertRows(row_index, 1, table_row)

    @table_altered
    def add_superset(self, sel_rows):
        model = self.model()
        new_top_row = sel_rows[0]
        new_bottom_row = new_top_row + len(sel_rows) + 1  # +1 because of 1st added ss row
        numb_of_new_ss = len([r for r in model.exer_exec_rows if type(r) == SupersetTopRow]) + 1
        self.add_row(SupersetTopRow(numb_of_new_ss), new_top_row)
        ss_bottom_data = get_default_col_value(1, True), get_default_col_value(3, True)
        self.add_row(SupersetBottomRow(numb_of_new_ss, *ss_bottom_data), new_bottom_row)

    @table_altered
    def remove_rows(self, rows):
        rows = tuple(rows) if type(rows) not in (tuple, list) else rows
        model = self.model()
        for i, row in enumerate(rows):
            # "-i" is for every deleted row before
            model.removeRows(row - i, 1)

    @table_altered
    def remove_superset(self, superset_numb):
        # Get superset index pairs
        top_ss_row = None
        bottom_ss_row = None
        for row, table_row in enumerate(self.model().exer_exec_rows):
            if type(table_row) == SupersetTopRow and table_row.numb == superset_numb:
                top_ss_row = row
            elif type(table_row) == SupersetBottomRow and table_row.numb == superset_numb:
                bottom_ss_row = row
                break
        assert None not in (top_ss_row, bottom_ss_row), 'Superset number not found'
        self.remove_rows((top_ss_row, bottom_ss_row))

    def select_index(self, index_row, index_column):
        index = self.model().index(index_row, index_column)
        sel_model = self.selectionModel()
        sel_model.clearSelection()
        sel_model.select(index, QtCore.QItemSelectionModel.SelectionFlag.Select)

    @table_altered
    def switch_row_data(self, row1, row2):
        model = self.model()
        model.exer_exec_rows[row1], model.exer_exec_rows[row2] = \
            model.exer_exec_rows[row2], model.exer_exec_rows[row1]
        self.select_index(row2, 0)

    # ----- SLOTS -----

    def keyReleaseEvent(self, event):
        key_name = event.key()
        if key_name == Key.CTRL:
            get_parent(self, 'week_plan_editor').keyReleaseEvent(event)

    def keyPressEvent(self, event):
        key_name = event.key()
        if key_name == Key.CTRL:
            get_parent(self, 'week_plan_editor').keyPressEvent(event)
            return
        sel_indexes = self.selectedIndexes()
        if len(sel_indexes) == 0:
            return
        sel_index = sel_indexes[0]
        model = self.model()
        sel_row = sel_index.row()
        sel_col = sel_index.column()
        if key_name == Key.DOWN and sel_row < (model.rowCount() - 1):
            self.select_index(sel_row + 1, sel_col)
        elif key_name == Key.UP and sel_row > 0:
            self.select_index(sel_row - 1, sel_col)
        elif key_name == Key.RIGHT and sel_col < (model.columnCount() - 1):
            self.select_index(sel_row, sel_col + 1)
        elif key_name == Key.LEFT and sel_col > 0:
            self.select_index(sel_row, sel_col - 1)
        elif key_name in (Key.ENTER, Key.RETURN) and len(sel_indexes) == 1:
            # only 1 index must be selected for edit
            self.edit(sel_index)
        elif key_name == Key.DEL:
            sel_rows = [index.row() for index in sel_indexes]
            self.remove_rows(sel_rows)

    def contextMenuEvent(self, event):
        # sorted tuple of selected rows; NOTE: duplicate rows are removed with 'set'
        sel_rows = tuple(sorted(set([index.row() for index in self.selectedIndexes()])))
        if len(sel_rows) == 0:
            return  # empty table
        context_menu = QtWidgets.QMenu(self)
        model = self.model()
        # Set actions
        action_move_up = None
        action_move_down = None
        action_group_superset = None
        action_remove_superset = None
        action_go_to_info = None
        sel_row = sel_rows[0]
        if len(sel_rows) == 1:
            # Actions below only work with 1 row
            if sel_row > 0:
                action_move_up = context_menu.addAction("Move up")
            if sel_row < (model.rowCount() - 1):
                action_move_down = context_menu.addAction("Move down")
            if action_move_up or action_move_down:
                context_menu.addSeparator()
            action_go_to_info = context_menu.addAction("Show exercise info")
            context_menu.addSeparator()
        if len(sel_rows) > 1:
            # Check if selected rows are in order and if any are in a superset
            any_row_in_superset = any(model.exer_exec_rows[row].superset_numb for row in sel_rows)
            if int_list_in_order(sel_rows) and not any_row_in_superset:
                action_group_superset = context_menu.addAction("Group as superset")
                context_menu.addSeparator()
        other_tables = [table_name for table_name in DAYS if table_name != self.name]
        menu_copy_all_rows = context_menu.addMenu("Copy all rows to table:")
        copy_all_rows_actions = []
        for table in other_tables:
            copy_all_rows_actions.append(menu_copy_all_rows.addAction(table))
        #
        menu_copy_selected_rows = context_menu.addMenu("Copy selected rows to table:")
        copy_selected_rows_actions = []
        for table in other_tables:
            copy_selected_rows_actions.append(menu_copy_selected_rows.addAction(table))
        context_menu.addSeparator()
        #
        if len(sel_rows) == 1 and model.exer_exec_rows[sel_row].superset_numb:
            action_remove_superset = context_menu.addAction("Remove superset")
            context_menu.addSeparator()
        action_remove_row = context_menu.addAction("Remove")
        action_remove_all = context_menu.addAction("Remove all")

        # Execute context menu
        action = context_menu.exec(self.mapToGlobal(event.pos()))
        if not action:  # clicked outside of context menu
            return
        if action == action_move_up:
            self.switch_row_data(sel_row, sel_row - 1)
            self.select_index(sel_row - 1, 0)
        elif action == action_move_down:
            self.switch_row_data(sel_row, sel_row + 1)
            self.select_index(sel_row + 1, 0)
        elif action == action_go_to_info:
            exer_id = model.exer_exec_rows[sel_row].exer_id
            get_parent(self, 'week_plan_editor').signal_show_exercise_info.emit(exer_id)
        elif action == action_group_superset:
            self.add_superset(sel_rows)
        elif action == action_remove_superset:
            self.remove_superset(model.exer_exec_rows[sel_row].superset_numb)
        elif action in copy_all_rows_actions:
            self.signal_copy_rows.emit(self.name, action.text(), tuple(range(model.rowCount())))
        elif action in copy_selected_rows_actions:
            self.signal_copy_rows.emit(self.name, action.text(), sel_rows)
        elif action == action_remove_row:
            self.remove_rows(sel_rows)
        elif action == action_remove_all:
            self.remove_rows(tuple(range(model.rowCount())))

    def wheelEvent(self, wheel_event):
        # If key "Ctrl" is pressed in plan editor move horizontal bar
        if get_parent(self, 'week_plan_editor').ctrl_pressed:
            get_parent(self, 'week_plan_editor').wheelEvent(wheel_event)
            return
        # move vertical bar in table
        vbar = self.verticalScrollBar()
        if wheel_event.angleDelta().y() == Key.WHEEL_DOWN:
            vbar.move_bar(vbar.MOVE_DOWN_LENGHT)
        elif wheel_event.angleDelta().y() == Key.WHEEL_UP:
            vbar.move_bar(vbar.MOVE_UP_LENGHT)


class _WorkoutEditorToolbar(QtWidgets.QWidget):
    signal_change_visibility = QtCore.pyqtSignal()
    signal_save_workout = QtCore.pyqtSignal()
    signal_load_workout = QtCore.pyqtSignal()
    signal_import_workout = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum,
                           QtWidgets.QSizePolicy.Policy.Maximum)
        self.setContentsMargins(0, 0, 0, 0)
        # Data
        self.hbox_layout = None
        self.bttn_options = None
        self.bttn_visibility = None
        self._init_ui()
        # Events to slots
        # self.bttn_visibility.clicked.connect(self._show_hide_table)
        self.bttn_visibility.clicked.connect(lambda: self.signal_change_visibility.emit())

    def _init_ui(self):
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.bttn_options = ImageButton(self, 'bttn_options', ImageFp.MENU, 'Options', visible=False)
        menu_options = QtWidgets.QMenu(self.bttn_options)
        menu_options.addAction(QtGui.QIcon(ImageFp.LOAD), 'Load workout',
                               lambda: self.signal_load_workout.emit())
        menu_options.addAction(QtGui.QIcon(ImageFp.SAVE), 'Save workout',
                               lambda: self.signal_save_workout.emit())
        menu_options.addAction(QtGui.QIcon(ImageFp.IMPORT), 'Import workout',
                               lambda: self.signal_import_workout.emit())
        self.bttn_options.setMenu(menu_options)
        self.bttn_visibility = CheckableImageButton(self, 'bttn_vis', ImageFp.VISIBLE,
                                                    ImageFp.INVISIBLE, 'Hide table',
                                                    'Show table',
                                                    visible=False)
        self.hbox_layout.addWidget(self.bttn_options)
        self.hbox_layout.addWidget(self.bttn_visibility)
        self.setLayout(self.hbox_layout)

    def set_visibility(self, visible):
        self.bttn_options.setVisible(visible)
        self.bttn_visibility.setVisible(visible)


class _WorkoutViewerToolbar(QtWidgets.QWidget):
    signal_change_visibility = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum,
                           QtWidgets.QSizePolicy.Policy.Maximum)
        self.setContentsMargins(0, 0, 0, 0)
        # ----- GUi children -----
        self.hbox_layout = None
        self.bttn_visibility = None
        self._init_ui()
        # ----- Connect events to slots -----
        self.bttn_visibility.clicked.connect(lambda: self.signal_change_visibility.emit())

    def _init_ui(self):
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.bttn_visibility = CheckableImageButton(self, 'bttn_vis', ImageFp.VISIBLE,
                                                    ImageFp.INVISIBLE, 'Hide table',
                                                    'Show table',
                                                    visible=False)
        self.hbox_layout.addWidget(self.bttn_visibility)
        self.setLayout(self.hbox_layout)

    def set_visibility(self, visible):
        self.bttn_visibility.setVisible(visible)


class _WorkoutEditorInfoRow(QtWidgets.QFrame, MouseMoveTracker):
    def __init__(self, parent, table_name):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        # Data
        self.table_name = table_name
        # GUI children
        self.hbox_layout = None
        self.workout_name = None
        self.workout_type = None
        self._init_ui()

    def _init_ui(self):
        workout_name = get_available_generic_workout_name(self.table_name)
        self.workout_name = ValidatedLineEdit(
            self, 'workout_name', workout_name, workout_name_valid,
            WORKOUT_NAME_CHECK_ERROR_MSG, bg_color=Colors.WORKOUT_TITLE.hex,
            border_radius=4, text_color='white', align_flag=AlignFlag.Center,
            retain_msg_size=False, font_flag=FontFlag.NORMAL_TEXT)
        _id_name_dict = dict(DB().select_from_table('plan_type', ('id', 'name')))
        self.workout_type = DBComboBox(
            self, 'cb_plan_type', _id_name_dict, font_flag=FontFlag.NORMAL_TEXT,
            tooltip='Workout type', size=(100, 20))
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.hbox_layout.addWidget(self.workout_name)
        self.hbox_layout.addWidget(self.workout_type)
        self.hbox_layout.setAlignment(self.workout_name, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.hbox_layout.setAlignment(self.workout_type, QtCore.Qt.AlignmentFlag.AlignRight)
        self.setLayout(self.hbox_layout)

    def reset_values(self):
        new_workout_name = get_available_generic_workout_name(self.table_name)
        self.workout_name.set_text(new_workout_name)
        self.workout_type.setCurrentIndex(0)


class WorkoutViewerInfoRow(QtWidgets.QWidget, MouseMoveTracker):
    def __init__(self, parent, table_name):
        super().__init__(parent)
        # Data
        self.table_name = table_name
        # GUI children
        self.hbox_layout = None
        self.workout_name = None
        self.workout_type = None
        self._init_ui()

    def _init_ui(self):
        workout_name = get_available_generic_workout_name(self.table_name)
        self.workout_name = TitleLabel(
            self, 'workout_title', workout_name, font_flag=FontFlag.SMALL_TEXT,
            bg_color=Colors.WORKOUT_TITLE.hex
        )
        _id_name_dict = dict(DB().select_from_table('plan_type', ('id', 'name')))
        self.workout_type = DBTitleLabel(
            self, 'workout_title', _id_name_dict, bg_color=Colors.PLAN_TYPE.hex,
            text_color='black', font_flag=FontFlag.SMALL_TEXT
        )
        self.workout_type.setToolTip('Workout type')
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.hbox_layout.addWidget(self.workout_name)
        self.hbox_layout.addWidget(self.workout_type)
        self.hbox_layout.setAlignment(self.workout_name, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.hbox_layout.setAlignment(self.workout_type, QtCore.Qt.AlignmentFlag.AlignRight)
        self.setLayout(self.hbox_layout)

    def reset_values(self):
        new_workout_name = get_available_generic_workout_name(self.table_name)
        _default_workout_type = tuple(self.workout_type.id_name_dict.items())[0][1]
        set_value(self.workout_name, new_workout_name)
        set_value(self.workout_type, _default_workout_type)


class WorkoutTimeBox(QtWidgets.QWidget):
    def __init__(self, parent, time_min=0):
        super().__init__(parent)
        # Data
        self.time_min = time_min
        # GUI children
        self.hbox_layout = None
        self.label = None
        self.label_time = None
        self._init_ui()

    def _init_ui(self):
        self.label = MyLabel(self, 'label', 'Workout time: ', font_flag=FontFlag.SMALL_TEXT)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.label_time = MyLabel(self, 'label_time', self._get_time_str(),
                                  font_flag=FontFlag.SMALL_TEXT_BOLD)
        self.label_time.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum,
                                      QtWidgets.QSizePolicy.Policy.Maximum)
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.addWidget(self.label)
        self.hbox_layout.addWidget(self.label_time)
        self.setLayout(self.hbox_layout)

    def _get_time_str(self):
        return f'<b>{self.time_min // 60}h: {self.time_min % 60}min</b>'

    def set_workout_time(self, time_min):
        self.time_min = time_min
        self.label_time.setText(self._get_time_str())


class _WorkoutTitleRow(HBoxPane, MouseMoveTracker):
    def __init__(self, parent, widgets, cont_margins=(5, 5, 5, 5)):
        super().__init__(parent, widgets, cont_margins=cont_margins)


class _WorkoutArea(QtWidgets.QFrame):
    MAX_WIDTH = 400

    def __init__(self, parent, title_text):
        super().__init__(parent)
        # ----- Data -----
        self.name = title_text.lower()
        # ----- Gui -----
        self.vbox_layout = None
        self.toolbar = None
        self.title_row = None
        self.title = None
        self.workout_info_row = None
        self.table = None
        self.workout_time = None
        # --- Props ---
        self.setObjectName('workout_area')
        self.setFixedWidth(_WorkoutArea.MAX_WIDTH)
        # self.setMouseTracking(True)
        self.setContentsMargins(10, 0, 10, 0)
        self.setStyleSheet("""
        _WorkoutArea {
            border-radius: 4px;
            border: 1px solid %s;
            background-color: %s;
        }
        """ % (Colors.CONTAINER.hex, Colors.CONTAINER.hex))
        # Initialize UI
        self.init_ui(title_text)
        # Connect events to slots
        self.toolbar.signal_change_visibility.connect(self._bttn_hide_show_clicked)

    def init_ui(self, title_text):
        self.toolbar = self.class_toolbar(self)
        self.title = TitleLabel(self, 'title', title_text,
                                font_flag=FontFlag.BIG_TEXT_BOLD,
                                bg_color=Colors.DAY_TITLE.hex)
        self.title_row = _WorkoutTitleRow(self, (self.toolbar, self.title))
        self.workout_info_row = self.class_workout_info_row(self, title_text.lower())
        self.table = self.class_table(self, title_text.lower())
        self.workout_time = WorkoutTimeBox(self)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.vbox_layout.addWidget(self.title_row)
        self.vbox_layout.addWidget(self.workout_info_row)
        self.vbox_layout.addWidget(self.table)
        self.vbox_layout.addWidget(self.workout_time)

        self.title_row.setContentsMargins(0, 0, 0, 0)
        self.workout_info_row.setContentsMargins(0, 0, 0, 0)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)

        self.vbox_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbox_layout)

    def get_workout_data(self):
        table_rows = self.table.model().exer_exec_rows
        if not table_rows:
            return None
        else:
            workout_name = get_value(self.workout_info_row.workout_name)
            workout_type_id = self.workout_info_row.workout_type.get_item_db_id()
            rows_data = []
            for table_row in table_rows:
                rows_data.append(table_row.to_data())
            workout_data = WorkoutData(workout_name,
                                       workout_type_id,
                                       rows_data,
                                       self.workout_time.time_min)
            return workout_data

    def get_workout_pdf_data(self):
        table_rows = self.table.model().exer_exec_rows
        if not table_rows:
            return None
        else:
            workout_name = get_value(self.workout_info_row.workout_name)
            workout_type = get_value(self.workout_info_row.workout_type)
            workout_type_icon_bytes = DB().select_from_table('plan_type', 'icon', {'name': workout_type})
            workout_pdf_data = WorkoutPdfData(
                workout_name, workout_type, workout_type_icon_bytes, table_rows,
                self.workout_time.time_min
            )
            return workout_pdf_data

    def set_workout_from_data(self, workout_data):
        if not workout_data:
            # No data is given(workout_data=None), so workout data is reset
            self.workout_info_row.reset_values()
            self.table.setModel(self.class_table_data_model())
            self.workout_time.set_workout_time(0)
            return
        set_value(self.workout_info_row.workout_name, workout_data.name)
        self.workout_info_row.workout_type.set_text_by_id(workout_data.type_id)
        table_rows = []
        for row_data in workout_data.rows_data:
            table_row = DB().get_table_row_obj_from_data(row_data)
            table_rows.append(table_row)
        self.table.setModel(self.class_table_data_model(table_rows))
        self.workout_time.set_workout_time(workout_data.workout_time)

    def _bttn_hide_show_clicked(self):
        visible = False if self.table.isVisible() else True
        if hasattr(self.toolbar, 'bttn_options'):
            # TODO: maybe implement different solution
            self.toolbar.bttn_options.setVisible(visible)
        self.title.setVisible(visible)
        self.workout_info_row.setVisible(visible)
        self.table.setVisible(visible)
        self.workout_time.setVisible(visible)
        if visible:
            self.setFixedWidth(_WorkoutArea.MAX_WIDTH)
        else:
            # TODO: find another solution, for now this will(have to) work
            self.setFixedWidth(self.toolbar.bttn_visibility.width() + 30)


class _WorkoutAreaViewer(_WorkoutArea):
    def __init__(self, parent, title_text):
        self.class_toolbar = _WorkoutViewerToolbar
        self.class_workout_info_row = WorkoutViewerInfoRow
        self.class_table = WorkoutTableViewer
        self.class_table_data_model = TableModel
        super().__init__(parent, title_text)

    def set_toolbar_visibility(self, visible):
        if self.table.isVisible():
            self.toolbar.bttn_visibility.setVisible(visible)


class _WorkoutAreaEditor(_WorkoutArea):
    signal_workout_saved = QtCore.pyqtSignal()

    def __init__(self, parent, title_text):
        # ----- Data -----
        self.class_toolbar = _WorkoutEditorToolbar
        self.class_workout_info_row = _WorkoutEditorInfoRow
        self.class_table = _WorkoutTableEditor
        self.class_table_data_model = EditableTableModel
        super().__init__(parent, title_text)
        # self.setStyleSheet("""border: 1px solid black;""")
        # connect event to slots
        self.toolbar.signal_save_workout.connect(self._save_workout_clicked)
        self.toolbar.signal_load_workout.connect(self._load_workout_clicked)
        self.toolbar.signal_import_workout.connect(self._import_workout_clicked)
        self.table.selectionModel().selectionChanged.connect(self._table_focused)
        self.table.model().rowsInserted.connect(self._table_focused)
        self.table.signal_table_changed.connect(self._table_data_changed)
        self.table.item_delegate.signal_table_data_changed.connect(self._table_data_changed)

    def set_toolbar_visibility(self, visible):
        if self.table.isVisible():
            self.toolbar.bttn_options.setVisible(visible)
            self.toolbar.bttn_visibility.setVisible(visible)

    def _save_workout(self):
        # ----- Collect Data -----
        workout_name = get_value(self.workout_info_row.workout_name)
        workout_type_id = self.workout_info_row.workout_type.get_item_db_id()
        table_rows = self.table.model().exer_exec_rows
        workout_rows_data = [row.to_data() for row in table_rows]
        workout_time = self.workout_time.time_min
        workout_data = WorkoutData(workout_name, workout_type_id, workout_rows_data, workout_time)
        # ----- Save new/existing workout
        existing_workout_id = DB().select_from_table('workout', 'id', {'name': workout_name},
                                                   get_none=True)
        if existing_workout_id:
            _msg = f'Workout "{workout_name}" already exist.\n\n' \
                   f'Do you want to overwrite it?'
            overwrite = QuestionDialog('Overwrite workout', _msg).exec()
            if overwrite:
                updated = DB().update_workout(existing_workout_id, workout_data)
                if updated:
                    InfoMessage(f'Save workout', f'Workout "{workout_name}" saved.').exec()
                    logging.info(f'Workout "{workout_name}" updated.')
        else:
            user_permission = True
            if APP_MODE == AppMode.DEVELOPMENT_MODE:
                _msg = 'Save this workout as USER workout?\n' \
                       'NOTE: Click "No" to save plan as SYSTEM workout.'
                user_permission = QuestionDialog('Plan permission type(Development mode)',
                                                 _msg).exec()
            inserted = DB().insert_into_workout(workout_data, user_permission)
            if inserted:
                InfoMessage('Save new workout', f'New workout "{workout_name}" saved in App').exec()
                logging.info(f'New workout "{workout_name}" inserted in DB.')
        self.signal_workout_saved.emit()

    def load_workout(self, workout_row):
        # ----- Check if workout has rows and save it(is user wants)
        if self.table.model().rowCount() > 0:
            _msg = f'Do you wan\'t to save workout "{workout_row.name}"?'
            save_workout = QuestionDialog('Save workout', _msg).exec()
            if save_workout:
                if self.workout_data_set():
                    self._save_workout()
        # ----- Set workout data -----
        _rows_data = DB().select_workout_rows_data(workout_row.workout_id)
        rows_data, missing_exercises = filter_existing_exercise_row_data(_rows_data)
        table_rows = []
        for row_data in rows_data:
            table_rows.append(DB().get_table_row_obj_from_data(row_data))
        set_value(self.workout_info_row.workout_name, workout_row.name)
        set_value(self.workout_info_row.workout_type, workout_row.workout_type)
        self.table.setModel(EditableTableModel(table_rows))
        if missing_exercises:
            raise_missing_exercises_error_msg(missing_exercises, MotType.WORKOUT)

    def workout_data_set(self, action_type='Save workout'):
        table_rows = self.table.model().exer_exec_rows
        if not table_rows:
            ErrorMessage(f'{action_type} failed', 'There are no exercises in table').exec()
            return False
        if not self.workout_info_row.workout_name.valid:
            ErrorMessage(f'{action_type} failed', WORKOUT_NAME_CHECK_ERROR_MSG).exec()
            return False
        return True

    def _save_workout_clicked(self):
        if self.workout_data_set():
            self._save_workout()

    def _load_workout_clicked(self):
        # ----- Get workout row from Workout List -----
        dialog = LoadListItemDialog('Load workout', WorkoutListView)
        workout_row = dialog.get_list_item()
        if workout_row:
            self.load_workout(workout_row)

    def _import_workout_clicked(self):
        _start_dir = Settings().getValue('motfiles_folderpath')
        workout_fp = get_filepath_from_dialog(
            self, title='Choose Workout file from PC', start_dir=_start_dir,
            file_types='Workout files (*.motwork)')
        if workout_fp:
            workout_data = import_workout(workout_fp)
            if workout_data:
                self.set_workout_from_data(workout_data)

    def _table_focused(self, event):
        get_parent(self, 'week_plan_editor').selected_table = self.table

    def _table_data_changed(self):
        workout_time = calc_workout_time(self.table.model().exer_exec_rows)
        self.workout_time.set_workout_time(workout_time)


class _PlanAreaBase(QtWidgets.QFrame):
    signal_show_exercise_info = QtCore.pyqtSignal(int)

    def __init__(self, parent, workout_area_class):
        super().__init__(parent)
        self.setObjectName('plan_area_base')
        # ----- Data -----
        self.tables = []  # Helper attr
        self.ctrl_pressed = False
        # Gui children
        self.hbox_layout = None
        self.workout_areas = []
        # init GUI
        self.init_ui(workout_area_class)
        # Connect events to slots
        for workout_area in self.workout_areas:
            table_name = workout_area.table.name
            workout_area.title_row.signal_mouse_moved.connect(partial(self._mouse_entered, table_name))
            workout_area.workout_info_row.signal_mouse_moved.connect(partial(self._mouse_entered, table_name))
            workout_area.table.signal_mouse_moved.connect(partial(self._mouse_entered, table_name))

    def init_ui(self, workout_area_class):
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(5, 5, 5, 5)
        self.hbox_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        for i, day in enumerate(DAYS_TITLE):
            day_plan = workout_area_class(self, day)
            self.workout_areas.append(day_plan)
            self.tables.append(day_plan.table)
            self.hbox_layout.addWidget(day_plan)
        self.setLayout(self.hbox_layout)

    def get_workouts_data(self):
        """Returns all workouts
        :return [WorkoutData, WorkoutData, ...]
        """
        workouts_data = []
        for i in range(7):
            workouts_data.append(self.workout_areas[i].get_workout_data())
        return workouts_data

    def set_plan_workouts(self, workouts_data):
        """week_plan_data:

        :param workouts_data: [<workout_data> or None, ...]
        """
        missing_exercises = []
        for i, workout_area in enumerate(self.workout_areas):
            # --- Check if workout data exist ---
            workout_data = None
            if workouts_data[i]:
                rows_data, missing_exers = filter_existing_exercise_row_data(workouts_data[i].rows_data)
                workout_data = WorkoutData(workouts_data[i].name, workouts_data[i].type_id,
                                           tuple(rows_data), workouts_data[i].workout_time)
                missing_exercises += missing_exers
            workout_area.set_workout_from_data(workout_data)
        if any(workouts_data) and type(self) == PlanAreaEditor:
            self.select_next_exercise()
        if missing_exercises:
            raise_missing_exercises_error_msg(missing_exercises, MotType.PLAN)

    def get_table_by_name(self, table_name):
        table = [table for table in self.tables if table.name == table_name][0]
        return table

    def get_workouts_pdf_data(self):
        workouts_pdf_data = []
        for workout_area in self.workout_areas:
            workouts_pdf_data.append(workout_area.get_workout_pdf_data())
        return workouts_pdf_data

    def get_all_links(self):
        """Collects YouTube video tutorial links(if they exist) from all
        tables and returns them in a dict with format {%Exercise name%: %url%}
        """
        all_links = {}
        for table in self.tables:
            table_links = table.get_links()
            all_links.update(table_links)
        return all_links

    # SLOTS

    def keyReleaseEvent(self, event) -> None:
        key_name = event.key()
        if key_name == Key.CTRL:
            self.ctrl_pressed = False

    def keyPressEvent(self, event) -> None:
        key_name = event.key()
        if key_name == Key.CTRL:
            self.ctrl_pressed = True

    def wheelEvent(self, wheel_event) -> None:
        if not self.ctrl_pressed:
            return
        plan_editor = get_parent(self, 'plan_editor')
        y = 20 if wheel_event.angleDelta().y() == -120 else -20
        plan_editor.scroll_y(y)

    def leaveEvent(self, event):
        """Hides workout area toolbar if mouse leaves plan area space"""
        for day_plan in self.workout_areas:
            day_plan.set_toolbar_visibility(False)

    def _mouse_entered(self, table_name):
        for workout_area in self.workout_areas:
            if workout_area.table.name == table_name:
                workout_area.set_toolbar_visibility(True)
            else:
                workout_area.set_toolbar_visibility(False)


class PlanAreaViewer(_PlanAreaBase):
    def __init__(self, parent):
        super().__init__(parent, _WorkoutAreaViewer)
        self.setObjectName('week_plan_viewer')


class PlanAreaEditor(_PlanAreaBase):
    signal_workout_saved = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent, _WorkoutAreaEditor)
        self.setObjectName('week_plan_editor')
        # Data
        self.selected_table = self.workout_areas[0].table
        # Connect events to slots
        for workout_area in self.workout_areas:
            workout_area.signal_workout_saved.connect(lambda: self.signal_workout_saved.emit())
            workout_area.table.signal_copy_rows.connect(self._copy_rows)

    def add_table_row(self, exer_data, table_name=None):
        # Add row
        if table_name:
            table_index = DAYS.index(table_name)
            self.selected_table = self.tables[table_index]
        exer_exec_work_data = get_default_exer_exec_data(exer_data.exer_type)
        exer_exec_row = ExerciseExecutionRow(exer_data.exer_id, exer_data.icon_bytes,
                                             exer_data.name, exer_exec_work_data.sets,
                                             exer_exec_work_data.reps, exer_exec_work_data.pause,
                                             exer_exec_work_data.on_reps)
        self.selected_table.add_row(exer_exec_row)

    def select_next_exercise(self):
        for table in self.tables:
            if table.model().rowCount() > 0:
                table.select_index(0, 0)
                return
        # NOTE: exer_id = 0 -> tables are empty, so no exercise row to emit
        self.tables[0].signal_execise_selected.emit('table_monday', 0)

    def set_selected_table(self, table_obj_name):
        # table_area = getattr(self, table_obj_name.split('_')[1])
        day_plan = [dp for dp in self.workout_areas if
                    dp.table.objectName() == table_obj_name][0]
        self.selected_table = day_plan.table

    def workout_data_set(self, action_name):
        """Check if all workout info is set and if there are any table rows"""
        has_workout_rows = False
        for workout_area in self.workout_areas:
            if not workout_area.workout_info_row.workout_name.valid:
                _msg = f'Workout name in table {workout_area.title.text()} is not valid.'
                ErrorMessage(action_name, _msg).exec()
                return False
            if workout_area.table.model().exer_exec_rows:
                has_workout_rows = True
        if not has_workout_rows:
            ErrorMessage(action_name, 'There are not exercises in plan').exec()
            return False
        return True

    def _copy_rows(self, from_table_name, to_table_name, sel_rows):
        from_table = self.get_table_by_name(from_table_name)
        exer_exec_rows = from_table.model().exer_exec_rows
        for row_index in sel_rows:
            row = exer_exec_rows[row_index]
            if row.row_type == TableRowType.EXER_EXEC:
                exercise_data = DB().select_exercise_data(row.exer_id)
                self.add_table_row(exercise_data, table_name=to_table_name)


# ----------------- Exercise info editors_NEW --------------------

class _LinkSetButton(RoundPushButton):
    VALID_YT_URL_PREFIX = 'https://www.youtube.com/watch'
    BTTN_DEFAULT_TEXT = 'Set link'
    BTTN_SET_URL_TEXT = 'Set link(again)'

    def __init__(self, parent, obj_name, url=None, font_flag=FontFlag.NORMAL_TEXT):
        super().__init__(parent, obj_name, self.BTTN_DEFAULT_TEXT, font_flag=font_flag)
        # ----- Data -----
        self.url = url
        # ----- Connect events to slots -----
        self.clicked.connect(self._set_link_clicked)

    def _set_link_clicked(self):
        input_dialog = InputTextDialog(
            'Youtube video tutorial link', 'Insert youtube link(leave blank to remove): ',
            ImageFp.URL)
        accept = input_dialog.exec()
        if accept:
            url = get_value(input_dialog.line_input)
            if url and not url.startswith('https://www.youtube.com/watch'):
                # url set(len > 0) and is not valid
                ErrorMessage('Invalid youtube link',
                             'Provided link is not a valid youtube link\n'
                             f'NOTE: Link must start with '
                             f'"{self.VALID_YT_URL_PREFIX}"',).exec()
                return
            self.set_url(url)
            self.setText(self.BTTN_SET_URL_TEXT)

    def setVisible(self, visible):
        self.setText(self.BTTN_DEFAULT_TEXT)
        super().setVisible(visible)

    def set_url(self, url):
        self.url = None if url == '-' else url


class _InfoRowTitle(QtWidgets.QFrame):
    PADDING = 5

    def __init__(self, parent, obj_name, text):
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setContentsMargins(10, 10, 10, 0)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MAXIMUM)
        # ----- GUI children -----
        self.hbox_layout = None
        self.bttn_favorite = None
        self.title = None
        self.user_image = None
        # ----- Init UI -----
        self._init_ui(text)

    def _init_ui(self, text):
        self.bttn_favorite = CheckableImageButton(
            self, 'bttn_favorite', ImageFp.HEART, ImageFp.HEART_ALT,
            'Set as Favorite...', 'Favorite!')
        _view_widget_title = TitleLabel(
            self, 'label_title', text, bg_color=Colors.EXERCISE_TITLE.hex,
            text_color='black', font_flag=FontFlag.BIG_TITLE)
        _edit_widget_title = ValidatedLineEdit(
            self, 'edit_title', text, plan_name_valid,
            PLAN_NAME_CHECK_ERROR_MSG, bg_color=Colors.EXERCISE_TITLE.hex,
            border_radius=10, retain_msg_size=False,
            font_flag=FontFlag.BIG_TITLE_BOLD)
        self.title = ExerciseDataViewEditWidget(
            self, _view_widget_title, _edit_widget_title,
            cont_margins=(10, 5, 10, 5))
        self.user_image = Image(
            self, 'image_user', ImageFp.USER, tooltip='User exercise', visible=False)
        # ----- Set Layout -----
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.hbox_layout.addStretch(1)
        self.hbox_layout.addWidget(self.bttn_favorite)
        self.hbox_layout.addStretch(40)
        self.hbox_layout.addWidget(self.title)
        self.hbox_layout.addStretch(40)
        self.hbox_layout.addWidget(self.user_image)
        self.hbox_layout.setAlignment(self.bttn_favorite, AlignFlag.Left)
        self.hbox_layout.setAlignment(self.title, AlignFlag.Center)
        self.hbox_layout.setAlignment(self.user_image, AlignFlag.Right)
        self.setLayout(self.hbox_layout)

    def set_data(self, title_text, favorite, user_permission):
        self.bttn_favorite.setChecked(favorite)
        set_value(self.title, title_text)
        _image_user_visible = True if user_permission else False
        self.user_image.setVisible(_image_user_visible)


class InfoGrid(QtWidgets.QFrame):
    signal_muscle_group_text_changed = QtCore.pyqtSignal(int, bool)

    _init_attr_ = {
        'exercise_type': 'EXERCISE TYPE',
        'body_part': 'BODY PART',
        'main_mus_groups': 'MAIN MUSCLE GROUPS',
        'minor_mus_groups': 'MAIN MUSCLE GROUPS',
        'equipment': 'EQUIPMENT',
        'link': 'VIDEO LINK',
    }

    def __init__(self, parent, exercise_data):
        super().__init__(parent)
        # ----- Properties -----
        self.setObjectName('info_grid')
        # self.setStyleSheet("""
        #     InfoGrid {
        #         background-color: %s;
        #     }
        # """ % Colors.MAIN_WINDOW.hex)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(350)
        self.setSizePolicy(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM)
        # ----- Data -----
        self.edit_widgets = None
        self.exercise_data = exercise_data
        self.label_texts = AttrObject()
        for attr_name, attr in InfoGrid._init_attr_.items():
            setattr(self.label_texts, attr_name, attr.title())
        # ----- GUI children -----
        self.grid_layout = None
        self.title = None
        self.label_type = None
        self.label_type_value = None
        self.label_body_part = None
        self.label_body_part_value = None
        self.label_main_muscles = None
        self.label_main_muscles_value = None
        self.label_minor_muscles = None
        self.label_minor_muscles_value = None
        self.label_equipment = None
        self.label_equipment_value = None
        self.label_link = None
        self.label_link_value = None
        # Initialize UI
        self.init_ui(exercise_data)
        # Connect events to slots
        self.label_main_muscles_value.edit_widget.currentTextChanged.connect(partial(self.muscle_group_changed, True))
        self.label_minor_muscles_value.edit_widget.currentTextChanged.connect(partial(self.muscle_group_changed, False))

    def init_ui(self, exercise_data):
        # Init Layout
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setContentsMargins(10, 0, 10, 0)
        self.grid_layout.setVerticalSpacing(5)
        self.grid_layout.setHorizontalSpacing(0)
        self.grid_layout.setColumnStretch(0, 10)
        self.grid_layout.setColumnStretch(1, 8)
        # ----- Title -----
        self.title = TitleLabel(self, 'title', 'Exercise Info', round_bottom=False)
        # ----- 1st row -----
        self.label_type = InfoGridLabel(
            self, 'label_type', self.label_texts.exercise_type, ThemeType.DARK)
        _view_widget_type_value = InfoGridLabel(
            self, 'label_type_value', exercise_data.exer_type, ThemeType.GREEN)
        _id_name_dict = dict(DB().select_from_table('exercise_type', ('id', 'name')))
        _edit_widget_type_value = DBComboBox(
            self, 'cb_type', _id_name_dict, tooltip='Exercise type')
        self.label_type_value = ExerciseDataViewEditWidget(
            self, _view_widget_type_value, _edit_widget_type_value)

        # ----- 2nd row -----
        self.label_body_part = InfoGridLabel(
            self, 'label_body_part', self.label_texts.body_part, ThemeType.DARK)
        _view_widget_body_value = InfoGridLabel(
            self, 'label_body_value', exercise_data.body_part, ThemeType.GREEN)
        _id_name_dict = dict(DB().select_from_table('body_part', ('id', 'name')))
        _edit_widget_body_value = DBComboBox(
            self, 'cb_body_part', _id_name_dict, tooltip='Body part')
        self.label_body_part_value = ExerciseDataViewEditWidget(
            self, _view_widget_body_value, _edit_widget_body_value)

        # ----- 3rd row -----
        self.label_main_muscles = InfoGridLabel(
            self, 'label_main_muscles', self.label_texts.main_mus_groups, ThemeType.DARK)
        _view_widget_main_mus_value = InfoGridLabel(
            self, 'label_main_mus_value', exercise_data.main_muscle_group, ThemeType.GREEN)
        _id_name_dict = dict(DB().select_from_table('muscle_group', ('id', 'name')))
        _edit_widget_main_mus_value = DBComboBox(
            self, 'cb_main_mus', _id_name_dict, tooltip='Main muscle group')
        self.label_main_muscles_value = ExerciseDataViewEditWidget(
            self, _view_widget_main_mus_value, _edit_widget_main_mus_value)

        # 4th row
        self.label_minor_muscles = InfoGridLabel(
            self, 'label_minor_muscles', self.label_texts.minor_mus_groups, ThemeType.DARK)
        _view_widget_minor_mus_value = InfoGridLabel(
            self, 'label_minor_mus_value', exercise_data.minor_muscle_group, ThemeType.GREEN)
        _id_name_dict = dict(DB().select_from_table('muscle_group', ('id', 'name')))
        _edit_widget_minor_mus_value = DBComboBox(
            self, 'cb_minor_mus', _id_name_dict, first_item='-', tooltip='Minor muscle group')
        self.label_minor_muscles_value = ExerciseDataViewEditWidget(
            self, _view_widget_minor_mus_value, _edit_widget_minor_mus_value)

        # 5th row
        self.label_equipment = InfoGridLabel(
            self, 'label_equipment', self.label_texts.equipment, ThemeType.DARK)
        _view_widget_equipment = InfoGridLabel(
            self, 'label_equipment_value', exercise_data.equipment, ThemeType.GREEN)
        _id_name_dict = dict(DB().select_from_table('equipment', ('id', 'name')))
        _edit_widget_equipment = DBComboBox(
            self, 'cb_equipment', _id_name_dict, tooltip='Equipment')
        self.label_equipment_value = ExerciseDataViewEditWidget(
            self, _view_widget_equipment, _edit_widget_equipment)

        # 6th row
        self.label_link = InfoGridLabel(
            self, 'label_link', self.label_texts.link, ThemeType.DARK)
        _view_widget_link = LinkInfoGridLabel(
            self, 'label_link', exercise_data.link, ThemeType.GREEN)
        _edit_widget_link = _LinkSetButton(
            self, 'bttn_set_link', exercise_data.link)
        self.label_link_value = ExerciseDataViewEditWidget(
            self, _view_widget_link, _edit_widget_link)

        #
        self.edit_widgets = (
            self.label_type_value,
            self.label_body_part_value,
            self.label_main_muscles_value,
            self.label_minor_muscles_value,
            self.label_equipment_value,
            self.label_link_value
        )
        # Set layout
        self.grid_layout.addWidget(self.title, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.label_type, 1, 0)
        self.grid_layout.addWidget(self.label_type_value, 1, 1)
        self.grid_layout.addWidget(self.label_body_part, 2, 0)
        self.grid_layout.addWidget(self.label_body_part_value, 2, 1)

        self.grid_layout.addWidget(self.label_main_muscles, 3, 0)
        self.grid_layout.addWidget(self.label_main_muscles_value, 3, 1)

        self.grid_layout.addWidget(self.label_minor_muscles, 4, 0)
        self.grid_layout.addWidget(self.label_minor_muscles_value, 4, 1)

        self.grid_layout.addWidget(self.label_equipment, 5, 0)
        self.grid_layout.addWidget(self.label_equipment_value, 5, 1)

        self.grid_layout.addWidget(self.label_link, 6, 0)
        self.grid_layout.addWidget(self.label_link_value, 6, 1, 1, 1)

        self.setLayout(self.grid_layout)

    # SLOTS #

    def muscle_group_changed(self, is_main):
        cb = self.label_main_muscles_value.edit_widget if is_main else self.label_minor_muscles_value.edit_widget
        if get_value(cb) == '-':
            return
        muscle_group_id = cb.get_item_db_id()
        self.signal_muscle_group_text_changed.emit(muscle_group_id, is_main)


class _ExerciseBasicInfoGrid(InfoGrid):
    def __init__(self, parent, exercise_data):
        super().__init__(parent, exercise_data)

    def set_data(self, exercise_data):
        self.exercise_data = exercise_data
        self.label_type_value.set_data(exercise_data.exer_type)
        self.label_body_part_value.set_data(exercise_data.body_part)
        self.label_main_muscles_value.set_data(exercise_data.main_muscle_group)
        self.label_minor_muscles_value.set_data(exercise_data.minor_muscle_group)
        self.label_equipment_value.set_data(exercise_data.equipment)
        self.label_link_value.set_data(exercise_data.link)


class InfoRow(QtWidgets.QWidget):
    def __init__(self, parent, exercise_data, orientation=Orientation.HORIZONTAL):
        super().__init__(parent)
        self.setContentsMargins(5, 5, 5, 5)
        _size_policy = (SizePolicy.MINIMUM, SizePolicy.MAXIMUM) if orientation == Orientation.HORIZONTAL \
            else (SizePolicy.MAXIMUM, SizePolicy.MINIMUM)
        self.setSizePolicy(*_size_policy)
        # ----- Set Layout -----
        self.layout = None
        self.info_grid = None
        self.pos1_image_text = None
        self.pos2_image_text = None
        # ----- Init UI -----
        self._init_ui(exercise_data, orientation=orientation)

    def _init_ui(self, exercise_data, orientation=Orientation.HORIZONTAL):
        self.info_grid = _ExerciseBasicInfoGrid(self, exercise_data)
        _view_widget_pos1_image = ImageWithText(
            self, 'view_image_pos1', 'Position 1', exercise_data.pos1_image)
        _edit_widget_pos1_image = InputImageWithText(
            self, 'edit_image_pos1', 'Position 1', exercise_data.pos1_image, min_height=images.MIN_IMAGE_HEIGHT)
        self.pos1_image_text = ExerciseDataViewEditWidget(
            self, _view_widget_pos1_image, _edit_widget_pos1_image)
        _view_widget_pos2_image = ImageWithText(
            self, 'view_image_pos2', 'Position 2', exercise_data.pos2_image, hide_no_image=True)
        _edit_widget_pos2_image = InputImageWithText(
            self, 'edit:image_pos2', 'Position 2', exercise_data.pos2_image,
            create_bttn_delete=True, min_height=images.MIN_IMAGE_HEIGHT)
        self.pos2_image_text = ExerciseDataViewEditWidget(
            self, _view_widget_pos2_image, _edit_widget_pos2_image)
        _layout_type = QtWidgets.QHBoxLayout if orientation == Orientation.HORIZONTAL else \
            QtWidgets.QVBoxLayout
        self.layout = _layout_type(self)
        _align_flag = AlignFlag.Left | AlignFlag.Top if orientation == Orientation.HORIZONTAL \
            else AlignFlag.Top | AlignFlag.Center
        self.layout.setAlignment(_align_flag)
        self.layout.addWidget(self.info_grid)
        self.layout.addWidget(self.pos1_image_text)
        self.layout.addWidget(self.pos2_image_text)
        self.setLayout(self.layout)

    def set_data(self, exercise_data):
        self.info_grid.set_data(exercise_data)
        self.pos1_image_text.set_data(exercise_data.pos1_image)
        self.pos2_image_text.set_data(exercise_data.pos2_image)
        # pos2_visible = True if self.pos2_image_text.view_widget.image_set else False
        # self.pos2_image_text.setVisible(pos2_visible)

    def activate_view_mode(self, save=False):
        for edit_widget in self.info_grid.edit_widgets:
            edit_widget.activate_view_mode(save=save)
        self.pos1_image_text.activate_view_mode(save=save)
        self.pos2_image_text.activate_view_mode(save=save)

    def activate_edit_mode(self):
        for edit_widget in self.info_grid.edit_widgets:
            edit_widget.activate_edit_mode()
        self.pos1_image_text.activate_edit_mode()
        self.pos2_image_text.activate_edit_mode()


class ExerciseBasicInfoViewer(QtWidgets.QFrame):
    signal_favorite_changed = QtCore.pyqtSignal(int, bool)

    def __init__(self, parent):
        """

        :param parent:
        :param exercise_data: <int> Exercise id
        """
        super().__init__(parent)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MINIMUM)
        self.setStyleSheet('''
            .ExerciseBasicInfoViewer {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 10px;
            }
        ''' % (Colors.CONTAINER.hex, Colors.CONTAINER.hex))
        # Data
        self.exercise_data = ExerciseData.get_empty_exercise_data()
        # GUI children
        self.layout = None
        self.title_row = None
        self.row = None
        self.row_scroll_area = None
        self._init_ui()
        # Connect events to slots
        self.title_row.bttn_favorite.clicked.connect(self._favorite_changed)

    def _init_ui(self):
        self.title_row = _InfoRowTitle(self, 'title_row', self.exercise_data.name)
        self.row = InfoRow(self, self.exercise_data)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(self.title_row)
        self.vbox_layout.addWidget(self.row)
        self.setLayout(self.vbox_layout)

    def set_data(self, exer_id=None):
        self.exercise_data = DB().select_exercise_data(exer_id) if exer_id else \
            ExerciseData.get_empty_exercise_data()
        self.title_row.set_data(self.exercise_data.name, self.exercise_data.favorite,
                                self.exercise_data.user_permission)
        self.row.set_data(self.exercise_data)

    def activate_edit_mode(self):
        self.title_row.title.activate_edit_mode()
        self.row.activate_edit_mode()

    def activate_view_mode(self, save=False):
        self.title_row.title.activate_view_mode(save=save)
        self.row.activate_view_mode(save=save)

    def pos2_image_set(self):
        return self.row.pos2_image_text.edit_widget.image_with_text.image_set

    # SLOTS

    def _favorite_changed(self):
        favorite = True if self.sender().isChecked() else False
        favorite_int = 1 if favorite else 0
        updated = DB().update_table('exercises', {'favorite': favorite_int}, self.exercise_data.exer_id)
        if not updated:
            ErrorMessage('Set exercise favorite', 'Exercise couldn\'t be set as favorite').exec()


class _AdditionalInfoRow(QtWidgets.QFrame):
    def __init__(self, parent, exercise_data):
        super().__init__(parent)
        self.setStyleSheet('''
            ._AdditionalInfoRow {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 10px;
            }
        ''' % (Colors.CONTAINER.hex, Colors.CONTAINER.hex))
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        self.hbox_layout = None
        self.instructions = None
        self.muscle_diagram1 = None
        self.muscle_diagram2 = None
        self._init_ui(exercise_data)

    def _init_ui(self, exercise_data):
        self.instructions = TextBrowserEditor(self, 'browser', 'Instructions',
                                              exercise_data.instructions)
        self.muscle_diagram1 = ImageWithText(self, 'image_muscle1', 'Main muscle group',
                                             exercise_data.main_muscle_group_image)
        _visible = True if exercise_data.minor_muscle_group else False
        self.muscle_diagram2 = ImageWithText(self, 'image_muscle2', 'Minor muscle group',
                                             exercise_data.minor_muscle_group_image, visible=_visible,
                                             hide_no_image=True)
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setAlignment(AlignFlag.Left)
        self.hbox_layout.addWidget(self.instructions)
        self.hbox_layout.addWidget(self.muscle_diagram1)
        self.hbox_layout.addWidget(self.muscle_diagram2)
        self.setLayout(self.hbox_layout)

    def set_data(self, exercise_data):
        set_value(self.instructions, exercise_data.instructions)
        set_value(self.muscle_diagram1, exercise_data.main_muscle_group_image)
        set_value(self.muscle_diagram2, exercise_data.minor_muscle_group_image)
        mus_diag2_visible = True if exercise_data.minor_muscle_group_image else False
        self.muscle_diagram2.setVisible(mus_diag2_visible)


class ExerciseDataViewer(QtWidgets.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        self.setObjectName('exercise_data_viewer')
        # Data
        self.exercise_data = ExerciseData.get_empty_exercise_data()
        self.edit_mode = False
        self.info_dialog = None
        # Gui elements
        self.vbox_layout = None
        self.basic_info_row = None
        self.additional_info_row = None
        # Initialize GUI
        self.init_ui()
        # Connect events to slots
        self.basic_info_row.row.info_grid.signal_muscle_group_text_changed.connect(self.change_muscle_group_image)

    def init_ui(self):
        self.basic_info_row = ExerciseBasicInfoViewer(self)
        self.additional_info_row = _AdditionalInfoRow(self, self.exercise_data)
        # Layout
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(self.basic_info_row)
        self.vbox_layout.addWidget(self.additional_info_row)
        self.setLayout(self.vbox_layout)

    def change_muscle_group_image(self, table_id, is_main):
        """Retrieves new main muscle group image from DB table 'muscle_group'
        and sets it in additional exercise data row.

        :param table_id <int> DB column 'id' value from table 'muscle_group'
        :param is_main <bool> True -> Main muscle diagram, False -> Minor muslce diagram
        :return None
        """
        image_diagram = self.additional_info_row.muscle_diagram1 if is_main else \
            self.additional_info_row.muscle_diagram2
        main_muscle_img_bytes = DB().select_from_table('muscle_group', 'image', {'id': table_id})
        image_diagram.set_data(main_muscle_img_bytes)

    def update_exercise(self):
        info_grid = self.basic_info_row.row.info_grid  # just for shorter path
        _pos2_image_set = self.basic_info_row.row.pos2_image_text.edit_widget.image_with_text.image_set
        exer_db_col_values_dict = {
            'name': get_value(self.basic_info_row.title_row.title),
            'type_id': info_grid.label_type_value.edit_widget.get_item_db_id(),
            'body_part_id': info_grid.label_body_part_value.edit_widget.get_item_db_id(),
            'main_muscle_group_id': info_grid.label_main_muscles_value.edit_widget.get_item_db_id(),
            'minor_muscle_group_id': info_grid.label_minor_muscles_value.edit_widget.get_item_db_id(),
            'equipment_id': info_grid.label_equipment_value.edit_widget.get_item_db_id(),
            'position_1': get_value(self.basic_info_row.row.pos1_image_text),
            'position_2': get_value(self.basic_info_row.row.pos2_image_text) if _pos2_image_set else None,
            'instructions': get_value(self.additional_info_row.instructions),
        }
        updated = DB().update_exercise(self.exercise_data.exer_id, exer_db_col_values_dict)
        if not updated:
            ErrorMessage('Edit Exercise failed', 'Couldn\'t update exercise').exec()
            return
        self.info_dialog = InfoMessage('Exercise updated', 'Exercise was updated')
        self.info_dialog.exec()
        self.info_dialog = None

    def set_data(self, exer_id=None):
        self.exercise_data = DB().select_exercise_data(exer_id) if exer_id else \
            ExerciseData.get_empty_exercise_data()
        self.basic_info_row.set_data(exer_id)
        self.additional_info_row.set_data(self.exercise_data)

    def activate_edit_mode(self):
        self.basic_info_row.activate_edit_mode()
        if self.exercise_data.user_permission:
            self.additional_info_row.instructions.activate_edit_mode()

    def activate_view_mode(self, save=False):
        self.basic_info_row.activate_view_mode(save=save)
        if self.exercise_data.user_permission:
            self.additional_info_row.instructions.activate_view_mode(save=save)
