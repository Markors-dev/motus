import time
from abc import ABC, abstractmethod
from functools import partial

from PyQt5.QtCore import QTimer, QObject
from PyQt5.QtWidgets import QApplication


class SingleDoubleClickSeparator:
    """Abstrack class for <QtWidgets> subtype classes which need to separate
    mouse single and double click events.
    """
    def __init__(self):
        # super(QObject, self).__init__()
        self.time_ms_last_click = time.time_ns() / 1_000_000
        self.last_click = 'Single'

    def mousePressEvent(self, event):
        self.last_click = 'Single'

    def mouseDoubleClickEvent(self, event):
        if self.last_click == 'Single Click':
            self.last = "Double Click"

    def mouseReleaseEvent(self, event):
        if self.last == "Click":
            QTimer.singleShot(QApplication.instance().doubleClickInterval(),
                              partial(self.performSingleClickAction, event))
        else:
            # Perform double click action.
            self.doubleClickAction(event)

    def performSingleClickAction(self, event):
        if self.last == "Click":
            # Perform single click action.
            self.singleClickAction(event)

    @abstractmethod
    def singleClickAction(self, event):
        pass

    @abstractmethod
    def doubleClickAction(self, event):
        pass


# OLD code
# class SingleDoubleClickSeparator:
#     """Abstrack class for <QtWidgets> subtype classes which need to separate
#     mouse single and double click events.
#     """
#     def __init__(self):
#         # super(QObject, self).__init__()
#         self.last = 'Click'
#
#     def mousePressEvent(self, event):
#         self.last = "Click"
#
#     def mouseDoubleClickEvent(self, event):
#         self.last = "Double Click"
#
#     def mouseReleaseEvent(self, event):
#         if self.last == "Click":
#             QTimer.singleShot(QApplication.instance().doubleClickInterval(),
#                               partial(self.performSingleClickAction, event))
#         else:
#             # Perform double click action.
#             self.doubleClickAction(event)
#
#     def performSingleClickAction(self, event):
#         if self.last == "Click":
#             # Perform single click action.
#             self.singleClickAction(event)
#
#     @abstractmethod
#     def singleClickAction(self, event):
#         pass
#
#     @abstractmethod
#     def doubleClickAction(self, event):
#         pass
