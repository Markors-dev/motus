from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from gui.flags import SizePolicy, AlignFlag, ImageFp
from gui.font import FontFlag, Font
from gui.colors import Colors
from gui.util import get_label_width
from ._labels import MyLabel
from ._images import Image
from ._panes import HBoxPane


class LineEdit(QtWidgets.QLineEdit):
    hover_focus_css = 'LineEdit:hover { border: 1px solid blue; } ' \
                      'LineEdit:focus { border: 1px solid green; }'

    def __init__(self, parent, obj_name, text, bg_color='white', text_color='black', enabled=True,
                 border_radius=2, font_flag=FontFlag.NORMAL_TEXT, place_holder_text='input_text...',
                 align_flag=AlignFlag.Left, size_policy=(SizePolicy.EXPANDING, SizePolicy.MINIMUM)):
        super().__init__(parent)
        # ----- Data -----
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_radius = border_radius
        # ----- Props -----
        self.setObjectName(obj_name)
        self.setText(text)
        self.setEnabled(enabled)
        self.setFont(Font.get_font(font_flag))
        self.setPlaceholderText(place_holder_text)
        self.setAlignment(align_flag)
        self.setSizePolicy(*size_policy)
        # ----- Post init actions -----
        self.set_valid_css()

    def sizeHint(self):
        text_width = get_label_width(self.text(), font=self.font())
        return QtCore.QSize(text_width + 16, self.height())

    def _set_css(self, bg_color):
        self.setStyleSheet("""
            LineEdit {
                background-color: %s;
                color: %s;
                border: 1px solid %s;
                border-radius: %spx;
            }
        """ % (bg_color, self.text_color, bg_color, self.border_radius) +
               self.hover_focus_css)

    def set_valid_css(self):
        self._set_css(self.bg_color)

    def set_invalid_css(self):
        self._set_css(Colors.INVALID_INPUT.hex)


class ValidatedLineEdit(QtWidgets.QFrame):
    signal_text_changed = QtCore.pyqtSignal(str)

    def __init__(self, parent, obj_name, text, text_validator, invalid_msg, bg_color='white',
                 text_color='black', border_radius=2, align_flag=AlignFlag.Left, retain_msg_size=True,
                 enabled=True, font_flag=FontFlag.BIG_TITLE,
                 size_policy=(SizePolicy.EXPANDING, SizePolicy.MAXIMUM), place_holder_text='',
                 empty_valid=False):
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setEnabled(enabled)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(*size_policy)
        # ----- Data -----
        self.valid = True
        self.empty_valid = empty_valid
        self.text_validator = text_validator
        # ----- GUI children -----
        self.vbox_layout = None
        self.line_edit = None
        self.message_row = None
        # ----- Init UI -----
        self._init_ui(text, retain_msg_size, invalid_msg, font_flag, size_policy,
                      place_holder_text, bg_color, text_color, border_radius, align_flag)
        # ----- Connect events to slots -----
        self.line_edit.textChanged.connect(self._text_changed)
        # ----- Post init actions -----
        self._validate_text()

    def _init_ui(self, text, retain_msg_size, invalid_msg, font_flag, size_policy,
                 place_holder_text, bg_color, text_color, border_radius, align_flag):
        self.line_edit = LineEdit(
            self, 'line_edit', text, bg_color=bg_color, text_color=text_color, border_radius=border_radius,
            font_flag=font_flag, place_holder_text=place_holder_text, align_flag=align_flag,
            size_policy=size_policy)
        self.line_edit.setContentsMargins(0, 0, 0, 0)
        message = MyLabel(self, 'label', '*text input invalid: ', font_flag=FontFlag.SMALL_TEXT)
        message.setContentsMargins(0, 0, 0, 0)
        bttn_message_info = Image(
            self, 'im_msg_info', ImageFp.INFO_SMALL, invalid_msg, cont_margins=(0, 0, 0, 0))
        self.message_row = HBoxPane(self, (message, bttn_message_info), visible=False,
                                    cont_margins=(0, 0, 0, 0))
        _size_policy = QtWidgets.QSizePolicy(*size_policy)
        _size_policy.setRetainSizeWhenHidden(retain_msg_size)
        self.message_row.setSizePolicy(_size_policy)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.vbox_layout.addWidget(self.line_edit)
        self.vbox_layout.addWidget(self.message_row)
        self.setLayout(self.vbox_layout)

    def _validate_text(self):
        text = self.line_edit.text()
        if len(text) == 0 and self.empty_valid or self.text_validator(text):
            self.valid = True
            self.line_edit.set_valid_css()
            self.message_row.setVisible(False)
        else:
            self.valid = False
            self.line_edit.set_invalid_css()
            self.message_row.setVisible(True)

    def _text_changed(self, text):
        self._validate_text()
        self.signal_text_changed.emit(text)

    def set_text(self, text):
        self.line_edit.setText(text)


class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent, obj_name, text, height=None, font_flag=FontFlag.NORMAL_TEXT):
        super().__init__(parent)
        self.setStyleSheet("""
        TextEdit:focus {
            border: 2px solid green;
        }
        """)
        self.setObjectName(obj_name)
        self.setText(text)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        if height:
            self.setFixedHeight(height)
        self.setFont(Font.get_font(font_flag))

    def sizeHint(self):
        return QtCore.QSize(self.width(), 20)
