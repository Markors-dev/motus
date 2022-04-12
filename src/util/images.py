import io
import logging
from enum import Enum
from PIL import Image, ImageFile, UnidentifiedImageError

from PyQt5 import QtCore

from settings import ICON_SIZES
from gui.flags import ImageFp


# Const
PROJ_SUPPORTED_IMG_EXTENSIONS = ('jpg', 'jpeg', 'png')
MIN_IMAGE_HEIGHT = 250  # For importing
MAX_IMAGE_WIDTH = 450
MAX_IMAGE_HEIGHT = 250


class CropOrientation(Enum):
    LEFT = 1
    TOP = 2
    RIGHT = 3
    BOTTOM = 4
    CENTER = 0

    LANDSCAPE_ORIENTATIONS = (1, 3, 0)
    PORTRAIT_ORIENTATIONS = (2, 4, 0)


class ImageDim(Enum):
    WIDTH = 0
    HEIGHT = 1


def _to_image_bytes(image):
    buf = io.BytesIO()
    format_ = image.format if image.format else 'JPEG'
    image.save(buf, format=format_)
    return buf.getvalue()


def from_bytes_to_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes))


def get_image_bytes_size(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    return QtCore.QSize(*image.size)


def get_icons_dict(image_bytes):
    icons_dict = {}
    for icon_size in ICON_SIZES:
        width, height = icon_size[0], icon_size[1]
        icons_dict[width] = resize_image_bytes(image_bytes, (width, height))
    return icons_dict


def get_file_binary(filepath):
    try:
        with open(filepath, 'rb') as file:
            blob_data = file.read()
    except IOError:
        logging.error(f'Failed reading binary data from motfile "{filepath}"', exc_info=True)
        return False
    return blob_data


def verify_image_bytes(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except PIL.UnidentifiedImageError:
        logging.error('File is not a supported image for this App.', exc_info=True)
        return False
    if image.format.lower() not in PROJ_SUPPORTED_IMG_EXTENSIONS:
        logging.error(f'Image motfile format is not supported for this App.\n'
                      f'Supported image formats: {PROJ_SUPPORTED_IMG_EXTENSIONS}.')
        return False
    return True


def import_image_from_pc(image_fp):
    image_extension = image_fp.split('.')[-1]
    if image_extension not in PROJ_SUPPORTED_IMG_EXTENSIONS:
        logging.error(f'Image motfile "{image_fp}" format is not supported in App\n'
                      f'Supported image extensions: {PROJ_SUPPORTED_IMG_EXTENSIONS}')
        return False
    image_bytes = get_file_binary(image_fp)
    if verify_image_bytes(image_bytes):
        return image_bytes
    return False


def _crop_from_image(image, rect):
    """Crops image with given rect

    :param image: <PIL.Image> Image object
    :param rect: <QtCore.QRect> or tuple(x1, y1, x2, y2) QRect or tuple
    """
    crop_box = rect if type(rect) == tuple else \
        (rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
    cropped_image = image.crop(crop_box)
    return cropped_image


def crop_from_image_bytes(image_bytes, rect):
    """Crops image with given rect

    :param image_bytes: <bytes> Image as bytes object
    :param rect: <QtCore.QRect> Rect object with attributes: x, y, width and height.
    """
    image = Image.open(io.BytesIO(image_bytes))
    cropped_image = _crop_from_image(image, rect)
    cropped_image_bytes = _to_image_bytes(cropped_image)
    return cropped_image_bytes


def _resize_image_prop(orig_image, image_dim, dimension_size):
    """ Proportionally resizes input image using width or height.

    :param orig_image : <PIL.Image> or <bytes> Image object
    :param image_dim: <ImageDim> - Image dimension(WIDTH or HEIGHT)
    :param dimension_size: <int> - Image width or height size
    :return: <PIL.Image> - resized image
    """
    orig_image_width, orig_image_height = orig_image.size
    new_width = dimension_size if image_dim == ImageDim.WIDTH else \
        int(orig_image_width * (dimension_size / orig_image_height))
    new_height = dimension_size if image_dim == ImageDim.HEIGHT else \
        int(orig_image_height * (dimension_size / orig_image_width))
    new_image = orig_image.resize((new_width, new_height), Image.LANCZOS)
    mode = 'RGBA' if new_image.format == 'PNG' else 'RGB'
    new_image = new_image.convert(mode)
    return new_image


def resize_image_bytes_prop(orig_image_bytes, image_dim, dimension_size):
    orig_image = Image.open(io.BytesIO(orig_image_bytes))
    resized_image = _resize_image_prop(orig_image, image_dim, dimension_size)
    resized_image_bytes = _to_image_bytes(resized_image)
    return resized_image_bytes


def resize_image(orig_image, new_size):
    """ Resizes input image.

    :param orig_image: <str> - 'width' or 'height'
    :param new_size: (width, height) - new image size
    :return: <PIL.Image> - resized image
    """
    new_image = orig_image.resize(new_size, Image.LANCZOS)
    return new_image


def resize_image_bytes(orig_image_bytes, new_size):
    """ Resizes input image.

    :param orig_image_bytes: <bytes> - Image bytes
    :param new_size: (width, height) - new image size
    :return: <PIL.Image> - resized image
    """
    orig_image = Image.open(io.BytesIO(orig_image_bytes))
    resized_image = resize_image(orig_image, new_size)
    resized_image_bytes = _to_image_bytes(resized_image)
    return resized_image_bytes


# ----- Below methods were used before - left for possible future use -----


def get_image_size(imagepath):
    im_par = ImageFile.Parser()
    with open(imagepath, "rb") as f:
        chunk = f.read(2048)
        count = 2048
        while chunk != "":
            im_par.feed(chunk)
            if im_par.image:
                break
            chunk = f.read(2048)
            count += 2048
    return im_par.image.size


def crop_square_from_image(orig_image, crop_orientation=CropOrientation.CENTER):
    """Crops image to a square size, preserving width(if image is in portrait) or
    height(if image is in landscape).

    :param orig_image: <PIL.Image> - new image width or height
    :param crop_orientation: <CropOrientation>
    :return: <PIL.Image> - resized square image
    """
    image_width, image_height = orig_image.size
    if image_width == image_height:
        new_image = orig_image  # image is already a square
    elif image_width < image_height:
        assert crop_orientation.value in CropOrientation.PORTRAIT_ORIENTATIONS.value, \
            'Incorrect crop orientation!'
        if crop_orientation == CropOrientation.TOP:
            first_row = 0
        elif crop_orientation == CropOrientation.CENTER:
            first_row = image_height // 2 - image_width // 2
        else:  # crop_orientation == CropOrientation.BOTTOM:
            first_row = image_height - image_width
        new_image = orig_image.crop((0, first_row, first_row + image_width, image_width))
    else:  # image_width > image_height
        assert crop_orientation.value in CropOrientation.LANDSCAPE_ORIENTATIONS.value, \
            'Incorrect crop orientation!'
        if crop_orientation == CropOrientation.LEFT:
            first_column = 0
        elif crop_orientation == CropOrientation.CENTER:
            first_column = image_width // 2 - image_height // 2
        else:  # crop_orientation == CropOrientation.RIGHT:
            first_column = image_width - image_height
        new_image = orig_image.crop((first_column, 0, first_column + image_height, image_height))
    return new_image


def crop_square_from_image_bytes(orig_image_bytes, crop_orientation=CropOrientation.CENTER):
    orig_image = Image.open(io.BytesIO(orig_image_bytes))
    cropped_image = crop_square_from_image(orig_image, crop_orientation=crop_orientation)
    cropped_image_bytes = _to_image_bytes(cropped_image)
    return cropped_image_bytes


def get_next_pos_image(dirpath):
    """Generator that yields motfile paths from some dir who have
    the appropriate int value '_exer_id' written in the 1st part
    of the filename
    """
    _exer_id = None
    get_exer_id = True
    for filename in os.listdir(dirpath)[:20]:
        if get_exer_id:
            _exer_id = yield
        file_exer_id = int(filename.split('_')[0].lstrip('0'))
        if file_exer_id == _exer_id:
            yield os.path.join(dirpath, filename)
            get_exer_id = True
        else:
            get_exer_id = False
