from PyQt5 import QtWidgets
from PyQt5 import QtCore


from util import images
from web.download import get_content_from_url
from gui.flags import SizePolicy, AlignFlag, ImageFp
from gui.dialogs import ErrorMessage, QuestionDialog, get_filepath_from_dialog
from gui.widgets import (
    HBoxPane, RoundPushButton, ImageWithText, CropImageDialog, InputTextDialog
)
from gui.util import set_value, get_value


class InputImageWithText(QtWidgets.QFrame):
    signal_image_set = QtCore.pyqtSignal()

    def __init__(self, parent, obj_name, text, image_bytes=None, enabled=True,
                 create_bttn_delete=False, min_width=None, min_height=None):
        super().__init__(parent)
        self.setObjectName(obj_name)
        # self.setStyleSheet('border: 1px solid black;')
        self.setSizePolicy(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM)
        self.setEnabled(enabled)
        # ----- Data -----
        self.min_width = min_width
        self.min_height = min_height
        # ----- GUI children -----
        self.vbox_layout = None
        self.bttn_import_pc = None
        self.bttn_import_url = None
        self.bttn_delete = None
        self.image_with_text = None
        self._init_ui(text, image_bytes, create_bttn_delete=create_bttn_delete)
        # ----- Connect events to slots -----
        self.bttn_import_pc.clicked.connect(self._import_image_from_pc)
        self.bttn_import_url.clicked.connect(self._import_image_from_url)
        if create_bttn_delete:
            self.bttn_delete.clicked.connect(self._delete_image)

    def _init_ui(self, text, image_bytes=None, create_bttn_delete=False):
        self.bttn_import_pc = RoundPushButton(
            self, 'bttn_import_pc', 'Import image from PC')
        self.bttn_import_url = RoundPushButton(
            self, 'bttn_import_url', 'Import image from URL')
        _bttns = (self.bttn_import_pc, self.bttn_import_url)
        _align_flags = (AlignFlag.Center, AlignFlag.Center)
        if create_bttn_delete:
            self.bttn_delete = RoundPushButton(self, 'bttn_delete', 'Delete image')
            _bttns += (self.bttn_delete, )
            _align_flags += (AlignFlag.Center, )
        _bttn_row = HBoxPane(
            self, _bttns, align_flags=_align_flags, cont_margins=(0, 0, 0, 0))
        self.image_with_text = ImageWithText(
            self, 'image_text', text, image_bytes=image_bytes)
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.addWidget(_bttn_row)
        self.vbox_layout.addWidget(self.image_with_text)
        self.vbox_layout.setAlignment(self.image_with_text, AlignFlag.Center)
        self.setLayout(self.vbox_layout)

    def _check_format_and_save_image(self, image_bytes):
        # ----- Check image size and type -----
        _image_size = images.get_image_bytes_size(image_bytes)
        if self.min_height and _image_size.height() < self.min_height:
            _msg = f'Image height is too small\n' \
                   f'Minimum height must be: {self.min_height} pixels'
            ErrorMessage('Import image failed', _msg).exec()
            return
        if self.min_width and _image_size.width() < self.min_width:
            _msg = f'Image height is too small\n' \
                   f'Minimum height must be: {self.min_width} pixels'
            ErrorMessage('Import image failed', _msg).exec()
            return
        if not images.verify_image_bytes(image_bytes):
            _msg = f'Image type is not supported\n ' \
                   f'Supported formats: {images.PROJ_SUPPORTED_IMG_EXTENSIONS}'
            ErrorMessage('Import image failed', _msg).exec()
            return
        # ----- Format image -----
        resized_image_bytes = images.resize_image_bytes_prop(
            image_bytes, images.ImageDim.HEIGHT, images.MAX_IMAGE_HEIGHT)
        _resized_image_bytes_width = images.get_image_bytes_size(resized_image_bytes).width()
        if _resized_image_bytes_width > images.MAX_IMAGE_WIDTH:
            _msg = 'Imported image width is too big. Do you want to crop it?'
            crop = QuestionDialog('Crop imported image', _msg).exec()
            if not crop:
                return
            crop_dialog = CropImageDialog(
                'Crop position image', resized_image_bytes, images.MAX_IMAGE_WIDTH,
                images.MAX_IMAGE_HEIGHT - 1)
            cropped = crop_dialog.exec()
            if not cropped:
                return
            new_image_bytes = crop_dialog.get_cropped_image_bytes()
        else:
            new_image_bytes = resized_image_bytes
        # ----- Save image -----
        set_value(self.image_with_text, new_image_bytes)
        self.signal_image_set.emit()

    # ----- SLOTS -----

    def _delete_image(self):
        self.image_with_text.set_data()

    def _import_image_from_pc(self):
        image_fp = get_filepath_from_dialog(self, file_types='Image Files (*.jpg *.jpeg *.png)')
        if image_fp:
            image_bytes = images.import_image_from_pc(image_fp)
            if not image_bytes:
                _msg = f'Can\'t import image motfile "{image_fp}"'
                ErrorMessage('Import image failed', _msg).exec()
            self._check_format_and_save_image(image_bytes)

    def _import_image_from_url(self):
        input_dialog = InputTextDialog(
            'Input image URL', 'Insert image url from web: ', ImageFp.URL)
        accept = input_dialog.exec()
        if not accept:
            return
        url = get_value(input_dialog.line_input)
        if url.split('.')[-1] not in images.PROJ_SUPPORTED_IMG_EXTENSIONS:
            _msg = f'Image url "{url}" is not valid.\n\n' \
                   f'Image extension must be in: ' \
                   f'{images.PROJ_SUPPORTED_IMG_EXTENSIONS}'
            ErrorMessage('Download image failed', _msg).exec()
            return
        image_bytes = get_content_from_url(url)
        if image_bytes:
            self._check_format_and_save_image(image_bytes)
