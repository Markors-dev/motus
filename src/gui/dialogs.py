import traceback

from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from config import PROJ_DIR, APP_MODE, AppMode
from settings import Settings
from .flags import ImageFp, AlignFlag, ButtonType, SizePolicy
from .util import get_center_pos, find_button_by_text, set_value


class BaseDialog(QtWidgets.QDialog):
    """Base dialog class for all custom dialog classes in App

    This class sets: dialog title, icon(if provided) and title bar properties.
    """
    def __init__(self, title, icon_fp=None):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint |
                            QtCore.Qt.WindowType.WindowCloseButtonHint |
                            QtCore.Qt.WindowType.WindowTitleHint)
        if icon_fp:
            self.setWindowIcon(QtGui.QIcon(icon_fp))


class BaseInfoDialog(BaseDialog):
    """Base dialog class for simple dialog and message classes

    The dialog body consists of an image(on the left), text(on the right)
    and a button box.
    """
    def __init__(self, title, image_fp, text, bttns, bttn_action_dict=None, parent_pos=None):
        """
        :param title <str> Dialog title
        :param image_fp <str> Image filepath
        :param text <str> Dialog body text
        :param bttns <int> Dialog button box buttons flag
        :param bttn_action_dict <None> or <dict[<str>: <func>]> Key: action button text,
                                                                Value: action function
        :param parent_pos <None> or <QPoint> Position of parent(upper left corner)
        """
        super().__init__(title, icon_fp=ImageFp.MOTUS_ICON)
        self.setMinimumWidth(500)
        self.setStyleSheet("""
        ._BaseInfoDialog {
            border: 1px solid black;
            border-radius: 10px;
        }
        """)
        # --- Image ---
        self.image = QtWidgets.QLabel(self)
        self.image.setPixmap(QtGui.QPixmap(image_fp))
        self.image.setSizePolicy(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM)
        self.image.setAlignment(AlignFlag.Top)
        # --- Text ---
        self.text = QtWidgets.QLabel(self)
        self.text.setWordWrap(True)
        self.text.setText(text)
        self.text.setSizePolicy(SizePolicy.MINIMUM, SizePolicy.MINIMUM)
        self.text.setAlignment(AlignFlag.Left | AlignFlag.VCenter)
        self.text.setOpenExternalLinks(True)
        # --- Button box ---
        self.button_box = QtWidgets.QDialogButtonBox(bttns)
        self.button_box.setContentsMargins(100, 20, 10, 5)
        if bttn_action_dict:
            bttn_action = find_button_by_text(self.button_box.buttons(), 'Apply')
            bttn_action.setText(tuple(bttn_action_dict.keys())[0])
            bttn_action.clicked.connect(tuple(bttn_action_dict.values())[0])
        # ----- Set layout -----
        _msg_row = QtWidgets.QWidget(self)
        _msg_row.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MINIMUM)
        _msg_row_layout = QtWidgets.QHBoxLayout(_msg_row)
        _msg_row_layout.setSpacing(10)
        _msg_row_layout.addWidget(self.image)
        _msg_row_layout.addWidget(self.text)
        _msg_row.setLayout(_msg_row_layout)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(_msg_row)
        self.vbox_layout.addWidget(self.button_box)
        self.setLayout(self.vbox_layout)
        # ----- Post init actions -----
        self.adjustSize()
        pos = self.mapToGlobal(parent_pos) if parent_pos else get_center_pos(self)
        self.setGeometry(pos.x(), pos.y(), self.width(), self.height())


class InfoMessage(BaseInfoDialog):
    """Simple info message containing info text and 'Ok' button"""

    def __init__(self, title, text, parent_pos=None):
        """
        :param title <str> Dialog title
        :param text <str> Dialog body text
        :param parent_pos <None> or <QPoint> Position of parent(upper left corner)
        """
        bttns = ButtonType.Ok
        super().__init__(title, ImageFp.INFO, text, bttns, parent_pos=parent_pos)
        self.button_box.accepted.connect(self.accept)


class QuestionDialog(BaseInfoDialog):
    """Simple question message containing question text and 'Yes'/'No' buttons"""

    def __init__(self, title, text, parent_pos=None):
        """
        :param title <str> Dialog title
        :param text <str> Dialog body text
        :param parent_pos <None> or <QPoint> Position of parent(upper left corner)
        """
        bttns = ButtonType.Yes | ButtonType.No
        super().__init__(title, ImageFp.QUESTION, text, bttns, parent_pos=parent_pos)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)


class ErrorMessage(BaseInfoDialog):
    """Simple error message containing info text and 'Ok' button"""

    def __init__(self, title, text, parent_pos=None):
        """
        :param title <str> Dialog title
        :param text <str> Dialog body text
        :param parent_pos <None> or <QPoint> Position of parent(upper left corner)
        """
        bttns = ButtonType.Ok
        super().__init__(title, ImageFp.ERROR, text, bttns, parent_pos=parent_pos)
        self.button_box.accepted.connect(self.accept)


def get_filepath_from_dialog(parent, title='Choose file from PC', start_dir=PROJ_DIR,
                             file_types='All files (*.*)'):
    """Raises a file dialog and, after user selection, returns file path

    :param parent <QWidget> Parent widget of dialog
    :param title <str> Dialog title
    :param start_dir <str> Path to start directory
    :param file_types <str> Approved file types(extensions)
    :return <str>
    """
    parent.file_dialog = QtWidgets.QFileDialog()
    parent.file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
    fp, _ = parent.file_dialog.getOpenFileName(parent, title, start_dir, file_types)
    return fp


def get_folderpath_from_dialog(parent, start_dir=PROJ_DIR):
    """Raises a file dialog and, after user selection, returns folder path

    :param parent <QWidget> Parent widget of dialog
    :param start_dir <str> Path to start directory
    :return <str>
    """
    file_dialog = QtWidgets.QFileDialog()
    file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
    fp = file_dialog.getExistingDirectory(parent, 'Choose directory', start_dir)
    return fp


def raise_missing_exercises_error_msg(missing_exercises, mot_type):
    """Raises error message when exercises are missing from workout/plan

    :param missing_exercises <list[<str>]> List of missing exercise names
    :param mot_type <MotType> Type of Motus App object -> Workout or Plan
    :return <None>
    """
    _msg = f'Some exercises are missing from App database.' \
           f'They were probably deleted.\n' \
           f'Missing exercises:\n' \
           f'{", ".join(missing_exercises)}\n\n' \
           f'NOTE: save(or export) {mot_type.value} to avoid this message again.'
    ErrorMessage('Missing exercises', _msg).exec()
