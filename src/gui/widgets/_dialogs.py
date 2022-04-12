from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from util import images
from web.mail import send_email, EMailType
from gui.flags import ImageFp, SizePolicy, LayoutOrientation, ButtonType, AlignFlag
from gui.dialogs import BaseDialog, BaseInfoDialog, InfoMessage
from gui.util import find_button_by_text
from ._buttons import RadiobuttonBox, DialogButtonBox
from ._images import Image
from ._labels import MyLabel
from ._panes import HBoxPane


# ----- Dialogs -----
# NOTE: these dialog classes are located in this module, and not in 'src.gui.dialogs',
# because of their use of custom widgets.


class CropImageDialog(BaseDialog):
    """Dialog for cropping image

    NOTE: this Dialog crops only LEFT, CENTER, RIGHT.
    """

    def __init__(self, title_text, image_bytes, crop_box_width,
                 crop_box_height, reject_bttn=True):
        super().__init__(title_text, icon_fp=ImageFp.EDIT)
        # ----- Data -----
        self._crop_rect = None
        self._orig_image_bytes = image_bytes
        self._crop_box_width = crop_box_width
        self._crop_box_height = crop_box_height
        # ----- GUI children -----
        self.label_cb = None
        self.rb_box_orien = None
        self.image = None
        self.button_box = None
        self.vbox_layout = None
        # ----- Init UI -----
        self._init_ui(image_bytes, reject_bttn=reject_bttn)
        # ----- Connect events to slots -----
        self.rb_box_orien.signal_rb_clicked.connect(self._set_cropped_image)
        self.button_box.signal_accepted.connect(self.accept)
        if reject_bttn:
            self.button_box.signal_rejected.connect(self.reject)
        # ----- Post init actions -----
        self._set_cropped_image()

    def _init_ui(self, image_bytes, reject_bttn=True):
        self.label_cb = MyLabel(self, 'label', 'Select crop orientation: ',
                                size_policy=(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM))
        _rb_data = [
            (images.CropOrientation.LEFT, 'Left'),
            (images.CropOrientation.CENTER, 'Center'),
            (images.CropOrientation.RIGHT, 'Right')
        ]
        self.rb_box_orien = RadiobuttonBox(
            self, 'rb_box', _rb_data, checked_rb_index=1,
            orientation=LayoutOrientation.HORIZONTAL)
        _cb_choose_crop_row = HBoxPane(self, (self.label_cb, self.rb_box_orien))
        self.image = Image(self, 'img', image_bytes, '')
        bttn_reject_text = 'Cancel' if reject_bttn else None
        self.button_box = DialogButtonBox(self, 'OK', bttn_reject_text=bttn_reject_text)
        # ----- Set layout-----
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(_cb_choose_crop_row)
        self.vbox_layout.addWidget(self.image)
        self.vbox_layout.addWidget(self.button_box)
        self.setLayout(self.vbox_layout)

    def get_cropped_image_bytes(self):
        cropped_image_bytes = images.crop_from_image_bytes(self._orig_image_bytes, self._crop_rect)
        return cropped_image_bytes

    def _set_cropped_image(self):
        # Load default image
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(self._orig_image_bytes)
        # Set crop rect
        crop_orien = self.rb_box_orien.checked_value
        if crop_orien == images.CropOrientation.LEFT:
            x = 0
        elif crop_orien == images.CropOrientation.CENTER:
            x = pixmap.width() // 2 - self._crop_box_width // 2
        else:
            x = pixmap.width() - self._crop_box_width
        self._crop_rect = QtCore.QRect(x, 0, self._crop_box_width, self._crop_box_height)
        # Set painter and draw rect
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtCore.Qt.green, 1, QtCore.Qt.SolidLine))
        painter.drawRect(self._crop_rect)
        painter.end()
        self.image.setPixmap(pixmap)


