from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore


from gui.font import Font, FontFlag
from gui.colors import Colors
from gui.flags import SizePolicy, AlignFlag, MouseButton, Orientation


class RoundPushButton(QtWidgets.QPushButton):

    def __init__(self, parent, obj_name, text, size=None, enabled=True,
                 visible=True, checkable=False, checked=False, font_flag=None):
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setText(text)
        if size:
            self.setFixedSize(*size)
        self.setEnabled(enabled)
        self.setVisible(visible)
        self.setCheckable(checkable)
        if checkable:
            self.setChecked(checked)
        if font_flag:
            self.setFont(Font.get_font(font_flag))
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet('''
            .RoundPushButton {
                border: 1px solid %s;
                border-radius: 8px;
                color: #FFFFFF;
                background-color: %s;
                padding: 5px;
            }
            .RoundPushButton:hover {
                background-color: %s;
            }
            .RoundPushButton:pressed {
                border: 1px solid grey;
                border-style: inset;
                background-color: gray;
            }
            .RoundPushButton:checked {
                background-color: %s;
            }
            .RoundPushButton:disabled {
                background-color: %s;
                color: black;
            }
        ''' % (Colors.BTTN.hex, Colors.BTTN.hex, Colors.BTTN_HOVER.hex,
               Colors.BTTN_PRESSED.hex, Colors.BTTN_DISABLED.hex))


class DropFileRoundPushButton(RoundPushButton):
    signal_file_dropped = QtCore.pyqtSignal(str)

    def __init__(self, parent, obj_name, text, accepted_ext):
        super().__init__(parent, obj_name, text)
        self.setAcceptDrops(True)
        # ----- Data -----
        self.accepted_ext = accepted_ext

    @staticmethod
    def _get_ext_from_url(url):
        return url.path().split('.')[-1]

    def dragEnterEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and self._get_ext_from_url(urls[0]) in self.accepted_ext:
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and self._get_ext_from_url(urls[0]) in self.accepted_ext:
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and self._get_ext_from_url(urls[0]) in self.accepted_ext:
            fp = str(urls[0].path())[1:]
            self.signal_file_dropped.emit(fp)


class ImageButton(QtWidgets.QPushButton):
    PADDING = 5

    def __init__(self, parent, obj_name, icon_fp, tooltip, for_user_tooltip=False, visible=True,
                 enabled=True):
        """ Custom button with image.

        :param parent <QWidget>
        :param obj_name <str>
        :param icon_filename: <str> Icon filename in dir r'\\data\\images\\icons\\buttons'
        :param size: <(int, int)> Size of icon
        :param tooltip: <str>
        """
        super().__init__(parent)
        # ----- Data ----
        self.tooltip = tooltip
        self.for_user_tooltip = for_user_tooltip
        #
        self.setObjectName(obj_name)
        self.setVisible(visible)
        self.icon_pixmap = QtGui.QPixmap(icon_fp)
        self.set_icon(self.icon_pixmap)
        self.setSizePolicy(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM)
        self.setStyleSheet('''
            ImageButton{
                background: none;
                border: none;
            }
            ImageButton:hover {
                background-color: %s;
                border: 1px solid %s;
                border-radius: 10px;
            }
        ''' % (Colors.BTTN_HOVER.hex, Colors.BTTN_HOVER.hex))
        # if tooltip:
        self.setToolTip(tooltip)
        self.setEnabled(enabled)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        if not enabled and self.for_user_tooltip:
            self.setToolTip(f'{self.tooltip}(for User exercises only)')
        else:
            self.setToolTip(self.tooltip)

    def set_icon(self, icon_pixmap):
        self.setIcon(QtGui.QIcon(icon_pixmap))
        self.setIconSize(icon_pixmap.size())


class MyToolbutton(QtWidgets.QToolButton):
    def __init__(self, parent, obj_name, icon_fp, text):
        super().__init__(parent)
        # self.setStyleSheet("""
        #     MyToolbutton {
        #         border: 1px solid black;
        # }
        # """)
        self.setObjectName(obj_name)
        self.setCheckable(True)
        self.setSizePolicy(SizePolicy.MINIMUM, SizePolicy.FIXED)
        icon_pixmap = QtGui.QPixmap(icon_fp)
        self.setIcon(QtGui.QIcon(icon_pixmap))
        self.setIconSize(icon_pixmap.size())
        self.setText(text)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)


