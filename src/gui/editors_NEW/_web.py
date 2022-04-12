from enum import Enum
from functools import partial

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from gui.widgets import (
    ImageButton, HBoxPane, MyLabel, TitleLabel, ScrollArea, TextEdit,
    Image,
)
from gui.flags import AlignFlag, SizePolicy, ImageFp, Orientation
from gui.font import FontFlag
from gui.util import get_value, set_value
from workout import instruction_text_valid, INSTRUCTION_STEP_TEXT_CHECK_ERROR_MSG


class ListType(Enum):
    Ordered = 0
    Unordered = 1


def _get_html_text_from_data(browser_data):
    html_text = ''
    for list_data in browser_data.split('|'):
        header_text, items_text = list_data.split(':')
        if not items_text:
            continue  # No items in this list
        orderer_list = True if header_text == 'STEPS' else False
        header_text = header_text.title()
        html_text += f'<h2><b>{header_text}:</b></h2>\n'
        list_start_tag, list_end_tag = ('<ol>', '</ol>') if \
            orderer_list else ('<ul>', '</ul>')
        html_text += f'{list_start_tag}\n'
        for item_text in items_text.split(','):
            tab = '\t'.expandtabs(2)
            # item_label = f'{tab}{i + 1}.' if orderer_list else f'{tab}*'
            html_text += f'{tab}<li>{item_text}</li>\n'
        html_text += f'{list_end_tag}\n'
    return html_text


class _ListItem(QtWidgets.QWidget):
    _base_css = """
    TextEdit:focus {
        border: 2px solid green;
        border-radius: 2px;
    }
    """
    _valid_text_css = """
    TextEdit {
        border: 1px solid black;
        border-radius: 2px;
        background-color: white;
    }
    """ + _base_css
    _invalid_text_css = """
    TextEdit {
        border: 1px solid black;
        border-radius: 2px;
        background-color: red;
    }
    """ + _base_css

    signal_remove_item = QtCore.pyqtSignal(int)

    def __init__(self, parent, list_type, index, text):
        super().__init__(parent)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.MAXIMUM)
        # ----- Data -----
        self.list_type = list_type
        self.text_valid = None
        self.index = index
        # ----- GUI children -----
        self.hbox_layout = None
        self.label = None
        self.text_edit = None
        self.bttn_remove = None
        # ----- init UI -----
        self._init_ui(text)
        # ----- Connect events to slots -----
        self.bttn_remove.clicked.connect(lambda: self.signal_remove_item.emit(self.index))
        self.text_edit.textChanged.connect(self._text_changed)
        # ----- Post init actions -----
        self._validate_text()

    def _init_ui(self, text):
        label_text = '*' if self.list_type == ListType.Unordered else f'{self.index + 1}.'
        self.label = MyLabel(self, 'label', label_text, font_flag=FontFlag.SMALL_TEXT,
                             align_flag=AlignFlag.VCenter,
                             size_policy=(SizePolicy.MAXIMUM, SizePolicy.MAXIMUM))
        self.text_edit = TextEdit(self, 'edit', text, font_flag=FontFlag.SMALL_TEXT, height=40)
        self.bttn_remove = ImageButton(self, 'bttn_remove', ImageFp.DELETE_SMALL, 'Delete item')
        # ----- Set layout -----
        self.hbox_layout = QtWidgets.QHBoxLayout(self)
        self.hbox_layout.setContentsMargins(0, 0, 0, 0)
        self.hbox_layout.addWidget(self.label)
        self.hbox_layout.addWidget(self.text_edit)
        self.hbox_layout.addWidget(self.bttn_remove)
        self.setLayout(self.hbox_layout)

    def set_index(self, index):
        self.index = index
        if self.list_type == ListType.Ordered:
            self.label.setText(f'\t{self.index + 1}.'.expandtabs(4))

    def _validate_text(self):
        step_text_lines = get_value(self.text_edit).replace('\n', '')
        if instruction_text_valid(step_text_lines):
            self.text_edit.setStyleSheet(self._valid_text_css)
            self.text_valid = True
        else:
            self.text_edit.setStyleSheet(self._invalid_text_css)
            self.text_valid = False

    def _text_changed(self):
        self._validate_text()


