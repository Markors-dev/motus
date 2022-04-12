from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from util import images
from gui.flags import SizePolicy, AlignFlag, ImageFp
from gui.font import FontFlag
from gui.util import get_value
from ._labels import MyLabel


class Image(QtWidgets.QLabel):
    def __init__(self, parent, obj_name, image, tooltip, visible=True,
                 cont_margins=None):
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setVisible(visible)
        if type(image) == bytes:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(image)
        else:  # image == "image filepath"
            pixmap = QtGui.QPixmap(image)
        self.setPixmap(pixmap)
        self.setToolTip(tooltip)
        if cont_margins:
            self.setContentsMargins(*cont_margins)


class ImageWithText(QtWidgets.QWidget):
    def __init__(self, parent, obj_name, text, image_bytes=None, visible=True,
                 hide_no_image=False):
        super().__init__(parent)
        # ---- Data ----
        self.image_bytes = None
        self.image_set = True if image_bytes else False
        self.hide_no_image = hide_no_image
        # ----- Props -----
        self.setObjectName(obj_name)
        self.setVisible(visible)
        self.setSizePolicy(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM)
        # -----Gui children -----
        self.vbox_layout = None
        self.image = None
        self.text = None
        # Initialize GUI
        self._init_ui(text)
        # Post init actions
        self.set_data(image_bytes)

    def _init_ui(self, text):
        self.image = QtWidgets.QLabel(self)
        self.text = MyLabel(self, 'caption', text, font_flag=FontFlag.SMALL_TEXT_BOLD)
        self.text.setAlignment(AlignFlag.HCenter)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(self.image)
        self.vbox_layout.addWidget(self.text)
        self.setLayout(self.vbox_layout)

    def get_data(self):
        if self.image_set:
            return self.image_bytes
        else:
            return None

    def set_data(self, image_bytes=None):
        if image_bytes:
            self.image_bytes = image_bytes
            visible = True
            self.image_set = True
        else:
            self.image_bytes = images.get_file_binary(ImageFp.NO_IMAGE)
            visible = True if not self.hide_no_image else False
            self.image_set = False
        image_pixmap = QtGui.QPixmap()
        image_pixmap.loadFromData(self.image_bytes)
        self.image.setPixmap(image_pixmap)
        self.setVisible(visible)
