import os
import subprocess
from pathlib import Path
from enum import Enum
from functools import partial

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from config import APP_NAME, SRC_DIR, BOOKMARKS_FILE, APP_MODE, VERSION
from settings import Settings, ICON_SIZES, EXER_PER_PAGE, DEFAULT_PROPERTIES
from session import Session
from export.pdf import create_plan_pdf
from export.motfile import export_plan, export_workout
from web.mail import send_email, EMailType
from util.value import shorten_text
from util.exception import log_and_show_method_exception, ExceptionWithMsg
from .tabs import TabExercises, TabPlanner, TabWorkouts, TabPlans
from .widgets import (
    MyComboBox, MyLabel, HLine, RadiobuttonBox, TabWidgetButton,
    ImageButton, CheckBox, TextEdit, RoundPushButton, HBoxPane,
    DialogButtonBox, LineEdit, DropFileRoundPushButton,
    ValidatedLineEdit, CrashReportErrorMessage, ExerciseListView
)
from .dialogs import (
    ErrorMessage, InfoMessage, QuestionDialog, get_folderpath_from_dialog, BaseDialog,
    get_filepath_from_dialog,
)
from .util import find_button_by_text, get_value, set_value
from .font import Font, FontFlag
from .colors import Colors
from .flags import ImageFp, SizePolicy, AlignFlag, LayoutOrientation, ExitCode


class TabIndex(Enum):
    EXERCISES = 0
    PLANNER = 1
    WORKOUTS = 2
    PLANS = 3


class _PlanPdfSettingsDialog(BaseDialog):
    """Dialog for collecting PDF settings before creating plan PDF file

    The PDF settings are:
        - create title option
        - choose between views:
            -> "Workout view":
            -> "Days view"(if checked, additional option to create rest days)
        - create YouTube video links
    """

    def __init__(self):
        super().__init__('Create pdf plan settings', icon_fp=ImageFp.PLAN_PDF)
        # ----- GUI children -----
        # ----- 1st row -----
        self.checkbox_create_title = CheckBox(
            self, 'checkbox_title', text='Create title', checked=True,
            direction=QtCore.Qt.LayoutDirection.LeftToRight)
        self.hline1 = HLine(self)
        # ----- 2nd row -----
        self.label_view_type = MyLabel(self, 'label', 'Choose plan PDF view type:')
        rb_box_data = (('workout_view', 'Workout view'), ('days_view', 'Days view'))
        self.rb_box_view_type = RadiobuttonBox(
            self, 'rb_box', rb_box_data, orientation=LayoutOrientation.HORIZONTAL)
        self.checkbox_rest_days = CheckBox(
            self, 'checkbox_rest', text='Create REST days',
            direction=QtCore.Qt.LayoutDirection.LeftToRight, enabled=False)
        self.hline2 = HLine(self)
        # ----- 3rd row -----
        # self.label_create_youtube_links = MyLabel(self, 'label', 'Create YouTube video links')
        self.checkbox_links = CheckBox(
            self, 'checkbox_links', text='Create YouTube video links',
            direction=QtCore.Qt.LayoutDirection.LeftToRight, checked=True)
        self.hline3 = HLine(self)
        # ----- 4th row -----
        self.button_box = DialogButtonBox(self, 'Create plan PDF', bttn_reject_text='Cancel')
        self.button_box.signal_accepted.connect(self.accept)
        self.button_box.signal_rejected.connect(self.reject)
        # ----- Set layout -----
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setVerticalSpacing(30)
        self.grid_layout.setSpacing(10)
        self.grid_layout.addWidget(self.checkbox_create_title, 0, 0)
        self.grid_layout.addWidget(self.hline1, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.label_view_type, 2, 0)
        self.grid_layout.addWidget(self.rb_box_view_type, 2, 1)
        self.grid_layout.addWidget(self.checkbox_rest_days, 3, 1)
        self.grid_layout.setAlignment(self.checkbox_rest_days, AlignFlag.Right)
        self.grid_layout.addWidget(self.hline2, 4, 0, 1, 2)
        self.grid_layout.addWidget(self.checkbox_links, 5, 0)
        self.grid_layout.addWidget(self.hline3, 6, 0, 1, 2)
        self.grid_layout.addWidget(self.button_box, 7, 1)
        self.setLayout(self.grid_layout)
        # ----- Connect events to slots -----
        self.rb_box_view_type.signal_rb_clicked.connect(self._view_type_clicked)

    def get_pdf_settings(self):
        """Executes this dialog and returns pdf settings(if they are accepted)

        :return <dict> Pdf settings as a dict
        """
        pdf_settings = self.exec()
        if pdf_settings:
            _view_type = self.rb_box_view_type.checked_value
            pdf_settings = {
                'title': self.checkbox_create_title.isChecked(),
                'view_type': _view_type
            }
            if _view_type == 'days_view':
                pdf_settings['rest_days'] = self.checkbox_rest_days.isChecked()
            pdf_settings['links'] = self.checkbox_links.isChecked()
            return pdf_settings
        return False

    def _view_type_clicked(self):
        chechbox_enabled = True if self.rb_box_view_type.checked_value == 'days_view' else False
        self.checkbox_rest_days.setEnabled(chechbox_enabled)


