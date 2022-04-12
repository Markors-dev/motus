from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from gui.flags import SizePolicy
from gui.font import FontFlag, Font
from gui.util import get_label_width


class MyComboBox(QtWidgets.QComboBox):
    def __init__(self, parent, obj_name, items, first_item=None,
                 font_flag=FontFlag.NORMAL_TEXT, size=None, tooltip=None):
        super().__init__(parent)
        # ----- Data -----
        self.items = (first_item,) + items if first_item else items
        # ----- Props -----
        self.setObjectName('my_combo_box')
        self.setObjectName(obj_name)
        self.setFont(Font.get_font(font_flag))
        self.addItems(self.items)
        for i, item in enumerate(self.items):
            _item_text_width = get_label_width(item, font=self.font())
            if _item_text_width > self.width():
                self.setItemData(i, item, QtCore.Qt.ItemDataRole.ToolTipRole)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MAXIMUM)
        if size:
            size = (size.width(), size.height()) if \
                type(size) == QtCore.QSize else size
            if size[0] and not size[1]:
                self.setFixedWidth(size[0])
            elif not size[0] and size[1]:
                self.setFixedHeight(size[1])
            else:
                self.setFixedSize(*size)
        if tooltip:
            self.setToolTip(tooltip)
        self.setStyleSheet("""
            {
                border: 1px solid black;
                border-radius: 2px;
            }
        """)

    def set_filtered(self):
        self.setProperty('background-color', 'white')

    def set_not_filtered(self):
        self.setProperty('background-color', 'green')

    def show_item(self, item_str):
        all_texts = [self.itemText(i) for i in range(len(self))]
        self.setCurrentIndex(all_texts.index(item_str))


class DBComboBox(MyComboBox):
    """Combobox that stores id:item pairs from DB table

    Helps if you need DB table id of item in combobox.
    """
    def __init__(self, parent, obj_name, id_col_dict, first_item=None,
                 font_flag=FontFlag.NORMAL_TEXT, size=None, tooltip=None):
        _items = tuple(id_col_dict.values())
        super().__init__(parent, obj_name, _items, first_item=first_item,
                         font_flag=font_flag, size=size, tooltip=tooltip)
        # ----- Data -----
        self.ids_cols_dict = id_col_dict
        self.first_item = first_item

    def get_item_db_id(self):
        if self.first_item and self.currentText() == self.first_item:
            # first itme is not in DB
            id_ = None
        else:
            id_ = [id_ for id_, col in self.ids_cols_dict.items() if
                   col == self.currentText()][0]
        return id_

    def set_text_by_id(self, id_):
        text = self.ids_cols_dict[id_]
        self.show_item(text)


class FilterDBComboBox(DBComboBox):
    def __init__(self, parent, obj_name, id_col_dict, filter_key,
                 first_item=None, font_flag=FontFlag.NORMAL_TEXT, size=None,
                 tooltip=None):
        super().__init__(parent, obj_name, id_col_dict, first_item=first_item,
                         font_flag=font_flag, size=size, tooltip=tooltip)
        self.setSizePolicy(SizePolicy.MINIMUM, SizePolicy.MAXIMUM)
        self.filtered_value = self.itemText(0)
        self.filter_key = filter_key

    def get_db_filter_dict(self):
        db_id = self.get_item_db_id()
        return {self.filter_key: db_id} if db_id else {}