class InputTextDialog(BaseDialog):
    def __init__(self, title, line_edit_text, icon_fp):
        super().__init__(title, icon_fp=icon_fp)
        # ----- Properties -----
        self.setFixedWidth(600)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MAXIMUM)
        # ----- GUI children -----
        self.label = QtWidgets.QLabel(self)
        self.label.setText(line_edit_text)
        self.line_input = QtWidgets.QLineEdit(self)
        self.button_box = DialogButtonBox(self, 'OK', bttn_reject_text='Cancel')
        self.button_box.signal_accepted.connect(self.accept)
        self.button_box.signal_rejected.connect(self.reject)
        # ----- Set layout -----
        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 4)
        self.grid_layout.addWidget(self.label, 0, 0)
        self.grid_layout.addWidget(self.line_input, 0, 1)
        self.grid_layout.addWidget(self.button_box, 1, 1)
        self.setLayout(self.grid_layout)


class LoadListItemDialog(QtWidgets.QDialog):
    def __init__(self, title, list_class):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon(ImageFp.LOAD))
        self.setMinimumWidth(600)
        self.setMaximumWidth(1200)
        self.setMinimumHeight(600)
        self.setMaximumHeight(900)
        # ----- GUI children -----
        self.list_view = list_class(self)
        self.button_box = DialogButtonBox(self, 'OK', bttn_reject_text='Cancel')
        self.button_box.signal_accepted.connect(self.accept)
        self.button_box.signal_rejected.connect(self.reject)
        # ----- Set layout -----
        self.vbox_layout = QtWidgets.QVBoxLayout()
        self.vbox_layout.addWidget(self.list_view)
        self.vbox_layout.addWidget(self.button_box)
        self.setLayout(self.vbox_layout)

    def get_list_item(self):
        load_item = self.exec()
        indexes = self.list_view.selectedIndexes()
        if load_item and indexes:
            list_item = self.list_view.model().rows[indexes[0].row()]
            return list_item
        return False


class CrashReportErrorMessage(BaseInfoDialog):
    def __init__(self, title, text, tb_msg, parent_pos=None):
        bttns = ButtonType.Close | ButtonType.Apply
        _bttn_action_name = 'Send crash report e-mail'
        _bttn_action_dict = {_bttn_action_name: self._send_report}
        super().__init__(title, ImageFp.ERROR, text, bttns,
                         bttn_action_dict=_bttn_action_dict, parent_pos=parent_pos)
        # ----- Data -----
        self.title = title
        self.tb_msg = tb_msg
        # ----- Connect events to slots -----
        bttn_close = find_button_by_text(self.button_box.buttons(), 'Close')
        bttn_close.clicked.connect(self.accept)

    def _send_report(self):
        _mail_text = f'{self.title}\n\n{self.tb_msg}'
        sent = send_email(EMailType.CRASH_REPORT, _mail_text)
        self.close()
        if sent:
            InfoMessage('EMail sent', 'Crash report mail sent').exec()


class ChoiceDialog(QtWidgets.QDialog):
    def __init__(self, item1_text, item2_text):
        super().__init__()
        self.setWindowTitle('Choose')
        self.setWindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint |
                            QtCore.Qt.WindowType.WindowTitleHint)
        self.setWindowIcon(QtGui.QIcon(ImageFp.CHOOSE))
        self.setMinimumWidth(300)
        # ----- Text -----
        self.text = QtWidgets.QLabel(self)
        self.text.setWordWrap(True)
        self.text.setText(f'Choose "{item1_text}" or "{item2_text}"')
        self.text.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MINIMUM)
        self.text.setAlignment(AlignFlag.Left | AlignFlag.VCenter)
        # ----- Button box -----
        self.button_box = DialogButtonBox(self, item1_text, bttn_reject_text=item2_text)
        # ----- Set layout -----
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(self.text)
        self.vbox_layout.addWidget(self.button_box)
        self.setLayout(self.vbox_layout)
        # ----- Connect events to slots -----
        self.button_box.signal_accepted.connect(self.accept)
        self.button_box.signal_rejected.connect(self.reject)