class _SettingsDialog(BaseDialog):
    """Dialog for setting Motus App settings:

    The Motus App settings are:
        - start display(after app run)
        - font
        - icon size(in list 'Exercises' and workout tables)
        - option to load last opened plan(in tab Planner)
        - exercises per page(in list 'Exercises'
        - PDF files folderpath
        - motfiles('*.motwork', '*.motplan') folderpath
    """

    signal_change_font = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__('Settings', icon_fp=ImageFp.SETTINGS)
        self.setContentsMargins(10, 10, 10, 0)
        self.setFixedWidth(700)
        # ----- Data -----
        self.settings = Settings()
        self.active_values = {}
        self.restart_after = False
        # ----- GUI children -----
        self.vbox_layout = None
        self.label_cb_display = None
        self.cb_display = None
        self.hor_line_1 = None
        self.label_fonts = None
        self.cb_font = None
        self.example_text = None
        self.hor_line_2 = None
        self.label_icon_size = None
        self.rb_box_icon_sizes = None
        self.hor_line_3 = None
        self.checkbox_reload_plan = None
        self.hor_line_4 = None
        self.label_exer_per_page = None
        self.cb_exer_per_page = None
        self.hor_line_5 = None
        self.label_pdfs = None
        self.edit_line_pdf_folderpath = None
        self.bttn_set_pdf_folderpath = None
        self.hor_line_6 = None
        self.label_motfiles = None
        self.edit_line_motfiles_folderpath = None
        self.bttn_set_motfiles_folderpath = None
        self.hor_line_7 = None
        self.bttn_reset_to_default = None
        self.button_box = None
        # ----- Initialize UI -----
        self._init_ui()
        # ----- Connect events to slots -----
        self.cb_display.currentIndexChanged.connect(self._value_changed)
        self.cb_font.currentIndexChanged.connect(self._value_changed)
        self.cb_font.currentIndexChanged.connect(self._font_changed)
        self.rb_box_icon_sizes.signal_rb_clicked.connect(self._value_changed)
        self.checkbox_reload_plan.clicked.connect(self._value_changed)
        self.cb_exer_per_page.currentTextChanged.connect(self._value_changed)
        self.edit_line_pdf_folderpath.signal_text_changed.connect(self._value_changed)
        self.edit_line_motfiles_folderpath.signal_text_changed.connect(self._value_changed)
        self.bttn_set_pdf_folderpath.clicked.connect(self._set_pdf_folderpath)
        self.bttn_set_motfiles_folderpath.clicked.connect(self._set_motfiles_folderpath)
        self.bttn_reset_to_default.clicked.connect(self._reset_to_default)
        self.button_box.signal_accepted.connect(self.accept)
        self.button_box.signal_rejected.connect(self.reject)
        # ----- Post init actions: remember active settings -----
        self.active_values['main_display'] = get_value(self.cb_display)
        self.active_values['font_family'] = get_value(self.cb_font)
        self.active_values['icon_size'] = get_value(self.rb_box_icon_sizes)
        self.active_values['reload_plan'] = get_value(self.checkbox_reload_plan)
        self.active_values['exer_per_page'] = get_value(self.cb_exer_per_page)
        self.active_values['pdf_folderpath'] = get_value(self.edit_line_pdf_folderpath)
        self.active_values['motfiles_folderpath'] = get_value(self.edit_line_motfiles_folderpath)

    def _init_ui(self):
        # ----- Row 1: Choose start display -----
        self.label_cb_display = MyLabel(self, 'label_display', 'Start display:')
        self.cb_display = MyComboBox(self, 'cb_displays', items=self.settings.get_available_displays())
        cb_curr_index = int(self.settings.getValue('main_display')[-1]) - 1
        self.cb_display.setCurrentIndex(cb_curr_index)
        self.hor_line_1 = HLine(self)
        # ----- Row 2: Choose font -----
        self.label_fonts = MyLabel(self, 'label_fonts', 'Font:')
        font_items = ['Recommended fonts'] + Font.PREFFERED_FONTS + \
                     ['-' * 30] + Font.get_font_families()
        self.cb_font = MyComboBox(self, 'cb_fonts', items=font_items)
        self.cb_font.setCurrentIndex(1)
        self.cb_font.model().item(0).setEnabled(False)
        self.cb_font.model().item(len(Font.PREFFERED_FONTS) + 1).setEnabled(False)
        self.cb_font.setCurrentText(Settings().getValue('font_family'))
        _example_text = 'This is an example text...'
        self.example_text = MyLabel(
            self, 'example_text', _example_text, font_flag=FontFlag.BIG_TEXT,
            align_flag=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.example_text.setStyleSheet("""
            border: 1px solid black;
            border-radius: 3px;
            background-color: white;
        """)
        self.hor_line_2 = HLine(self)
        # ----- Row 3: Choose icon size -----
        self.label_icon_size = MyLabel(self, 'label_icon_sizes', 'Icon size(pixels):')
        checked_rb_index = None
        rb_data = []
        for i, icon_size in enumerate(ICON_SIZES):
            if icon_size == self.settings.getValue('icon_size'):
                checked_rb_index = i
            rb_text = f'{icon_size[0]}x{icon_size[1]}'
            rb_data.append((icon_size, rb_text))
        self.rb_box_icon_sizes = RadiobuttonBox(
            self, 'rb_box', rb_data, checked_rb_index=checked_rb_index)
        self.hor_line_3 = HLine(self)
        # ----- Row 4: Option remember opened planner plan -----
        _checked = Settings().getValue('reload_plan')
        self.checkbox_reload_plan = CheckBox(
            self, 'checkbox', '(On startup) Load last opened plan', checked=_checked)
        self.checkbox_reload_plan.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.hor_line_4 = HLine(self)
        # ----- Row 5: Set exercises per page in Exercise List -----
        self.label_exer_per_page = MyLabel(
            self, 'label', 'Exercises per page(in Exercise list): ')
        self.cb_exer_per_page = MyComboBox(self, 'cb', EXER_PER_PAGE, size=(50, None))
        current_text = str(Settings().getValue('exer_per_page'))
        set_value(self.cb_exer_per_page, current_text)
        self.hor_line_5 = HLine(self)
        # ----- Row 6: Set pdf exports folderpath -----
        self.label_pdfs = MyLabel(self, 'label', 'PDF folder path:')
        self.edit_line_pdf_folderpath = ValidatedLineEdit(
            self, 'pdf_fp', Settings().getValue('pdf_folderpath'),
            lambda fp: Path(fp).is_dir(), f'Folder path doesn\'t exist',
            retain_msg_size=False, font_flag=FontFlag.SMALL_TEXT)
        self.bttn_set_pdf_folderpath = ImageButton(
            self, 'bttn', ImageFp.FOLDER, 'Set PDF folder')
        cell_set_pdf_folderpath = HBoxPane(
            self, (self.edit_line_pdf_folderpath, self.bttn_set_pdf_folderpath),
            cont_margins=(0, 0, 0, 0))
        self.hor_line_6 = HLine(self)
        # ----- Row 7: Set motfile exports folderpath -----
        self.label_motfiles = MyLabel(self, 'label', 'Motfiles folder path:')
        self.edit_line_motfiles_folderpath = ValidatedLineEdit(
            self, 'motfiles_fp', Settings().getValue('motfiles_folderpath'),
            lambda fp: Path(fp).is_dir(), 'Folder path doesnt exist',
            retain_msg_size=False, font_flag=FontFlag.SMALL_TEXT)
        self.bttn_set_motfiles_folderpath = ImageButton(
            self, 'bttn', ImageFp.FOLDER, 'Set motfiles folder')
        cell_set_motfiles_folderpath = HBoxPane(
            self, (self.edit_line_motfiles_folderpath, self.bttn_set_motfiles_folderpath),
            cont_margins=(0, 0, 0, 0))
        self.hor_line_7 = HLine(self)
        # ----- Row 8: Dialog buttons -----
        self.bttn_reset_to_default = RoundPushButton(self, 'bttn', 'Reset to default')
        self.button_box = DialogButtonBox(
            self, 'OK', bttn_reject_text='Cancel',
            bttn_action_dict={'Apply': self._apply_settings})
        self.button_box.bttn_action.setEnabled(False)
        # ----- Set layout -----
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setColumnStretch(0, 2)
        self.grid_layout.setColumnStretch(1, 3)
        self.grid_layout.addWidget(self.label_cb_display, 0, 0)
        self.grid_layout.addWidget(self.cb_display, 0, 1)
        self.grid_layout.addWidget(self.hor_line_1, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.label_fonts, 2, 0)
        self.grid_layout.addWidget(self.cb_font, 2, 1)
        self.grid_layout.addWidget(self.example_text, 3, 1)
        self.grid_layout.addWidget(self.hor_line_2, 4, 0, 1, 2)
        self.grid_layout.addWidget(self.label_icon_size, 5, 0)
        self.grid_layout.addWidget(self.rb_box_icon_sizes, 5, 1)
        self.grid_layout.addWidget(self.hor_line_3, 6, 0, 1, 2)
        self.grid_layout.addWidget(self.checkbox_reload_plan, 7, 0)
        self.grid_layout.addWidget(self.hor_line_4, 8, 0, 1, 2)
        self.grid_layout.addWidget(self.label_exer_per_page, 9, 0)
        self.grid_layout.addWidget(self.cb_exer_per_page, 9, 1)
        self.grid_layout.addWidget(self.hor_line_5, 10, 0, 1, 2)
        self.grid_layout.addWidget(self.label_pdfs, 11, 0)
        self.grid_layout.addWidget(cell_set_pdf_folderpath, 11, 1)
        self.grid_layout.addWidget(self.hor_line_6, 12, 0, 1, 2)
        self.grid_layout.addWidget(self.label_motfiles, 13, 0)
        self.grid_layout.addWidget(cell_set_motfiles_folderpath, 13, 1)
        self.grid_layout.addWidget(self.hor_line_7, 14, 0, 1, 2)
        self.grid_layout.addWidget(self.bttn_reset_to_default, 15, 0)
        self.grid_layout.addWidget(self.button_box, 15, 1)
        self.setLayout(self.grid_layout)

    def open_settings(self):
        """Opens dialog and after its closed applies new settings(if needed)
        and restarts App(if needed)

        :return <bool> Restart app or not
        """
        apply = self.exec()
        if apply:
            self._apply_settings()
        if self.restart_after:
            _msg = 'App restart needed for changed settings to be viewed.\n' \
                   'Do you want to restart App now?'
            pos = self.pos()
            restart = QuestionDialog('Restart needed for changes', _msg,
                                     parent_pos=pos).exec()
            return restart
        return False

    # ----- SLOTS -----

    def _apply_settings(self):
        """Slot for button 'Apply' click event.

        This method:
            - applies settings and resets active values, for settings that were changed
            - sets attr 'restart_after' as 'True' if icon size or exercises per page are changed
            - disables button 'Apply'

        :return <None>
        """
        chosen_display = self.cb_display.currentText()
        chosen_font_family = get_value(self.cb_font)
        chosen_icon_size = get_value(self.rb_box_icon_sizes)
        chosen_reload_plan = get_value(self.checkbox_reload_plan)
        chosen_exer_per_page = get_value(self.cb_exer_per_page)
        chosen_pdf_folderpath = get_value(self.edit_line_pdf_folderpath)
        chosen_motfiles_folderpath = get_value(self.edit_line_motfiles_folderpath)
        if chosen_display != self.active_values['main_display']:
            self.settings.setValue('main_display', chosen_display.split('(')[0])
            self.active_values['main_display'] = chosen_display
        if chosen_font_family != self.active_values['font_family']:
            self.settings.setValue('font_family', chosen_font_family)
            self.active_values['font_family'] = chosen_font_family
            self.signal_change_font.emit(chosen_font_family)
        if chosen_icon_size != self.active_values['icon_size']:
            self.settings.setValue('icon_size', chosen_icon_size)
            self.active_values['rb_box'] = chosen_icon_size
            self.restart_after = True
        if chosen_reload_plan != self.active_values['reload_plan']:
            self.settings.setValue('reload_plan', chosen_reload_plan)
            self.active_values['reload_plan'] = chosen_reload_plan
        if chosen_exer_per_page != self.active_values['exer_per_page']:
            self.settings.setValue('exer_per_page', chosen_exer_per_page)
            self.active_values['exer_per_page'] = chosen_exer_per_page
            self.restart_after = True
        if chosen_pdf_folderpath != self.active_values['pdf_folderpath']:
            self.settings.setValue('pdf_folderpath', chosen_pdf_folderpath)
            self.active_values['pdf_folderpath'] = chosen_pdf_folderpath
        if chosen_motfiles_folderpath != self.active_values['motfiles_folderpath']:
            self.settings.setValue('motfiles_folderpath', chosen_motfiles_folderpath)
            self.active_values['motfiles_folderpath'] = chosen_motfiles_folderpath
        self.button_box.bttn_action.setEnabled(False)

    def _font_changed(self):
        """Slot for combobox 'Font' item change event.

        This method changes the example text below the combobox.

        :return <None>
        """
        new_font = QtGui.QFont(self.cb_font.currentText(), 10)
        self.example_text.setFont(new_font)

    def _set_pdf_folderpath(self):
        """Slot for button 'Set PDF folder' click event.

        This method opens the folder dialog and sets it(if it is given)

        :return <None>
        """
        pdf_folderpath = get_folderpath_from_dialog(self)
        if pdf_folderpath:
            pdf_folderpath = os.path.normpath(pdf_folderpath)
            set_value(self.edit_line_pdf_folderpath, pdf_folderpath)

    def _set_motfiles_folderpath(self):
        """Slot for button 'Set motfiles folder' click event.

        This method opens the folder dialog and sets it(if it is given)

        :return <None>
        """
        motfiles_folderpath = get_folderpath_from_dialog(self)
        if motfiles_folderpath:
            motfiles_folderpath = os.path.normpath(motfiles_folderpath)
            set_value(self.edit_line_motfiles_folderpath, motfiles_folderpath)

    def _value_changed(self):
        """Slot for any value change in widgets for settings values

        This method enables button 'Apply' if any changed settings value is not
        set as active. Otherwise, disables the button.

        :return <None>
        """
        active_chosen_value_pairs = [
            (self.active_values['main_display'], get_value(self.cb_display)),
            (self.active_values['font_family'], get_value(self.cb_font)),
            (self.active_values['icon_size'], get_value(self.rb_box_icon_sizes)),
            (self.active_values['reload_plan'], get_value(self.checkbox_reload_plan)),
            (self.active_values['exer_per_page'], get_value(self.cb_exer_per_page)),
            (self.active_values['pdf_folderpath'], get_value(self.edit_line_pdf_folderpath)),
            (self.active_values['motfiles_folderpath'], get_value(self.edit_line_motfiles_folderpath)),
        ]
        if any(act_val != ch_val for act_val, ch_val in active_chosen_value_pairs):
            self.button_box.bttn_action.setEnabled(True)
        else:
            self.button_box.bttn_action.setEnabled(False)

    def _reset_to_default(self):
        """Slot for button 'Reset to default' click event.

        This method resets all values of settings widgets to default values

        :return <None>
        """
        _display1 = Settings().get_available_displays()[0]
        set_value(self.cb_display, _display1)
        set_value(self.cb_font, DEFAULT_PROPERTIES['font_family'])
        set_value(self.rb_box_icon_sizes, DEFAULT_PROPERTIES['icon_size'])
        set_value(self.checkbox_reload_plan, DEFAULT_PROPERTIES['reload_plan'])
        set_value(self.cb_exer_per_page, DEFAULT_PROPERTIES['exer_per_page'])
        set_value(self.edit_line_pdf_folderpath,
                  DEFAULT_PROPERTIES['pdf_folderpath'])
        set_value(self.edit_line_motfiles_folderpath,
                  DEFAULT_PROPERTIES['motfiles_folderpath'])


class _FeedbackDialog(BaseDialog):
    """Dialog for sending feedback e-mail to Motus App developers

    There are 2 types of feedbacks:
        - 'Defect', for app bugs
        - 'Enhancement', for app suggestions and improvements
    Besides the issue text, the feedback can include a response e-mail
    and an attachmed image.
    """

    def __init__(self):
        super().__init__('Send feedback', icon_fp=ImageFp.MOTUS_ICON)
        self.setFixedWidth(500)
        self.setFixedHeight(500)
        self.setContentsMargins(10, 10, 10, 10)
        # ----- Data ----
        self.attached_file = None
        # ----- GUI children -----
        self.grid_layout = None
        self.label_feedback_type = None
        self.rb_box_feedback_type = None
        self.label_description = None
        self.text_edit = None
        self.label_additional_info = None
        self.label_email = None
        self.email_line_edit = None
        self.bttn_attach_file = None
        self.label_attach_file = None
        self.bttn_delete_attach = None
        self.button_box = None
        # ----- Initialize UI -----
        self._init_ui()
        # ----- Connect events to slots -----
        self.bttn_attach_file.clicked.connect(self._choose_file)
        self.button_box.signal_accepted.connect(self._send_feedback)
        self.button_box.signal_rejected.connect(self._rejected)
        self.bttn_attach_file.signal_file_dropped.connect(self._file_dropped)
        self.bttn_delete_attach.clicked.connect(self._delete_attached_file_clicked)

    def _init_ui(self):
        # ----- Feedback type -----
        self.label_feedback_type = MyLabel(
            self, 'label', 'Feedback type: ', font_flag=FontFlag.NORMAL_TEXT_BOLD)
        _rb_box_data = ((EMailType.DEFECT, 'Defect'), (EMailType.ENHANCEMENT, 'Enhancement'))
        self.rb_box_feedback_type = RadiobuttonBox(
            self, 'rb_box', _rb_box_data, orientation=LayoutOrientation.HORIZONTAL)
        # ----- Description label and text area -----
        self.label_description = MyLabel(
            self, 'label', 'Describe the issue', font_flag=FontFlag.NORMAL_TEXT_BOLD,
            cont_margins=(5, 10, 5, 10))
        self.text_edit = TextEdit(self, 'description', '')
        # ----- Additional info -----
        self.label_additional_info = MyLabel(
            self, 'label', 'Additional info(optional)', font_flag=FontFlag.NORMAL_TEXT_BOLD,
            cont_margins=(5, 10, 5, 10))
        self.label_email = MyLabel(
            self, 'label', 'Response e-mail', font_flag=FontFlag.SMALL_TEXT,
            align_flag=AlignFlag.VCenter, cont_margins=(20, 0, 0, 0))
        self.email_line_edit = LineEdit(self, 'line_edit', '', place_holder_text='input email...')
        self.label_attach_file = MyLabel(
            self, 'label', 'Attach a file', font_flag=FontFlag.SMALL_TEXT,
            align_flag=AlignFlag.VCenter, cont_margins=(20, 0, 0, 0))
        self.bttn_attach_file = DropFileRoundPushButton(
            self, 'bttn', 'Choose file', ('jpg', 'jpeg', 'png'))
        self.label_attached_file = MyLabel(
            self, 'label', '<i>No file choosen</i>', font_flag=FontFlag.SMALL_TEXT,
            align_flag=AlignFlag.VCenter)
        self.bttn_delete_attach = ImageButton(self, 'bttn_del', ImageFp.DELETE_SMALL,
                                              'Delete attached file', enabled=False)
        attach_file_row = HBoxPane(
            self, (self.bttn_attach_file, self.label_attached_file, self.bttn_delete_attach))
        self.button_box = DialogButtonBox(self, 'Send', bttn_reject_text='Cancel')
        # ----- Set Layout -----
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 2)
        self.grid_layout.addWidget(self.label_feedback_type, 0, 0)
        self.grid_layout.addWidget(self.rb_box_feedback_type, 0, 1)
        self.grid_layout.addWidget(self.label_description, 1, 0)
        self.grid_layout.addWidget(self.text_edit, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.label_additional_info, 3, 0, 1, 2)
        self.grid_layout.addWidget(self.label_email, 4, 0)
        self.grid_layout.addWidget(self.email_line_edit, 4, 1)
        self.grid_layout.addWidget(self.label_attach_file, 5, 0)
        self.grid_layout.addWidget(attach_file_row, 5, 1)
        self.grid_layout.addWidget(self.button_box, 6, 1)
        self.setLayout(self.grid_layout)

    def _send_feedback(self):
        """Slot for button 'Send' click event.

        This method checks if text is given, collects response e-mail and attached
        image(if they exist) and sends the e-mail.

        :return <None>
        """
        description = get_value(self.text_edit)
        if not description:
            ErrorMessage('Send feedback failed', 'There is no description').exec()
            return
        email_type = self.rb_box_feedback_type.checked_value
        response_email = get_value(self.email_line_edit)
        if response_email:
            description += f'\n\nResponse e-mail: {response_email}'
        send = send_email(email_type, description, attachment_fp=self.attached_file)
        if send:
            InfoMessage('Feedback sent', 'E-mail sent to Motus developers').exec()
            self.close()

    def _rejected(self):
        """Slot for button 'Cancel' click event.

        This method closes the dialog.

        :return <None>
        """
        self.close()

    def _choose_file(self):
        """Slot for button 'Choose file' click event.

        This method open the file dialog, and if the filepath is given,
        sets it in the label widget and enables the 'Delete attached file'
        button.

        :return <None>
        """
        fp = get_filepath_from_dialog(
            self, title='Choose file from PC',
            file_types='Files (*.jpg *.jpeg *.png)')
        if fp:
            self.attached_file = fp
            label_filename_text = shorten_text(Path(fp).name, 40)
            self.label_attached_file.setText(label_filename_text)
            self.bttn_delete_attach.setEnabled(True)

    def _file_dropped(self, fp):
        """Slot for button 'Choose file' file drop event.

        This method sets the dropped filepath in the label widget and
        enables the 'Delete attached file' button.

        :return <None>
        """
        self.attached_file = fp
        label_filename_text = shorten_text(Path(fp).name, 40)
        self.label_attached_file.setText(label_filename_text)
        self.bttn_delete_attach.setEnabled(True)

    def _delete_attached_file_clicked(self):
        """Slot for button 'Delete attached file' click event.

        This method resets the attached filepath and disables the
        'Delete attached file' button.

        :return <None>
        """
        set_value(self.label_attached_file, '<i>No file choosen</i>')
        self.attached_file = None
        self.bttn_delete_attach.setEnabled(False)


