from pathlib import Path
from enum import Enum

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from settings import Settings


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
    """Returns value of a QWidget object

    :param widget <QWidget>
    :return <object> Can be: text, image bytes, checked value, etc.
    """
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
    """Set value of a QWidget object

    The value can be: text, image bytes, checked value, etc.

    :param widget <QWidget>
    :return <None>
    """
    setter_classes = tuple(widget_class_setter_dict.keys())
    for class_ in type(widget).mro():
        class_name = class_.__name__
        if class_name in setter_classes:
            widget_setter = widget_class_setter_dict[class_name]
            widget_setter(widget, *args)
            return
    raise ValueError(f'Class {widget.__class__.__name__} is not registered for '
                     f'method "set_value\n---> Registered setter class names: {setter_classes}"')


def get_parent(widget, obj_name):
    """Returns widget parent by searching object name

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


def get_label_width(text, font=None):
    """Calculates and returns width of label text

    :param text <str> Label text
    :param font <None> or <QtGui.QFont> Default font is used if not given
    :return <int> Label width
    """
    label = QtWidgets.QLabel()
    if font:
        label.setFont(font)
    label.setText(text)
    return label.fontMetrics().boundingRect(label.text()).width()


def get_center_pos(window):
    """Calculates and returns position(top-left point) of a centered widget

    :window <QtWidgets.QWidget>
    :return <QtCore.QPoint>
    """
    main_display = Settings().getValue('main_display')
    disp_geo = Settings().getValue(f'{main_display}_geometry')
    center_pos = QtCore.QPoint(disp_geo[0] + disp_geo[2] // 2 - window.width() // 2,
                               disp_geo[1] + disp_geo[3] // 2 - window.height() // 2)
    return center_pos


def find_button_by_text(bttn_iter, text, get_none=False, substr=True):
    """Find and returns unique button by looking button text

    If parameter 'get_none' is True, function returns None if widget is not
    found or is not unique in iterable.
    If parameter 'substr' is True, it searches button text substrings.

    :param bttn_iter <list> or <tuple> Iterable of button widgets
    :param text <str> Text to search in button text
    :param get_none <bool>
    :param substr <bool>
    :return <QtWidgets.QPushButton> or <None>
    """
    text = text.lower()
    if substr:
        def _text_check(_bttn_text, _text): return _text in _bttn_text
    else:
        def _text_check(_bttn_text, _text): return _bttn_text == _text
    bttns = [bt for bt in bttn_iter if _text_check(bt.text().lower(), text)]
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
    """Find and returns unique widget by looking attribute value

    If parameter 'get_none' is True, function returns None if widget is not
    found or is not unique in iterable.

    :param widget_iter <list> or <tuple> Iterable of widgets
    :param attr_name <str> Attribute name
    :param attr_val <object> Attribute value
    :param get_none <bool>
    :return <QtWidgets.QWidget> or <None>
    """
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


def set_widget_property(widget, prop_name, prop_value):
    widget.setProperty(prop_name, prop_value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