class _TextList(QtWidgets.QWidget):
    signal_text_changed = QtCore.pyqtSignal()

    def __init__(self, parent, header_text, list_type, items_texts):
        super().__init__(parent)
        self.setContentsMargins(5, 0, 5, 0)
        # ----- Data -----
        self.list_type = list_type
        self.header_text = header_text
        # ----- GUI children -----
        self.vbox_layout = None
        self.header = None
        self.bttn_add_step = None
        self.items = []
        self._init_ui(items_texts)
        # ----- Connect events to slots -----
        self.bttn_add_step.clicked.connect(partial(self._add_item, ''))

    def _init_ui(self, items_texts):
        _header_text = f'<b>{self.header_text}</b>:'
        self.header = MyLabel(self, 'label_header', _header_text,
                              font_flag=FontFlag.SMALL_TEXT_BOLD)
        self.bttn_add_step = ImageButton(self, 'add_bttn', ImageFp.PLUS, 'Add new item')
        header_row = HBoxPane(self, (self.header, self.bttn_add_step),
                              cont_margins=(0, 0, 0, 0))
        # ----- Set layout -----
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setAlignment(AlignFlag.Top)
        self.vbox_layout.addWidget(header_row)
        for item_text in items_texts:
            self._add_item(item_text)
        self.setLayout(self.vbox_layout)

    def get_data(self):
        data_str = self.header_text.upper() + ':'
        item_text_index = 0  # indexes for only items with any text
        for item in self.items:
            item_text = get_value(item.text_edit).replace('\n', '')
            if item_text:
                data_str += ',' if item_text_index > 0 else ''
                data_str += item_text
                item_text_index += 1
        return data_str

    def set_data(self, list_text):
        # ---- Remove all items ----
        for i in range(len(self.items) - 1, -1, -1):
            self._remove_item(i)
        # ---- Add new items ----
        items_texts = list_text.split(':')[1]
        if items_texts:
            for item_text in items_texts.split(','):
                self._add_item(item_text)

    def _remove_item(self, index):
        item_index = index + 1  # 1st item(header) must be ignored
        item = self.vbox_layout.itemAt(item_index)
        item.widget().deleteLater()
        self.vbox_layout.removeItem(item)
        self.items.pop(index)

    # ----- SLOTS -----

    def _add_item(self, item_text):
        item_index = len(self.items)
        new_item = _ListItem(self, self.list_type, item_index, item_text)
        new_item.text_edit.textChanged.connect(self._list_text_changed)
        self.items.append(new_item)
        self.vbox_layout.addWidget(new_item)
        new_item.signal_remove_item.connect(self._remove_item_clicked)

    def _remove_item_clicked(self, index):
        """Removes item by index, corrects all indexes and signals item change"""
        self._remove_item(index)
        for index, item in enumerate(self.items):
            item.set_index(index)
        self.signal_text_changed.emit()

    def _list_text_changed(self):
        self.signal_text_changed.emit()