class _TabBar(QtWidgets.QWidget):
    """This class, with class '_TabArea', simulates a custom 'TabWidget'

    This class acts only as a container for the buttons and has no
    significant methods.
    """

    signal_change_tab = QtCore.pyqtSignal(TabIndex)
    signal_restart = QtCore.pyqtSignal()
    signal_shutdown = QtCore.pyqtSignal()
    signal_open_pdf_folder = QtCore.pyqtSignal()
    signal_open_motfiles_folder = QtCore.pyqtSignal()
    signal_send_feedback = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        # ----- GUI children ------
        self.vbox_layout = None
        self.bttn_exercises = None
        self.bttn_planner = None
        self.bttn_workouts = None
        self.bttn_plans = None
        self.bttn_about = None
        self.bttn_settings = None
        self.bttn_menu = None
        self.bttn_shutdown = None
        # ----- Initialize UI -----
        self._init_ui()
        # ----- Connect events to slots -----
        self.bttn_exercises.clicked.connect(partial(self._tab_bttn_clicked, TabIndex.EXERCISES))
        self.bttn_planner.clicked.connect(partial(self._tab_bttn_clicked, TabIndex.PLANNER))
        self.bttn_workouts.clicked.connect(partial(self._tab_bttn_clicked, TabIndex.WORKOUTS))
        self.bttn_plans.clicked.connect(partial(self._tab_bttn_clicked, TabIndex.PLANS))

    def _init_ui(self):
        self.bttn_exercises = TabWidgetButton(self, 'bttn_exercises', ImageFp.EXERCISES,
                                              'Exercises', TabIndex.EXERCISES)
        self.bttn_planner = TabWidgetButton(self, 'bttn_planner', ImageFp.PLANNER,
                                            'Planner', TabIndex.PLANNER)
        self.bttn_workouts = TabWidgetButton(self, 'bttn_workouts', ImageFp.WORKOUTS,
                                             'Workouts', TabIndex.WORKOUTS)
        self.bttn_plans = TabWidgetButton(self, 'bttn_plans', ImageFp.PLANS, 'Plans',
                                          TabIndex.PLANS)
        self.bttn_options = ImageButton(self, 'bttn_options', ImageFp.OPTIONS, 'Options')
        self.bttn_about = ImageButton(self, 'bttn_about', ImageFp.ABOUT, 'About')
        self.bttn_settings = ImageButton(self, 'bttn_settings', ImageFp.SETTINGS, 'Settings')
        self.bttn_shutdown = ImageButton(self, 'bttn_shutdown', ImageFp.SHUTDOWN, 'Shutdown/Restart App')
        # ----- Options menu -----
        options_menu = QtWidgets.QMenu()
        options_menu.addAction(QtGui.QIcon(ImageFp.FOLDER), 'Open PDF files folder',
                               lambda: self.signal_open_pdf_folder.emit())
        options_menu.addAction(QtGui.QIcon(ImageFp.FOLDER), 'Open MOT files folder',
                               lambda: self.signal_open_motfiles_folder.emit())
        options_menu.addAction(QtGui.QIcon(ImageFp.FEEDBACK), 'Send feedback',
                               lambda: self.signal_send_feedback.emit())
        self.bttn_options.setMenu(options_menu)
        # ----- Shutdown/restart menu -----
        shutdown_menu = QtWidgets.QMenu()
        shutdown_menu.addAction(QtGui.QIcon(ImageFp.RESTART), 'Restart',
                                lambda: self.signal_restart.emit())
        shutdown_menu.addAction(QtGui.QIcon(ImageFp.SHUTDOWN_SMALL), 'Shutdown',
                                lambda: self.signal_shutdown.emit())
        self.bttn_shutdown.setMenu(shutdown_menu)
        # ----- Set layout -----
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        for bttn in (self.bttn_exercises, self.bttn_planner, self.bttn_workouts, self.bttn_plans):
            self.vbox_layout.addWidget(bttn)
            self.vbox_layout.setAlignment(bttn, QtCore.Qt.AlignmentFlag.AlignTop)
            self.vbox_layout.addStretch(1)
        self.vbox_layout.addStretch(10)
        for bttn in (self.bttn_options, self.bttn_about, self.bttn_settings, self.bttn_shutdown):
            self.vbox_layout.addWidget(bttn)
            self.vbox_layout.setAlignment(bttn, QtCore.Qt.AlignmentFlag.AlignBottom)
            self.vbox_layout.setAlignment(bttn, QtCore.Qt.AlignmentFlag.AlignCenter)
            self.vbox_layout.addStretch(1)
        self.setLayout(self.vbox_layout)

    def _tab_bttn_clicked(self, index):
        """Slot for tab buttons click event.

        This method disables the clicked tab button and enables other buttons.
        Also, it sends the button clicked signal.

        :return <None>
        """
        for bttn in (self.bttn_exercises, self.bttn_planner, self.bttn_workouts, self.bttn_plans):
            if bttn.index == index:
                bttn.setEnabled(False)
            else:
                bttn.setChecked(False)
                bttn.setEnabled(True)
        self.signal_change_tab.emit(index)


