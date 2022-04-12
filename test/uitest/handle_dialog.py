import time

from PyQt5 import QtGui

from gui.util import get_value, set_value, find_button_by_text, find_widget_by_attr


def handle_info_dialog(widget):
    # start = time.time()
    assert getattr(widget, 'info_dialog'), f'Widget <{widget}> doesn\'t have "info_dialog"'
    while widget.info_dialog is None:
        QtGui.QGuiApplication.processEvents()
        # if time.time() - start > 1.0:
        #
    bttn_ok = find_button_by_text(widget.info_dialog.button_box.buttons(), 'OK')
    bttn_ok.click()


# TODO: maybe implement
# def handle_question_dialog(widget, answer='Yes'):
#     assert getattr(widget, 'question_dialog'), f'Widget <{widget}> doesn\'t have "question_dialog"'
#     while widget.question_dialog is None:
#         QtGui.QGuiApplication.processEvents()
#     bttn = find_button_by_text(widget.question_dialog.button_box.buttons(), answer)
#     # QtCore.QTimer.singleShot(100, handle_info_dialog)
#     QtCore.QTimer.singleShot(100, lambda: handle_info_dialog(tab_plans))
#     bttn_yes.click()
