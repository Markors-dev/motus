from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from gui.flags import AlignFlag, SizePolicy, ImageFp
from ._buttons import CheckableImageButton
from ._labels import TitleLabel


class HBoxPane(QtWidgets.QWidget):
    DEFAULT_ALIGN = AlignFlag.Left

    def __init__(self, parent, widgets, align_flags=None,
                 visible=True, cont_margins=(0, 0, 0, 0)):
        """
        :param parent: <QtWidgets.QWidget>
        :param widgets: <Iterable> Iterable containing widget or None
                        NOTE: If None is given as widget, an stretch is added in layout
        :param align_flags: <Iterable> Iterable of Align flags
        :param visible: <bool> Widget visibility
        :param cont_margins: <tuple> Widget margins
        """
        super().__init__(parent)
        # ----- Properties -----
        self.setContentsMargins(*cont_margins)
        self.setVisible(visible)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MINIMUM)
        # NOTE: There can be a 'None' object in 'widgets' param
        _actual_widgets = [w for w in widgets if w is not None]
        # ----- Set layout -----
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(*cont_margins)
        widget_index = 0
        for widget in widgets:
            if widget is None:
                self.hbox_layout.addStretch()
                continue
            self.hbox_layout.addWidget(widget)
            if align_flags:
                self.hbox_layout.setAlignment(widget, align_flags[widget_index])
            widget_index += 1
        self.setLayout(self.hbox_layout)


class ResizePane(QtWidgets.QWidget):
    def __init__(self, parent, widget, title='', pane_visible=False):
        super().__init__(parent)
        # self.setStyleSheet("""border: 1px solid black;""")
        self.setContentsMargins(0, 0, 0, 0)
        # GUI children
        self.vbox_layout = None
        self.bttn_resize = None
        self.title = None
        self.main_widget = None
        # Initialize UI
        self._init_ui(widget, title, pane_visible)
        # Connect events to slots
        self.bttn_resize.clicked.connect(self._bttn_resize)

    def _init_ui(self, widget, title, pane_visible):
        self.bttn_resize = CheckableImageButton(self, 'bttn_resize', ImageFp.DOWN_ARROW,
                                                ImageFp.RIGHT_ARROW, f'Hide {title}', f'Show {title}')
        self.title = TitleLabel(self, 'title', title)
        _title_row = HBoxPane(self, (self.bttn_resize, self.title))
        self.main_widget = widget
        self.main_widget.setVisible(pane_visible)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(_title_row)
        self.vbox_layout.addWidget(self.main_widget)
        self.setLayout(self.vbox_layout)

    def _bttn_resize(self):
        visible = False if self.main_widget.isVisible() else True
        self.main_widget.setVisible(visible)