class _TabArea(QtWidgets.QWidget):
    """This class, with class '_TabBar', simulates a custom 'TabWidget'

    This class holds all tab workspaces within its stacked widget. It manages
    all actions between tabs.
    """

    def __init__(self, parent):
        super().__init__(parent)
        # ----- GUI children -----
        self.hbox_layout = None
        self.bar = None
        self.tab_all_exercises = None
        self.tab_planner = None
        self.tab_workouts = None
        self.tab_plans = None
        self.stacked_widget = None
        # ----- Initialize UI -----
        self._init_ui()
        # ----- Connect events to slots -----
        self.bar.signal_change_tab.connect(self._change_tab)
        #
        self.tab_exercises.list_exercises.signal_add_exercise_to_table.connect(self._add_exercise_to_table)
        self.tab_exercises.exercise_data_editor.bookmarks_bar. \
            signal_add_exercise_to_table.connect(self._add_exercise_to_table)
        self.tab_exercises.exercise_data_editor.signal_edit_mode_activated.connect(self._activate_edit_mode)
        self.tab_exercises.exercise_data_editor.signal_view_mode_activated.connect(self._activate_view_mode)
        self.tab_exercises.exercise_data_editor.signal_load_to_planner.connect(self._add_exercise_to_table)
        self.tab_exercises.exercise_data_editor.signal_refresh_exer_name_icon.connect(self._refresh_exer_icon_name)
        self.tab_exercises.exercise_data_editor.signal_exercise_deleted.connect(self._exercise_deleted)
        #
        self.tab_planner.exercise_list_viewer.exercises_box.list_exercises.\
            signal_show_exercise_info.connect(self._show_exercise_info)
        self.tab_planner.right.plan_editor.signal_plans_changed.connect(self._plans_changed)
        self.tab_planner.right.plan_editor.signal_create_plan_pdf.connect(self._create_plan_pdf)
        self.tab_planner.right.plan_editor.signal_export_plan.connect(self._export_plan)
        self.tab_planner.right.plan_editor.plan_area.signal_show_exercise_info.\
            connect(self._show_exercise_info)
        self.tab_planner.right.plan_editor.plan_area.signal_workout_saved.\
            connect(self._workout_saved)
        #
        self.tab_workouts.signal_load_workout_to_planner.connect(self._load_workout_to_planner)
        self.tab_workouts.workout_viewer.signal_export_workout.connect(self._export_workout)
        self.tab_workouts.workout_viewer.table.signal_show_exercise_info.\
            connect(self._show_exercise_info)
        #
        self.tab_plans.system_plan_list_viewer.plan_list.signal_load_plan.connect(self._load_plan)
        self.tab_plans.signal_plan_deleted.connect(self._plan_deleted)
        self.tab_plans.user_plan_list_viewer.plan_list.signal_load_plan.connect(self._load_plan)
        self.tab_plans.plan_viewer.plan_area_viewer.signal_show_exercise_info.\
            connect(self._show_exercise_info)
        self.tab_plans.plan_viewer.signal_create_plan_pdf.connect(self._create_plan_pdf)
        self.tab_plans.plan_viewer.signal_export_plan.connect(self._export_plan)
        self.tab_plans.signal_load_plan.connect(self._load_plan)

    def _init_ui(self):
        self.bar = _TabBar(self)
        self.tab_exercises = TabExercises(self, TabIndex.EXERCISES)
        self.tab_planner = TabPlanner(self, TabIndex.PLANNER)
        self.tab_workouts = TabWorkouts(self, TabIndex.WORKOUTS)
        self.tab_plans = TabPlans(self, TabIndex.PLANS)
        self.stacked_widget = QtWidgets.QStackedWidget(self)
        self.stacked_widget.addWidget(self.tab_exercises)
        self.stacked_widget.addWidget(self.tab_planner)
        self.stacked_widget.addWidget(self.tab_workouts)
        self.stacked_widget.addWidget(self.tab_plans)
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.addWidget(self.bar)
        self.hbox_layout.addWidget(self.stacked_widget)
        self.setLayout(self.hbox_layout)

    def display_tab(self, index):
        """Displays tab with given index

        :param index <int> Tab index
        :return <None>
        """
        self.stacked_widget.setCurrentIndex(index)

    # ----- SLOTS -----

    @staticmethod
    def _create_plan_pdf(parent, plan_pdf_data):
        """Slot for signal 'signal_create_plan_pdf' emit event

        :param parent <QtWidgets.QWidget> Widget needed to attach a dialog object
                                          onto it(for testing)
        :param plan_pdf_data <PlanPdfData>
        :return <None>
        """
        parent.pdf_settings_dialog = _PlanPdfSettingsDialog()
        pdf_settings = parent.pdf_settings_dialog.get_pdf_settings()
        if not pdf_settings:
            return  # Creating pdf plan Cancelled
        exported = create_plan_pdf(plan_pdf_data, pdf_settings)
        if exported:
            _export_dir = Settings().getValue('pdf_folderpath')
            _msg = f'Plan "{plan_pdf_data.name}" PDF was created in directory:\n' \
                   f'{_export_dir}'
            parent.info_dialog = InfoMessage('Plan export to PDF', _msg)
            parent.info_dialog.exec()
            parent.info_dialog = None

    @staticmethod
    def _export_plan(parent, plan_data):
        """Slot for signal 'signal_export_plan' emit event

        :param parent <QtWidgets.QWidget> Widget needed to attach a dialog object
                                          onto it(for testing)
        :param plan_pdf_data <PlanData>
        :return <None>
        """
        exported = export_plan(plan_data)
        if exported:
            _export_dir = Settings().getValue('motfiles_folderpath')
            _msg = f'Plan "{plan_data.name}" exported to directory:\n' \
                   f'{_export_dir}'
            parent.info_dialog = InfoMessage('Plan exported', _msg)
            parent.info_dialog.exec()
            parent.info_dialog = None

    @staticmethod
    def _export_workout(workout_data):
        """Slot for signal 'signal_export_workout' emit event

        :param parent <QtWidgets.QWidget> Widget needed to attach a dialog object
                                          onto it(for testing)
        :param plan_pdf_data <PlanData>
        :return <None>
        """
        exported = export_workout(workout_data)
        if exported:
            _export_dir = Settings().getValue('motfiles_folderpath')
            _msg = f'Workout "{workout_data.name}" exported to directory:\n' \
                   f'"{_export_dir}"'
            InfoMessage('Workout exported', _msg).exec()

    def _activate_edit_mode(self):
        """Slot for signal 'signal_edit_mode_activated' emit event

        This method disables tab bar, exercise list viewer and bookmarks bar.
        Used exclusively(for now) when editing exercise data in Tab Exercises.

        :return <None>
        """
        self.bar.setEnabled(False)
        self.tab_exercises.exercise_list_viewer.setEnabled(False)
        self.tab_exercises.exercise_data_editor.bookmarks_bar.setEnabled(False)

    def _activate_view_mode(self):
        """Slot for signal 'signal_view_mode_activated' emit event

        This method enables tab bar, exercise list viewer and bookmarks bar.
        Used exclusively(for now) when editing exercise data in Tab Exercises.

        :return <None>
        """
        self.bar.setEnabled(True)
        self.tab_exercises.exercise_list_viewer.setEnabled(True)
        self.tab_exercises.exercise_data_editor.bookmarks_bar.setEnabled(True)

    def _change_tab(self, index):
        """Slot for signal 'signal_change_tab' emit event

        This method changes the displayed tab.

        :return <None>
        """
        self.display_tab(index.value)

    def _add_exercise_to_table(self, exer_id, table_name):
        """Slot for signals 'signal_load_to_planner' and
        'signal_add_exercise_to_table' emit event

        This method activates tab planner and adds exercise to table from other tabs.

        :return <None>
        """
        self.bar.bttn_planner.click()
        self.tab_planner.right.plan_editor.add_table_row(exer_id, table_name)
        self.tab_planner.right.exer_info_viewer.set_data(exer_id)

    def _show_exercise_info(self, exer_id):
        """Slot for signal 'signal_show_exercise_info' emit event

        This method activates tab exercises and displays exercise data
        from given exercise.

        :param exer_id <int> Exercise id from DB
        :return <None>
        """
        self.bar.bttn_exercises.click()
        self.tab_exercises.list_exercises.clearSelection()
        self.tab_exercises.exercise_data_editor.set_active_exercise(exer_id)

    def _plans_changed(self):
        """Slot for signal 'signal_plans_changed' emit event

        This method refreshes plan in tab plans.

        :return <None>
        """
        self.tab_plans.refresh_plans()

    def _load_workout_to_planner(self, table_name, workout_data):
        """Slot for signal 'signal_load_workout_to_planner' emit event

        This method activates tab planner and loads workout to in table.

        :return <None>
        """
        self.bar.bttn_planner.click()
        self.tab_planner.right.plan_editor.load_workout_to_table(table_name, workout_data)

    def _workout_saved(self):
        """Slot for signal 'signal_workout_saved' emit event

        This method refreshes workouts in tab workouts.

        :return <None>
        """
        self.tab_workouts.refresh_workouts()

    def _load_plan(self, plan_row):
        """Slot for signal 'signal_load_plan' emit event

        This method activates tab planner and loads plan in table.

        :return <None>
        """
        self.bar.bttn_planner.click()
        self.tab_planner.right.plan_editor.load_plan(plan_row)

    def _refresh_exer_icon_name(self, exer_id):
        """Slot for signal 'signal_refresh_exer_name_icon' emit event

        This method refreshes exercise name and icon in exercise list view,
        in tab exercises and tab planner, after its name and/or has been changed
        in exercise data editor.

        :return <None>
        """
        self.tab_exercises.exercise_list_viewer.exercises_box.refresh_icon_name(exer_id)
        self.tab_planner.exercise_list_viewer.exercises_box.refresh_icon_name(exer_id)

    def _exercise_deleted(self):
        """Slot for signal 'signal_exercise_deleted' emit event

        This method refreshes exercise lists in tab exercises and planner.

        :return <None>
        """
        self.tab_exercises.exercise_list_viewer.refresh_exercises()
        self.tab_planner.exercise_list_viewer.refresh_exercises()

    def _plan_deleted(self, plan_id):
        """Slot for signal 'signal_plan_deleted' emit event

        This method, if deleted plan is loaded in tab planner, removes its
        reference as the loaded plan.

        :return <None>
        """
        plan_editor = self.tab_planner.right.plan_editor
        if plan_id == plan_editor.loaded_plan_id:
            plan_editor.loaded_plan_id = None
            plan_editor.top_row.toolbar.bttn_save.setEnabled(False)


