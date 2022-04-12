from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from gui.dialogs import ErrorMessage
from gui.colors import Colors, ThemeType, Theme
from gui.flags import AlignFlag, SizePolicy
from gui.font import FontFlag, Font
from gui.util import get_label_width


class MyLabel(QtWidgets.QLabel):
    def __init__(self, parent, obj_name, text, font_flag=FontFlag.NORMAL_TEXT,
                 visible=True, align_flag=AlignFlag.Left, size=None,
                 cont_margins=(0, 0, 0, 0),
                 size_policy=(SizePolicy.EXPANDING, SizePolicy.MAXIMUM)):
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setText(text)
        self.setFont(Font.get_font(font_flag))
        self.setVisible(visible)
        self.setContentsMargins(*cont_margins)
        self.setSizePolicy(*size_policy)
        if size:
            self.setFixedSize(QtCore.QSize(*size))
        self.setAlignment(align_flag)


class TitleLabel(MyLabel):
    PADDING_LEFT_RIGHT = 6
    PADDING_TOP_BOTTOM = 10
    BORDER_RADIUS = 10
    PADDING = (4, 20, 4, 20)

    def __init__(self, parent, obj_name, text, font_flag=FontFlag.SMALL_TITLE_BOLD,
                 align_flag=AlignFlag.Center, bg_color=Colors.TITLE.hex, text_color='white',
                 round_bottom=True, size_policy=(SizePolicy.EXPANDING, SizePolicy.MAXIMUM)):
        super().__init__(parent, obj_name, text, font_flag=font_flag, align_flag=align_flag,
                         size_policy=size_policy)
        _bottom_border_radius = 10 if round_bottom else 0
        self.setStyleSheet('''
        TitleLabel {
            padding: %spx %spx %spx %spx;
            border: 1px solid %s;
            border-top-left-radius: %spx;
            border-top-right-radius: %spx;
            border-bottom-left-radius: %spx;
            border-bottom-right-radius: %spx;
            background-color: %s;
            color: %s;
        }
        TitleLabel:disabled {
            background-color: %s;
        }
        ''' % (*self.PADDING, bg_color, self.BORDER_RADIUS, self.BORDER_RADIUS,
               _bottom_border_radius, _bottom_border_radius,
               bg_color, text_color, Colors.CONTAINER.hex))


class DBTitleLabel(TitleLabel):
    def __init__(self, parent, obj_name, _id_name_dict, font_flag=FontFlag.SMALL_TITLE_BOLD,
                 align_flag=AlignFlag.Center, bg_color=Colors.TITLE.hex, text_color='white',
                 size_policy=(SizePolicy.EXPANDING, SizePolicy.MAXIMUM)):
        _first_text = tuple(_id_name_dict.values())[0]
        super().__init__(parent, obj_name, _first_text, font_flag=font_flag,
                         align_flag=align_flag, bg_color=bg_color,
                         text_color=text_color, size_policy=size_policy)
        # ----- Data -----
        self.id_name_dict = _id_name_dict

    def get_item_db_id(self):
        id_ = [id_ for id_, name in self.id_name_dict.items() if name == self.text()][0]
        return id_

    def set_text_by_id(self, id_):
        text = self.id_name_dict[id_]
        self.setText(text)


class InfoGridLabel(MyLabel):
    def __init__(self, parent, obj_name, text, bg_theme):
        super().__init__(parent, obj_name, text)
        self.theme = Theme(bg_theme)
        align_flag = QtCore.Qt.AlignmentFlag
        if bg_theme == ThemeType.DARK:
            font_flag = FontFlag.BIG_TEXT
            align = AlignFlag.Right | AlignFlag.VCenter
            border_radius = 'border-top-left-radius: 5px;' \
                            'border-bottom-left-radius: 5px;'
        else:  # == ThemeType.GREEN
            font_flag = FontFlag.NORMAL_TEXT
            align = AlignFlag.Center | AlignFlag.VCenter
            border_radius = 'border-top-right-radius: 10px;' \
                            'border-bottom-right-radius:10px;'
        self.setFont(Font.get_font(font_flag))
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MINIMUM)
        self.setAlignment(align)
        self.setStyleSheet('''
        InfoGridLabel {
            padding: 5px;
            border: 1px solid %s;
            background-color: %s;
            color: %s;
            %s
        }
        ''' % (self.theme.bg_color,
               self.theme.bg_color,
               self.theme.text_color,
               border_radius))

    def setText(self, text):
        text = '-' if text in (None, '-') else text
        super().setText(text)


class LinkInfoGridLabel(InfoGridLabel):
    def __init__(self, parent, obj_name, url, bg_theme):
        super().__init__(parent, obj_name, url, bg_theme)
        self.setOpenExternalLinks(True)
        self.setText(url)
        # ----- Data -----
        self._url = url

    def setText(self, url):
        self._url = url
        text = f'<a href="{url}">LINK</a>' if url else '-'
        super().setText(text)

    def get_link_value(self):
        return self._url if self._url else None


class ClickableLabel(MyLabel):
    signal_clicked = QtCore.pyqtSignal()

    def __init__(self, parent, obj_name, text, font_flag=FontFlag.NORMAL_TEXT,
                 visible=True, size=None, align_flag=None):
        super().__init__(parent, obj_name, text, font_flag=font_flag,
                         visible=visible, align_flag=align_flag)
        self.setStyleSheet("""
            .ClickableLabel {
                background-color: %s;
                color: white;
                border-radius: 3px;
                padding: 1px, 2px;
            }
            .ClickableLabel:hover {
                background-color: %s;
                color: white;
            }
        """ % (Colors.BTTN.hex, Colors.BTTN_HOVER.hex))

    def mousePressEvent(self, event):
        self.signal_clicked.emit()


class YoutubeLinkLabel(QtWidgets.QLabel):
    EMPTY_VALUE_STR = '-'

    def __init__(self, parent, obj_name, text):
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setOpenExternalLinks(True)
        self.setAlignment(AlignFlag.Center)
        self.setLink(text)

    def setLink(self, text):
        if text == '-' or text is None:
            # No link
            self.setText('-')
            self.setToolTip('')
            return True
        else:
            # link validation
            if not text.startswith('https://www.youtube.com/watch'):
                pos = self.mapToGlobal(self.pos())
                error_message = ErrorMessage('Invalid youtube link',
                                             'Provided link is not a valid youtube link',
                                             pos=pos)
                error_message.exec()
                return False
            else:
                # link is valid youtube url and is set as label
                self.setText(f'<a href="{text}">LINK</a>')
                self.setToolTip(text)
                return True
