from PyQt5 import QtWidgets
from PyQt5 import QtCore

from gui.util import set_value, get_value
from gui.flags import SizePolicy
from ._images import ImageWithText


class ExerciseDataViewEditWidget(QtWidgets.QWidget):
    """This widget contains 2 widgets: one for viewing desired value,
    and other for editing. Only 1 can be visible at a time.
    The widget for editing can have a value validator.
    """

    def __init__(self, parent, view_widget, edit_widget, edit_mode=False,
                 cont_margins=(0, 0, 0, 0)):
        super().__init__(parent)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MINIMUM)
        # ----- Data -----
        self.edit_mode = edit_mode
        # ----- Gui children -----
        self.hbox_layout = None
        self.view_widget = view_widget
        self.edit_widget = edit_widget
        # Initialize GUI
        self._init_ui(cont_margins)

    def _init_ui(self, cont_margins):
        # Set visibility of widgets based on active mode
        view_vidget_visible, edit_vidget_visible = (False, True) if self.edit_mode \
            else (True, False)
        self.view_widget.setVisible(view_vidget_visible)
        self.view_widget.setContentsMargins(*cont_margins)
        self.edit_widget.setVisible(edit_vidget_visible)
        self.edit_widget.setContentsMargins(*cont_margins)
        # Set layout
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(*cont_margins)
        self.hbox_layout.addWidget(self.view_widget)
        self.hbox_layout.addWidget(self.edit_widget)
        self.setLayout(self.hbox_layout)

    def activate_view_mode(self, save=False):
        self.edit_mode = False
        self.edit_widget.setVisible(False)
        _visible = True
        if type(self.view_widget) == ImageWithText:
            # Horible workaround for "ImageWithText class; TODO: Fix this
            _visible = True if self.view_widget.image_set else False
        self.view_widget.setVisible(_visible)
        if save:
            set_value(self.view_widget, get_value(self.edit_widget))

    def activate_edit_mode(self):
        self.edit_mode = True
        self.view_widget.setVisible(False)
        self.edit_widget.setVisible(True)
        set_value(self.edit_widget, get_value(self.view_widget))

    def set_data(self, data):
        if self.edit_mode:
            return set_value(self.edit_widget, data)
        else:
            return set_value(self.view_widget, data)

    def get_data(self):
        if self.edit_mode:
            return get_value(self.edit_widget)
        else:
            return get_value(self.view_widget)


class VLine(QtWidgets.QFrame):
    def __init__(self, parent, size=None):
        super().__init__(parent)
        self.setStyleSheet("""border: 1px solid black;""")
        if size:
            self.setFixedSize(QtCore.QSize(*size))
        self.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)


class HLine(QtWidgets.QFrame):
    def __init__(self, parent, size=None):
        super().__init__(parent)
        if size:
            self.setFixedSize(QtCore.QSize(*size))
        self.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)


class CheckBox(QtWidgets.QCheckBox):
    def __init__(self, parent, obj_name, text='', checked=False, enabled=True,
                 direction=QtCore.Qt.LayoutDirection.RightToLeft):
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setText(text)
        self.setEnabled(enabled)
        self.setChecked(checked)
        self.setLayoutDirection(direction)
