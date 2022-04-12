import pdb
from pathlib import Path
from enum import Enum

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from settings import Settings


def _isinstance_from_str(widget, class_name):
    return True if widget.__class__.__name__ == class_name else False


widget_class_getter_dict = {
    'QLabel': lambda w: w.text(),
    'TextEdit': lambda w: w.toPlainText(),
    'QLineEdit': lambda w: w.text(),
    'QComboBox': lambda w: w.currentText(),
    'QRadioButton': lambda w: w.text(),
    'RadiobuttonBox': lambda w: w.checked_value,
    'CheckableImageButton': lambda w: w.isChecked(),
    'CheckBox': lambda w: w.isChecked(),
    'ValidatedLineEdit': lambda w: w.line_edit.text(),
    'LinkInfoGridLabel': lambda w: w.get_link_value(),
    '_LinkSetButton': lambda w: w.url,
    'ExerciseDataViewEditWidget': lambda w: w.get_data(),
    'ImageWithText': lambda w: w.get_data(),
    'InputImageWithText': lambda w: w.image_with_text.get_data(),
    'WorkoutTimeBox': lambda w: w.time_min,
    'TextBrowser': lambda w: w.get_data(),
    'TextBrowserEditor': lambda w: w.get_data(),
    'TextBrowserEditPane': lambda w: w.get_data(),
}


def get_value(widget):
    getter_classes = tuple(widget_class_getter_dict.keys())
    for class_ in type(widget).mro():
        class_name = class_.__name__
        if class_name in getter_classes:
            widget_getter = widget_class_getter_dict[class_name]
            return widget_getter(widget)
    raise ValueError(f'Class {widget.__class__.__name__} is not registered for '
                     f'method "get_value"')


widget_class_setter_dict = {
    'QLabel': lambda w, val: w.setText(val),
    'QLineEdit': lambda w, val: w.setText(val),
    'TextEdit': lambda w, val: w.setText(val),
    'CheckBox': lambda w, val: w.setChecked(val),
    'QComboBox': lambda w, val: w.setCurrentText(val),
    'ValidatedLineEdit': lambda w, val: w.line_edit.setText(val),
    'RadiobuttonBox': lambda w, val: w.set_checked(val),
    'CheckableImageButton': lambda w, val: w.setChecked(val),
    '_LinkSetButton': lambda w, val: w.set_url(val),
    'ExerciseDataViewEditWidget': lambda w, val: w.set_data(val),
    'ImageWithText': lambda w, val: w.set_data(val),
    'InputImageWithText': lambda w, val: w.image_with_text.set_data(val),
    'WorkoutTimeBox': lambda w, val: w.set_workout_time(val),
    'TextBrowser': lambda w, val: w.set_data(val),
    'TextBrowserEditor': lambda w, val: w.set_data(val),
    'TextBrowserEditPane': lambda w, val: w.set_data(val),
}


def set_value(widget, *args):
    setter_classes = tuple(widget_class_setter_dict.keys())
    for class_ in type(widget).mro():
        class_name = class_.__name__
        if class_name in setter_classes:
            widget_setter = widget_class_setter_dict[class_name]
            # setter_args = (widget, value, *kwargs.values()) if kwargs else (widget, value)
            widget_setter(widget, *args)
            return
    raise ValueError(f'Class {widget.__class__.__name__} is not registered for '
                     f'method "set_value\n---> Registered setter class names: {setter_classes}"')


def get_parent(widget, obj_name):
    """Returns widgets parent by object name.

    If parent is not found, returns None.
    :param widget <QWidget>
    :param obj_name <str>
    :return <QWidget> or None
    """
    parent_widget = widget.parent()
    while parent_widget.objectName() != obj_name:
        parent_widget = parent_widget.parent()
        if isinstance(parent_widget, QtWidgets.QMainWindow):
            return None
    return parent_widget


def get_child_widget(widget, obj_name):
    pytest.set_trace()
    for child_widget in widget.children():
        pass


def get_label_width(text, font=None):
    """Calculates and returns width of label in pixels

    @param: text <str> The text
    @param: font <None> or <QtGui.QFont> Either default font is used or

    """

    label = QtWidgets.QLabel()
    if font:
        label.setFont(font)
    label.setText(text)
    return label.fontMetrics().boundingRect(label.text()).width()


def get_window_center_pos(window):
    main_display = Settings().getValue('main_display')
    display_geometry = Settings().getValue(f'{main_display}_geometry')
    pos = QtCore.QPoint(display_geometry[0] + display_geometry[2] // 2 - window.width() // 2,
                        display_geometry[1] + display_geometry[3] // 2 - window.height() // 2)
    widget_geometry = QtCore.QRect(pos.x(), pos.y(), window.width(), window.height())
    return widget_geometry


def find_button_by_text(bttn_iter, text, get_none=False, substr=True):
    text = text.lower()
    lambda_text_check = lambda _bttn_text, _text: _text in _bttn_text if substr else \
        lambda _bttn_text, _text: _bttn_text == _text
    bttns = [bt for bt in bttn_iter if lambda_text_check(bt.text().lower(), text)]
    if len(bttns) == 0:
        if get_none:
            return None
        raise ValueError(f'Button "{bttn_text}" not found in iterable.')
    elif len(bttns) > 1:
        if get_none:
            return None
        raise ValueError(f'Multiple buttons "{bttn_text}" found in iterable.')
    return bttns[0]


def find_widget_by_attr(widget_iter, attr_name, attr_val, get_none=False):
    widgets = [w for w in widget_iter if getattr(w, attr_name) == attr_val]
    if len(widgets) == 0:
        if get_none:
            return None
        raise ValueError(f'Widget with attr value "{attr_name}"="{attr_val}" '
                         f'not found in iterable.')
    elif len(widgets) > 1:
        if get_none:
            return None
        raise ValueError(f'Multiple widgets with attr value "{attr_name}"="{attr_val}" '
                         f'found in iterable.')
    return widgets[0]


def get_icon_bytes_from_image(image):
    """
    :param image: <PIL.Image>
    :return: <bytes>
    """
    icon_50_bytes = images.resize_image(image, (50, 50)).tobytes()
    icon_60_bytes = images.resize_image(image, (60, 60)).tobytes()
    icon_70_bytes = images.resize_image(image, (70, 70)).tobytes()
    icons_dict = {50: icon_50_bytes, 60: icon_60_bytes, 70: icon_70_bytes}
    return pickle.dumps(icons_dict)