class MainWindow(QtWidgets.QMainWindow):
    """Class for main window - parent of all gui widgets"""

    def __init__(self):
        super().__init__()
        self.setObjectName('main_window')
        self.setWindowIcon(QtGui.QIcon(ImageFp.MOTUS_ICON))
        self.setIconSize(QtCore.QSize(50, 50))
        self.setWindowTitle(APP_NAME)
        self.showMaximized()
        self.setGeometry(self._get_window_geometry())
        self.setStyleSheet('''
            .MainWindow{
                background-color: %s
            }
        ''' % Colors.MAIN_WINDOW.hex)
        # ----- Data -----
        self.updated_widgets = {}  # NOTE: for development mode: {KEY=object, VALUE=objectName()}
        # ----- GUI children -----
        self.bttn_load_css = None  # NOTE: for development mode
        self.toolbar = None  # NOTE: for development mode
        self.tab_widget = None

    def init_ui(self):
        # ----- Set GUI -----
        if APP_MODE == APP_MODE.DEVELOPMENT_MODE:
            self.toolbar = QtWidgets.QToolBar(self)
            # Load css available only in development mode
            self.bttn_load_css = QtWidgets.QWidgetAction(self)
            self.bttn_load_css.setText('Load CSS(development mode)')
            self.bttn_load_css.triggered.connect(self._load_css)
            self.toolbar.addAction(self.bttn_load_css)
            self.addToolBar(self.toolbar)
        self.tab_widget = _TabArea(self)
        # ----- Connect events to slots -----
        self.tab_widget.bar.bttn_about.clicked.connect(self._open_about)
        self.tab_widget.bar.bttn_settings.clicked.connect(self._open_settings)
        self.tab_widget.bar.signal_restart.connect(self._restart_app)
        self.tab_widget.bar.signal_shutdown.connect(self._exit_app)
        self.tab_widget.bar.signal_open_pdf_folder.connect(self._open_pdf_folder)
        self.tab_widget.bar.signal_open_motfiles_folder.connect(self._open_motfiles_folder)
        self.tab_widget.bar.signal_send_feedback.connect(self._send_feedback)
        self.setCentralWidget(self.tab_widget)
        # ----- Post init actions -----
        self.tab_widget.bar.bttn_exercises.click()

    @staticmethod
    def _get_window_geometry():
        """Returns main screen rectangle

        :return <QtCore.QRect> Has attrs: x, y, width and height
        """
        key_screen_geometry = f'{Settings().values["main_display"]}_geometry'
        geo_tuple = Settings().values[key_screen_geometry]
        return QtCore.QRect(geo_tuple[0], geo_tuple[1], geo_tuple[2], geo_tuple[3])

    def sizeHint(self):
        return QtCore.QSize(self.geometry().width(),
                            self.geometry().height())

    def _pre_close_actions(self):
        """Executes actions before app is restarted or closed.

        :return <None>
        """
        # ----- Save session bookmarked exercises ----
        self.tab_widget.tab_exercises.exercise_data_editor.bookmarks_bar.write_to_file()
        # ----- Save planner changes -----
        plan_editor = self.tab_widget.tab_planner.right.plan_editor
        if plan_editor.unsaved_changes:
            self.tab_widget.display_tab(TabIndex.PLANNER.value)
            plan_editor.check_for_changes_and_save()
        # ----- Save last loaded plan in planner -----
        plan_id = self.tab_widget.tab_planner.right.plan_editor.loaded_plan_id
        if plan_id:
            Session().set_value('last_loaded_plan', plan_id)

    @staticmethod
    @log_and_show_method_exception('Opening folder failed')
    def _open_folder(folder_path):
        """Opens folder in Windows explorer with given path.

        :folder_path <str> Folderpath
        :return <None> or <ExceptionWithMsg>
        """
        windows_explorer = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
        folder_path = os.path.normpath(folder_path)
        if not Path(folder_path).exists():
            _msg = f'Directory with path "{folder_path}" not found\n\n' \
                   f'Create folder and set some other one in settings.'
            ErrorMessage('Opening folder failed', _msg).exec()
            return
        try:
            subprocess.run([windows_explorer, folder_path])
        except OSError as ex:
            return ExceptionWithMsg(ex, f'Couldn\'t open folder "{folder_path}".')

    # ----- SLOTS -----

    def _change_font(self, font_family):
        """Slot on signal 'signal_change_font' emit event.

        Changes font family of texts in whole app.

        :param font_family <str>
        :param <None>
        """
        all_children = self.findChildren(QtWidgets.QWidget)
        for widget in all_children:
            if hasattr(widget, 'setFont'):
                size = widget.font().pointSize()
                new_font = QtGui.QFont(font_family, size)
                widget.setFont(new_font)

    def _load_css(self):
        """Slot on button 'Load CSS' clicked event.

        Loads stylesheet for every registerd widget in whole app.
        Check README.txt file in directory '/src/css'.

        :return <None>
        """
        all_children = self.findChildren(QtWidgets.QWidget)
        css_folder = Path(SRC_DIR).joinpath('css')
        for ch in all_children:
            obj_css_fp = Path(css_folder).joinpath(ch.objectName() + '.txt')
            class_css_fp = Path(css_folder).joinpath('class_' + ch.__class__.__name__ + '.txt')
            if '_WorkoutTableBase' in str(class_css_fp):
                print(1)
            for css_fp in (obj_css_fp, class_css_fp):
                if css_fp.exists():
                    with open(css_fp, 'r') as fopen:
                        style_sheet = fopen.read()
                    ch.setStyleSheet(style_sheet)
                    self.updated_widgets[ch] = f'{ch.__class__.__name__}({ch.objectName()})'
        if self.updated_widgets:
            dialog_text = '\n'.join(list(self.updated_widgets.values()))
            pos = self.mapToGlobal(self.toolbar.children()[3].pos())
            InfoMessage('Updated css - widgets', dialog_text, parent_pos=pos).exec()

    def closeEvent(self, event):
        """Overrites parent method 'closeEvent'

        Handles action after close button is clicked.

        :param event <QtGui.QCloseEvent> Event object
        :return <None>
        """
        self._pre_close_actions()
        super().closeEvent(event)

    def _open_pdf_folder(self):
        """Slot on button 'Open PDF files folder' clicked event.

        Opens folder with exported pdf files.

        :return <None>
        """
        pdf_folder = Settings().getValue('pdf_folderpath')
        self._open_folder(pdf_folder)

    def _open_motfiles_folder(self):
        """Slot on button 'Open MOT files folder' clicked event.

        Opens folder with exported mot files.

        :return <None>
        """
        motfiles_folder = Settings().getValue('motfiles_folderpath')
        self._open_folder(motfiles_folder)

    @staticmethod
    def _send_feedback():
        """Slot on button 'Send feecback' clicked event.

        Opens Feedback dialog.

        :return <None>
        """
        _FeedbackDialog().exec()

    @staticmethod
    def _open_about():
        """Slot on button 'About' clicked event.

        Shows about info message.

        :return <None>
        """
        resource_page_link = '<a href="https://www.bodybuilding.com/exercises/">LINK</a>'
        _msg = (f'''
        <p>
        Author:  Marko Raos-Stojnić</h3><br><br>
        Version: {VERSION}<br><br>
        E-mail:  motusappdevs@gmail.com<br><br>
        Images and data used from site:<br><br>
        &nbsp;&nbsp;&nbsp;&nbsp;->&nbsp;{resource_page_link}
        </p>
        ''')
        InfoMessage('About Motus App', _msg).exec()

    def _open_settings(self):
        """Slot on button 'Settings' clicked event.

        Opens settings dialog and restart app if needed.

        :return <None>
        """
        dialog = _SettingsDialog()
        dialog.signal_change_font.connect(self._change_font)
        restart = dialog.open_settings()
        if restart:
            self._restart_app()

    def _restart_app(self):
        """Slot on button 'Restart' clicked event.

        Executes pre-close actions and restarts app.

        :return <None>
        """
        self._pre_close_actions()
        QtWidgets.QApplication.exit(ExitCode.RESTART)

    def _exit_app(self):
        """Slot on button 'Shutdown' clicked event.

        Executes pre-close actions and closes app.

        :return <None>
        """
        self._pre_close_actions()
        QtCore.QCoreApplication.quit()
