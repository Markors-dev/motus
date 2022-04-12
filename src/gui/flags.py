from pathlib import Path
from enum import Enum

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from config import IMAGES_DIR


def _get_path(dir_, *args):
    return str(Path(dir_).joinpath(*args))


class ExitCode:
    RESTART = 1
    SHUTDOWN = 2


class MouseButton(Enum):
    LEFT = 1


class LayoutOrientation(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class MotType(Enum):
    WORKOUT = 'Workout'
    PLAN = 'Plan'


class ImageFp:
    NO_IMAGE = _get_path(IMAGES_DIR, 'no_image.jpg')
    USER = _get_path(IMAGES_DIR, 'user.png')
    # PDF
    BODYBUILDING = _get_path(IMAGES_DIR, 'pdf', 'bodybuilding.png')
    CALISTHENICS = _get_path(IMAGES_DIR, 'pdf', 'calisthenics.png')
    CARDIO = _get_path(IMAGES_DIR, 'pdf', 'cardio.png')
    HIIT = _get_path(IMAGES_DIR, 'pdf', 'hiit.png')
    OLYMPIC_WEIGHTLIFTING = _get_path(IMAGES_DIR, 'pdf', 'olympic_weightlifting.png')
    POWERLIFTING = _get_path(IMAGES_DIR, 'pdf', 'powerlifting.png')
    REST_DAY = _get_path(IMAGES_DIR, 'pdf', 'rest_day.png')
    # Icons
    ERROR = _get_path(IMAGES_DIR, 'error.png')
    QUESTION = _get_path(IMAGES_DIR, 'question.png')
    INFO = _get_path(IMAGES_DIR, 'info.png')
    INFO_SMALL = _get_path(IMAGES_DIR, 'info_small.png')
    EXERCISE = _get_path(IMAGES_DIR, 'exercise.png')
    MOTUS_ICON = _get_path(IMAGES_DIR, 'motus_icon.png')
    MOTUS_LOGO = _get_path(IMAGES_DIR, 'motus_logo.png')
    URL = _get_path(IMAGES_DIR, 'url.png')
    FEEDBACK = _get_path(IMAGES_DIR, 'feedback.png')
    CHOOSE = _get_path(IMAGES_DIR, 'choose.png')
    # Buttons
    HEART = _get_path(IMAGES_DIR, 'buttons', 'heart.png')
    HEART_ALT = _get_path(IMAGES_DIR, 'buttons', 'heart_alt.png')
    PREVIOUS = _get_path(IMAGES_DIR, 'buttons', 'previous.png')
    PREVIOUS_ALT = _get_path(IMAGES_DIR, 'buttons', 'previous_alt.png')
    NEXT = _get_path(IMAGES_DIR, 'buttons', 'next.png')
    NEXT_ALT = _get_path(IMAGES_DIR, 'buttons', 'next_alt.png')
    DOWN_ARROW = _get_path(IMAGES_DIR, 'buttons', 'arrow_down.png')
    RIGHT_ARROW = _get_path(IMAGES_DIR, 'buttons', 'arrow_right.png')
    SAVE = _get_path(IMAGES_DIR, 'buttons', 'save.png')
    SAVE_AS = _get_path(IMAGES_DIR, 'buttons', 'save_as.png')
    LOAD = _get_path(IMAGES_DIR, 'buttons', 'load.png')
    EXPORT = _get_path(IMAGES_DIR, 'buttons', 'export.png')
    IMPORT = _get_path(IMAGES_DIR, 'buttons', 'import.png')
    MENU = _get_path(IMAGES_DIR, 'buttons', 'menu.png')
    EXERCISES = _get_path(IMAGES_DIR, 'buttons', 'exercises.png')
    PLANNER = _get_path(IMAGES_DIR, 'buttons', 'planner.png')
    PLANS = _get_path(IMAGES_DIR, 'buttons', 'plans.png')
    SETTINGS = _get_path(IMAGES_DIR, 'buttons', 'settings.png')
    ABOUT = _get_path(IMAGES_DIR, 'buttons', 'about.png')
    SHUTDOWN = _get_path(IMAGES_DIR, 'buttons', 'shutdown.png')
    SHUTDOWN_SMALL = _get_path(IMAGES_DIR, 'buttons', 'shutdown_small.png')
    RESTART = _get_path(IMAGES_DIR, 'buttons', 'restart.png')
    OPTIONS = _get_path(IMAGES_DIR, 'buttons', 'options.png')
    WORKOUTS = _get_path(IMAGES_DIR, 'buttons', 'workouts.png')
    VISIBLE = _get_path(IMAGES_DIR, 'buttons', 'visible.png')
    INVISIBLE = _get_path(IMAGES_DIR, 'buttons', 'invisible.png')
    NEW = _get_path(IMAGES_DIR, 'buttons', 'new.png')
    PLAN_PDF = _get_path(IMAGES_DIR, 'buttons', 'plan_pdf.png')
    EDIT = _get_path(IMAGES_DIR, 'buttons', 'edit.png')
    CANCEL = _get_path(IMAGES_DIR, 'buttons', 'cancel.png')
    DELETE = _get_path(IMAGES_DIR, 'buttons', 'delete.png')
    DELETE_SMALL = _get_path(IMAGES_DIR, 'buttons', 'delete_small.png')
    PLUS = _get_path(IMAGES_DIR, 'buttons', 'plus.png')
    FOLDER = _get_path(IMAGES_DIR, 'buttons', 'folder.png')
    ICON = _get_path(IMAGES_DIR, 'buttons', 'icon.png')


class Key:
    ENTER = 16777220
    RETURN = 16777221
    DEL = 16777223
    LEFT = 16777234
    UP = 16777235
    RIGHT = 16777236
    DOWN = 16777237
    CTRL = 16777249
    #
    WHEEL_DOWN = -120
    WHEEL_UP = 120


class SizePolicy:
    MAXIMUM = QtWidgets.QSizePolicy.Policy.Maximum
    PREFERRED = QtWidgets.QSizePolicy.Policy.Preferred
    FIXED = QtWidgets.QSizePolicy.Policy.Fixed
    MINIMUM = QtWidgets.QSizePolicy.Policy.Minimum
    MINIMUM_EXPANDING = QtWidgets.QSizePolicy.Policy.MinimumExpanding
    EXPANDING = QtWidgets.QSizePolicy.Policy.Expanding
    IGNORED = QtWidgets.QSizePolicy.Policy.Ignored


class Orientation:
    HORIZONTAL = QtCore.Qt.Orientation.Horizontal
    VERTICAL = QtCore.Qt.Orientation.Vertical


class AlignFlag:
    Center = QtCore.Qt.AlignmentFlag.AlignCenter
    Left = QtCore.Qt.AlignmentFlag.AlignLeft
    Right = QtCore.Qt.AlignmentFlag.AlignRight
    Top = QtCore.Qt.AlignmentFlag.AlignTop
    Bottom = QtCore.Qt.AlignmentFlag.AlignBottom
    HCenter = QtCore.Qt.AlignmentFlag.AlignHCenter
    VCenter = QtCore.Qt.AlignmentFlag.AlignVCenter
    Absolute = QtCore.Qt.AlignmentFlag.AlignAbsolute
    Baseline = QtCore.Qt.AlignmentFlag.AlignBaseline
    Justify = QtCore.Qt.AlignmentFlag.AlignJustify
    Trailing = QtCore.Qt.AlignmentFlag.AlignTrailing
    Leading = QtCore.Qt.AlignmentFlag.AlignLeading
    Horizontal_Mask = QtCore.Qt.AlignmentFlag.AlignHorizontal_Mask
    Vertical_Mask = QtCore.Qt.AlignmentFlag.AlignVertical_Mask


class ScrollBarPolicy:
    AlwaysOn = QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
    AlwaysOff = QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    AsNeeded = QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded


class ButtonType:
    Ok = QtWidgets.QDialogButtonBox.StandardButton.Ok
    Cancel = QtWidgets.QDialogButtonBox.StandardButton.Cancel
    Yes = QtWidgets.QDialogButtonBox.StandardButton.Yes
    No = QtWidgets.QDialogButtonBox.StandardButton.No
    Apply = QtWidgets.QDialogButtonBox.StandardButton.Apply
    Close = QtWidgets.QDialogButtonBox.StandardButton.Close
    Abort = QtWidgets.QDialogButtonBox.StandardButton.Abort
    Discard = QtWidgets.QDialogButtonBox.StandardButton.Discard
    Help = QtWidgets.QDialogButtonBox.StandardButton.Help
    Ignore = QtWidgets.QDialogButtonBox.StandardButton.Ignore
    NoButton = QtWidgets.QDialogButtonBox.StandardButton.NoButton


class PermissionType(Enum):
    System = 0
    User = 1


class ItemFlag:
    Selectable = QtCore.Qt.ItemFlag.ItemIsSelectable
    Enabled = QtCore.Qt.ItemFlag.ItemIsEnabled
    Editable = QtCore.Qt.ItemFlag.ItemIsEditable
