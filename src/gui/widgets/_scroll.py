from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from gui.flags import Orientation, SizePolicy, ScrollBarPolicy


class MyScrollBar(QtWidgets.QScrollBar):
    FLAG_MOVE_UP = 'up'
    FLAG_MOVE_DOWN = 'down'
    MOVE_UP_LENGHT = -1
    MOVE_DOWN_LENGHT = 1

    def __init__(self, parent,  enabled=True):
        super().__init__(parent)
        style_sheet = """
        QScrollBar:vertical {
            border: 0px;
            /*background-color: rgb(59, 59, 90);*/
            background-color: rgb(98,198,221);
            width: 10px;
            margin: 0px, 0px, 0px, 0px;
            border-radius: 8px;   
        }
        QScrollBar:horizontal {
            border: 0px solid rgb(0, 0, 0);
            /*background-color: rgb(59, 59, 90);*/
            background-color: rgb(98,198,221);
            height: 10px;
            margin: 0px, 0px, 0px, 0px;
            border-radius: 0px;   
        }
        QScrollBar::handle:vertical{
            background-color: rgb(80, 80, 122);
            min-height: 30px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background-color: rgb(80, 80, 122);
            min-width: 30px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
            background-color: rgb(255, 0, 127);                
        }
        QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed{
            background-color: rgb(185, 0, 92); 
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
        }


        /*
        QScrollBar::sub-line:vertical{
            border: none;
            background-color: rgb(59, 59, 90); 
            height: 15px;
            border-top-left-radius: 7px;
            border-top-right-radius: 7px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }*/
        """
        self.setStyleSheet(style_sheet)
        self.setEnabled(enabled)

    def move_bar(self, move_lenght):
        self.setValue(self.value() + move_lenght)


class ScrollArea(QtWidgets.QScrollArea):
    def __init__(self, parent, orientation=Orientation.HORIZONTAL):
        super().__init__(parent)
        self.setObjectName('scroll_area')
        self.setContentsMargins(0, 0, 0, 0)
        # Set size policy
        _hor_size_policy = SizePolicy.EXPANDING if orientation == Orientation.HORIZONTAL else \
            SizePolicy.MINIMUM
        _vert_size_policy = SizePolicy.EXPANDING if orientation == Orientation.VERTICAL else \
            SizePolicy.MINIMUM
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        #
        self.setWidgetResizable(True)
        _hor_bar_enabled = True
        _vert_bar_enabled = True
        if orientation == Orientation.HORIZONTAL:
            self.setHorizontalScrollBarPolicy(ScrollBarPolicy.AsNeeded)
            self.setVerticalScrollBarPolicy(ScrollBarPolicy.AlwaysOff)
            _vert_bar_enabled = False
        else:  # == Orientation.VERTICAL
            self.setHorizontalScrollBarPolicy(ScrollBarPolicy.AlwaysOff)
            self.setVerticalScrollBarPolicy(ScrollBarPolicy.AsNeeded)
            _hor_bar_enabled = False
        self.setHorizontalScrollBar(MyScrollBar(self, enabled=_hor_bar_enabled))
        self.setVerticalScrollBar(MyScrollBar(self, enabled=_vert_bar_enabled))
