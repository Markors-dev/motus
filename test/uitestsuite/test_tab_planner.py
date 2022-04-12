import pdb
import time
from pathlib import Path

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import pytest
import pytestqt

from settings import Settings
from config import DAYS, PLAN_FILE_EXTENSION
from workout import get_available_generic_plan_name
from gui.util import get_value, set_value, find_button_by_text, find_widget_by_attr


from test.uitest.manip import window
from test.uitest.handle_dialog import handle_info_dialog


# TODO: Add steps for import and load plan actions


def test_tab_planner(window, qtbot):
    # --- Set GUI and vars ---
    tab_planner = window.tab_widget.tab_planner
    plan_editor = tab_planner.right.plan_editor

    # ----- Step 1: Add 5 exercises to table 'Monday'-----
    window.tab_widget.bar.bttn_planner.click()
    list_exercises = tab_planner.exercise_list_viewer.exercises_box.list_exercises
    event_type = QtCore.QEvent.Type.GraphicsSceneMouseDoubleClick
    for row in range(5):
        list_exercises.select_index(row)
        list_exercises.mouseDoubleClickEvent(event_type)
    table = plan_editor.plan_area.workout_areas[0].table
    assert table.model().rowCount() == 5, 'Exercises were NOT added to table'

    # ----- Step 2: Set plan type and name and save plan -----
    tab_planner.right.plan_editor.unsaved_changes = False
    plan_name = get_available_generic_plan_name(prefix='Test ')
    set_value(plan_editor.top_row.title, plan_name)
    set_value(plan_editor.top_row.cb_plan_type, 'HIIT')
    QtCore.QTimer.singleShot(100, lambda: handle_info_dialog(plan_editor))
    plan_editor.top_row.toolbar.bttn_save_as.click()

    # ----- Step 3: Export plan to motfile-----
    QtCore.QTimer.singleShot(100, lambda: handle_info_dialog(plan_editor))
    plan_editor.top_row.toolbar.bttn_export.click()
    export_dir = Settings().getValue('motfiles_folderpath')
    plan_filename = plan_name.replace(' ', '_').lower() + f'.{PLAN_FILE_EXTENSION}'
    exported_plan_path = Path(export_dir).joinpath(plan_filename)
    assert exported_plan_path.exists(), f'Plan "{plan_name}" wasn\'t exported'

    # ----- Step 3: Create plan PDF file -----
    def handle_pdf_settings_dialog():
        while plan_editor.pdf_settings_dialog is None:
            QtGui.QGuiApplication.processEvents()

        QtCore.QTimer.singleShot(100, lambda: handle_info_dialog(plan_editor))
        plan_editor.pdf_settings_dialog.button_box.bttn_accept.click()

    QtCore.QTimer.singleShot(100, handle_pdf_settings_dialog)
    plan_editor.top_row.toolbar.bttn_create_pdf.click()
    plan_pdf_filename = plan_name.replace(' ', '_').lower() + '.pdf'
    export_dir = Settings().getValue('pdf_folderpath')
    plan_pdf_path = Path(export_dir).joinpath(plan_pdf_filename)
    assert plan_pdf_path.exists(), f'Plan "{plan_name}" PDF wasn\'t created'

    # ----- Step 4: Clear plan editor with button New -----
    plan_editor.top_row.toolbar.bttn_new.click()
    assert table.model().rowCount() == 0, 'Exercises were not cleared from table Monday'

    # ----- Step 5: Delete newly created plan -----
    window.tab_widget.bar.bttn_plans.click()
    tab_plans = window.tab_widget.tab_plans
    list_user_plans = tab_plans.user_plan_list_viewer.plan_list
    row = [i for i, row in enumerate(list_user_plans.model().rows) if row.name == plan_name][0]
    list_user_plans.select_index(row)

    def handle_question_dialog():
        while tab_plans.question_dialog is None:
            QtGui.QGuiApplication.processEvents()
        bttn_yes = find_button_by_text(tab_plans.question_dialog.button_box.buttons(), '&Yes')

        # QtCore.QTimer.singleShot(100, handle_info_dialog)
        QtCore.QTimer.singleShot(100, lambda: handle_info_dialog(tab_plans))
        bttn_yes.click()

    QtCore.QTimer.singleShot(100, handle_question_dialog)
    tab_plans.plan_viewer.top_row.toolbar.bttn_delete.click()

    # This is to prevent Save plan dialog
    window.tab_widget.tab_planner.right.plan_editor.unsaved_changes = False