class TabWidgetButton(MyToolbutton):
    PADDING = 10

    def __init__(self, parent, obj_name, icon_fp, text, index):
        super().__init__(parent, obj_name, icon_fp, text)
        self.setStyleSheet("""
        TabWidgetButton {
            border: none;
            border-radius: 10px;
            margin-top: 5px;
            margin-bottom: 5px;
            padding: 10px;
        }
        TabWidgetButton:hover {
            border: 1px solid #99CCFF;
            background-color: #99CCFF;
            padding-top: 5px;
            padding-bottom: 5px;
        }
        TabWidgetButton:checked {
            border: 1px solid #3399FF;
            background-color: #3399FF;
            color: white;
        }
        """)
        self.setSizePolicy(SizePolicy.FIXED, SizePolicy.FIXED)
        self.index = index

    # def sizeHint(self):
    #     return QtCore.QSize(self.iconSize().width() + self.PADDING * 2,
    #                         self.iconSize().height() + self.PADDING * 3)


class CheckableImageButton(ImageButton):
    """Checkable image button that changes image when checked"""

    def __init__(self, parent, obj_name, icon_fp, icon_fp_alt, tooltip, alt_tooltip,
                 checked=False, visible=True):
        super().__init__(parent, obj_name, icon_fp, tooltip=tooltip)
        self.icon_alt_pixmap = QtGui.QPixmap(icon_fp_alt)
        self.alt_tooltip = alt_tooltip
        self.setVisible(visible)
        self.setSizePolicy(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM)
        self.setCheckable(True)
        self.setChecked(checked)

    def setChecked(self, checked):
        super().setChecked(checked)
        icon_pixmap = self.icon_pixmap if not checked else self.icon_alt_pixmap
        self.set_icon(icon_pixmap)
        tooltip = self.tooltip if not checked else self.alt_tooltip
        self.setToolTip(tooltip)

    # SLOTS $

    def mousePressEvent(self, event):
        checked = False if self.isChecked() else True
        self.setChecked(checked)
        self.clicked.emit(checked)


class _CloseButton(QtWidgets.QPushButton):
    """Used only in class <ClosableButton>"""

    def __init__(self, parent, text, size, visible=True):
        super().__init__(parent)
        assert size[0] == size[1], 'Close button width and height must be equal!'
        self.setText(text)
        self.setFixedSize(*size)
        self.setVisible(visible)
        # self.setMinimumWidth(size[0])
        self.setStyleSheet('''
            _CloseButton {
                border: 1px solid #FF9999;
                border-radius: 5px;
                background-color: #FF9999;
                color: white;
                vertical-align: middle;
                padding: 3px;
            }
            _CloseButton:hover {
                background-color: #FF0000;
            }
            _CloseButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #dadbde, stop: 1 #f6f7fa);
            }
        ''')


class BookmarkButton(QtWidgets.QFrame):
    signal_bttn_clicked = QtCore.pyqtSignal(str)
    signal_close_bttn = QtCore.pyqtSignal()
    PADDING = 20

    def __init__(self, parent, obj_name, exer_id, text):
        super().__init__(parent)
        # ----- Properties ------
        self.setObjectName(obj_name)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM)
        self.setStyleSheet("""
        BookmarkButton {
            color: white;
            border: 1px solid %s;
            border-radius: 5px;
            background-color: %s;
        }
        BookmarkButton:hover {
            background-color: %s;
        }
        BookmarkButton:disabled {
            background-color: %s;
            color: black;
        }
        """ % (Colors.BTTN.hex,
               Colors.BTTN.hex,
               Colors.BTTN_HOVER.hex,
               Colors.BTTN_DISABLED.hex))
        # ----- Data -----
        self.exer_id = exer_id
        # ----- GUI children -----
        self.hbox_layout = None
        self.label = None
        self.close_bttn = None
        # ----- Init Gui -----
        self._init_ui(text)
        # ----- Connect events to slots -----
        self.close_bttn.clicked.connect(lambda: self.signal_close_bttn.emit())

    def _init_ui(self, text):
        self.label = QtWidgets.QLabel(self)
        self.label.setText(text)
        self.close_bttn = _CloseButton(self, 'x', (16, 16), visible=False)
        self.close_bttn.setVisible(False)
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.addWidget(self.label)
        self.hbox_layout.addWidget(self.close_bttn)
        self.setLayout(self.hbox_layout)

    def click(self):
        self.close_bttn.setVisible(False)
        self.signal_bttn_clicked.emit(self.objectName())

    # ----- SLOTS -----

    def enterEvent(self, event):
        """
        :param event: <QtGui.QEnterEvent>
        :return:
        """
        if self.isEnabled():
            self.close_bttn.setVisible(True)

    def leaveEvent(self, event):
        self.close_bttn.setVisible(False)

    def mousePressEvent(self, event):
        if event.button() == MouseButton.LEFT.value:
            self.click()