class TextBrowserEditPane(QtWidgets.QWidget):
    """
    Data format:
    'STEPS:Step 1,Step 2|NOTES:|VARIATIONS:Exercise 2'

    """
    def __init__(self, parent, browser_data=None, visible=True):
        super().__init__(parent)
        self.setVisible(visible)
        self.setSizePolicy(SizePolicy.MINIMUM, SizePolicy.MINIMUM)
        # ----- Data -----
        self.text_valid = None
        # ----- GUI children -----
        self.vbox_layout = None
        self.message_row = None
        self.steps_list = None
        self.notes_list = None
        self.variations_list = None
        # ----- Initialize UI -----
        self._init_ui(browser_data)
        # ----- Connect events to slots -----
        self.steps_list.signal_text_changed.connect(self._list_text_changed)
        self.notes_list.signal_text_changed.connect(self._list_text_changed)
        self.variations_list.signal_text_changed.connect(self._list_text_changed)

    def _init_ui(self, browser_data=None):
        message = MyLabel(self, 'label', '*step text input invalid: ', font_flag=FontFlag.SMALL_TEXT,
                          cont_margins=(0, 0, 0, 0))
        bttn_message_info = Image(
            self, 'im_msg_info', ImageFp.INFO_SMALL, INSTRUCTION_STEP_TEXT_CHECK_ERROR_MSG,
            cont_margins=(0, 0, 0, 0))
        self.message_row = HBoxPane(self, (message, bttn_message_info), visible=False,
                                    cont_margins=(5, 5, 5, 5))
        _size_policy = QtWidgets.QSizePolicy()
        _size_policy.setRetainSizeWhenHidden(False)
        self.message_row.setSizePolicy(_size_policy)
        self.message_row.setVisible(False)
        if browser_data:
            steps_data, notes_data, variations_data = browser_data.split('|')
            steps_items_text = steps_data.split(':')[1].split(',')
            notes_items_text = notes_data.split(':')[1].split(',')
            variations_items_text = variations_data.split(':')[1].split(',')
        else:
            steps_items_text = tuple()
            notes_items_text = tuple()
            variations_items_text = tuple()
        self.steps_list = _TextList(
            self, 'Steps', ListType.Ordered, steps_items_text)
        self.notes_list = _TextList(
            self, 'Notes', ListType.Unordered, notes_items_text)
        self.variations_list = _TextList(
            self, 'Variations', ListType.Unordered, variations_items_text)
        # ----- Set layout -----
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setContentsMargins(0, 0, 0, 0)
        self.vbox_layout.setAlignment(AlignFlag.Top)
        self.vbox_layout.addWidget(self.message_row)
        self.vbox_layout.addWidget(self.steps_list)
        self.vbox_layout.addWidget(self.notes_list)
        self.vbox_layout.addWidget(self.variations_list)
        self.vbox_layout.setSpacing(0)
        self.setLayout(self.vbox_layout)

    def get_data(self):
        data_str = f'{self.steps_list.get_data()}|' \
                   f'{self.notes_list.get_data()}|' \
                   f'{self.variations_list.get_data()}'
        return data_str

    def set_data(self, browser_data):
        """NOTE: Lookup 'browser_text" format in class doc-string"""
        assert browser_data[:5] in ('STEPS', ''), 'Browser data is not formatted'
        if not browser_data:
            browser_data = 'STEPS:|NOTES:|VARIATIONS:'
        steps_list_data, notes_list_data, variations_list_data = browser_data.split('|')
        self.steps_list.set_data(steps_list_data)
        self.notes_list.set_data(notes_list_data)
        self.variations_list.set_data(variations_list_data)
        self._check_steps_text()

    def _check_steps_text(self):
        for list_ in (self.steps_list, self.notes_list, self.variations_list):
            for item in list_.items:
                if not item.text_valid:
                    self.message_row.setVisible(True)
                    self.text_valid = False
                    return
        self.text_valid = True
        self.message_row.setVisible(False)

    # ----- SLOTS -----

    def _list_text_changed(self):
        self._check_steps_text()


class TextBrowser(QtWidgets.QTextBrowser):
    def __init__(self, parent, browser_data):
        super().__init__(parent)
        self.browser_data = None
        # ----- Post init actions -----
        self.set_data(browser_data)

    def get_data(self):
        return self.browser_data

    def set_data(self, browser_data):
        self.browser_data = browser_data
        browser_html = _get_html_text_from_data(browser_data) if \
            browser_data.startswith('STEPS') else browser_data
        self.setText(browser_html)


