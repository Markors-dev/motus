from enum import Enum

from PyQt5 import QtGui

from settings import Settings


class FontFlag(Enum):
    # "Texts"
    TINY_TEXT = -1
    TINY_TEXT_BOLD = 0
    SMALL_TEXT = 1
    SMALL_TEXT_BOLD = 2
    NORMAL_TEXT = 3
    NORMAL_TEXT_BOLD = 4
    BIG_TEXT = 5
    BIG_TEXT_BOLD = 6
    # "Titles"
    SMALL_TITLE = 7
    SMALL_TITLE_BOLD = 8
    TITLE = 9
    TITLE_BOLD = 10
    BIG_TITLE = 11
    BIG_TITLE_BOLD = 12
    #
    DEFAULT_FONT = 3  # A.K.A. "NORMAL_TEXT"


class Font:
    PREFFERED_FONTS = [
        'Arial',
        'Calibri',
        'Helvetica',
    ]

    @staticmethod
    def get_font(font_flag=FontFlag.DEFAULT_FONT):
        if font_flag in (FontFlag.TINY_TEXT, FontFlag.TINY_TEXT_BOLD):
            font_size = 6
        elif font_flag in (FontFlag.SMALL_TEXT, FontFlag.SMALL_TEXT_BOLD):
            font_size = 8
        elif font_flag in (FontFlag.NORMAL_TEXT, FontFlag.NORMAL_TEXT_BOLD):
            font_size = 10
        elif font_flag in (FontFlag.BIG_TEXT, FontFlag.BIG_TEXT_BOLD):
            font_size = 12
        elif font_flag in (FontFlag.SMALL_TITLE, FontFlag.SMALL_TITLE_BOLD):
            font_size = 16
        elif font_flag in (FontFlag.TITLE, FontFlag.TITLE_BOLD):
            font_size = 18
        elif font_flag in (FontFlag.BIG_TITLE, FontFlag.BIG_TITLE_BOLD):
            font_size = 20
        else:
            raise ValueError(f'Point size for FontFlag "{font_flag}" is not defined')
        font = QtGui.QFont(Settings().getValue('font_family'), font_size)
        bold = True if font_flag in (0, 2, 4, 6, 8, 10, 12) else False
        if bold:
            # font.setBold(True)
            font.setWeight(600)
        return font

    @staticmethod
    def get_font_families():
        # NOTE: 'Helvetica' is available, although not returned in 'families()'
        families = QtGui.QFontDatabase().families() + ['Helvetica']
        return sorted(families)