class FilterButton(QtWidgets.QPushButton):

    def __init__(self, parent, obj_name, text, enabled=True):
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setText(text)
        self.setEnabled(enabled)
        self.setStyleSheet("""
            FilterButton {
                padding: 5px 10px;
                border-radius: 5px;
                border: 1px solid MediumSeaGreen;
                background-color: MediumSeaGreen;
                color: white;
            }
            FilterButton:hover {
                border: 1px solid ForestGreen;
                background-color: ForestGreen;
            }
            FilterButton:pressed {
                border: 1px solid grey;
                border-style: inset;
                background-color: gray;
            }
            FilterButton:disabled {
                border: 1px solid grey;
                background-color: gray;
            }
        """)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))


class RadioButton(QtWidgets.QRadioButton):
    def __init__(self, parent, value, text, checked=False):
        super().__init__(parent)
        self.setText(text)
        self.setChecked(checked)
        # Data
        self.value = value


class RadiobuttonBox(QtWidgets.QFrame):
    signal_rb_clicked = QtCore.pyqtSignal()

    def __init__(self, parent, obj_name, rb_data, checked_rb_index=0,
                 visible=True, orientation=Orientation.VERTICAL):
        """
        :param parent: Instance of <QtWidgets.QWidget>
        :param rb_data: <Iterable> Iterable of tuples->(rb_value, rb_text)
        :param checked_rb_index: <int> Index of checked radiobutton
        :param orientation: <QtCore.Qt.Orientation> Flag for widgetorientation
        NOTE: In this class, read "rb" as "radiobutton"
        """
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setVisible(visible)
        self.setSizePolicy(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM)
        # ----- Data -----
        self.checked_value = None
        self.radiobuttons = []
        # ----- GUI children -----
        class_layout = QtWidgets.QVBoxLayout if orientation == Orientation.VERTICAL \
            else QtWidgets.QHBoxLayout
        self.layout = class_layout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        for i, rb_value_text in enumerate(rb_data):
            checked = True if i == checked_rb_index else False
            rb = RadioButton(self, rb_value_text[0], rb_value_text[1], checked=checked)
            rb.toggled.connect(self._rb_clicked)
            if i == checked_rb_index:
                self.checked_value = rb.value
            self.radiobuttons.append(rb)
            self.layout.addWidget(rb)
        self.setLayout(self.layout)

    def set_checked(self, rb_value):
        for rb in self.radiobuttons:
            if rb_value == rb.value:
                rb.setChecked(True)
                return
        raise ValueError(f'Can\'t set value. No radiobutton with value "{rb_value}" found')

    def _rb_clicked(self):
        self.checked_value = self.sender().value
        self.signal_rb_clicked.emit()


class DialogButtonBox(QtWidgets.QFrame):
    signal_accepted = QtCore.pyqtSignal()
    signal_rejected = QtCore.pyqtSignal()

    def __init__(self, parent, bttn_accept_text, bttn_reject_text=None,
                 bttn_action_dict=None, align_flag=AlignFlag.Right):
        """
        :param parent: <QtWidgets.QWidget> Instance of QWidget
        :param bttn_accept_text: <str> Button accept text
        :param bttn_reject_text: <str> Button reject text
        :param bttn_action_dict: <dict> Dict with 1 item(if set): Key=button text, Value: method
        """
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        # ----- GUI children -----
        self.hbox_layout = None
        self.bttn_accept = None
        self.bttn_reject = None
        self.bttn_action = None
        self._init_ui(bttn_accept_text, bttn_reject_text=bttn_reject_text, bttn_action_dict=bttn_action_dict,
                      align_flag=align_flag)
        # ----- Connect events to slots .....
        self.bttn_accept.clicked.connect(lambda: self.signal_accepted.emit())
        if bttn_reject_text:
            self.bttn_reject.clicked.connect(lambda: self.signal_rejected.emit())
        if bttn_action_dict:
            _, bttn_action_meth = tuple(bttn_action_dict.items())[0]
            self.bttn_action.clicked.connect(bttn_action_meth)

    def _init_ui(self, bttn_accept_text, bttn_reject_text=None, bttn_action_dict=None,
                 align_flag=AlignFlag.Right):
        self.bttn_accept = QtWidgets.QPushButton(self)
        self.bttn_accept.setText(bttn_accept_text)
        if bttn_reject_text:
            self.bttn_reject = QtWidgets.QPushButton(self)
            self.bttn_reject.setText(bttn_reject_text)
        if bttn_action_dict:
            bttn_action_text, _ = tuple(bttn_action_dict.items())[0]
            self.bttn_action = QtWidgets.QPushButton(self)
            self.bttn_action.setText(bttn_action_text)
        # ----- Set layout -----
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.addWidget(self.bttn_accept)
        for bttn in (self.bttn_reject, self.bttn_action):
            if bttn:
                self.hbox_layout.addWidget(bttn)
        self.hbox_layout.setAlignment(align_flag)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.hbox_layout)