class TextBrowserEditor(QtWidgets.QWidget):
    """
    instructions format:
    - [Ordered list]Exercise steps
    - [P]:
        -> Note[Strong]
        -> Notes
        -> Caution
        -> Tip
        -> Variations

    TODO: Implement:
        Steps, Notes, Variations


    Code for getting stats:
    '''
    import re
    regex_pattern = "<[^<>]+>"

    all_html_tags = set()
    ins_start_with_div_tag = 0
    empty_ins = 0
    for name, ins in names_instructions:
        matched_divs = re.findall(regex_pattern, ins)
        if not matched_divs:
            empty_ins += 1
            continue
        div1 = matched_divs[0]
        if div1.startswith('<div') and ins.startswith(div1):
            ins_start_with_div_tag += 1
        for matched_div in set(matched_divs):
            all_html_tags.add(matched_div)
    '''
    Rrsults:
        all_html_tags:
            <div>...</div>,
            <a href="...">...</a>,
            <p>...</p>,
            <strong>...</strong>,
            <ul>...</ul>,
            <ol>...</ol>,
            <li>...</li>,
        Total exercises: 816
        No html tags: 1('Band Seated Calf Raise')
        Only div tags: 195 -> no text

    Code snippets:
    '''
     names_instructions = db.select_from_table('exercises', ('name', 'instructions'))
     '''
    """
    def __init__(self, parent, obj_name, title_text, browser_data):
        super().__init__(parent)
        self.setObjectName(obj_name)
        self.setFixedWidth(500)
        self.setSizePolicy(SizePolicy.EXPANDING, SizePolicy.EXPANDING)
        # ----- Data -----
        self.browser_data_given = True if browser_data.startswith('STEPS') else False
        self.edit_mode = False
        # ----- Gui children -----
        self.vbox_layout = None
        self.title = None
        self.browser = None
        self.browser_edit = None
        self.scroll_area = None
        # ----- init UI -----
        self._init_ui(title_text, browser_data)

    def _init_ui(self, title_text, browser_data):
        self.title = TitleLabel(self, 'title', title_text, round_bottom=False)
        self.browser = TextBrowser(self, browser_data)
        self.browser.setContentsMargins(0, 0, 0, 0)
        edit_browser_data = browser_data if self.browser_data_given else None
        self.browser_edit = TextBrowserEditPane(self, edit_browser_data, visible=False)
        self.scroll_area = ScrollArea(self, orientation=Orientation.VERTICAL)
        self.scroll_area.setWidget(self.browser_edit)
        self.scroll_area.setVisible(False)
        browser_row = HBoxPane(
            self, (self.browser, self.scroll_area), cont_margins=(0, 0, 0, 0))
        self.vbox_layout = QtWidgets.QVBoxLayout(self)
        self.vbox_layout.setSpacing(0)
        self.vbox_layout.addWidget(self.title)
        self.vbox_layout.addWidget(browser_row)
        self.setLayout(self.vbox_layout)

    def set_data(self, browser_data):
        if self.edit_mode:
            set_value(self.browser_edit, browser_data)
        else:  # self.browser_edit.isVisible() == True
            set_value(self.browser, browser_data)

    def get_data(self):
        if self.edit_mode:
            return get_value(self.browser_edit)
        else:
            return get_value(self.browser)

    def activate_edit_mode(self):
        # assert self.browser_data_given,
        # 'Edit mode can't be activated with non formatted browser data!'
        self.edit_mode = True
        self.browser.setVisible(False)
        self.scroll_area.setVisible(True)
        set_value(self.browser_edit, get_value(self.browser))

    def activate_view_mode(self, save=False):
        self.edit_mode = False
        self.browser.setVisible(True)
        self.scroll_area.setVisible(False)
        if save:
            set_value(self.browser, get_value(self.browser_edit))
