from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import pytest
import pytestqt

from gui.util import get_value, set_value, find_button_by_text
from test.uitest.manip import window
from test.uitest.handle_dialog import handle_info_dialog


def test_tab_exercises(window, qtbot):
    # --- Set GUI and vars ---
    tab_exercises = window.tab_widget.tab_exercises
    filter_box = tab_exercises.exercise_list_viewer.filter_box
    bttn_resize = tab_exercises.exercise_list_viewer.resize_pane.bttn_resize
    bttn_resize.click()

    # ----- Step 1: set filters and get exercises -----
    set_value(filter_box.cb_exer_type, 'Strength')
    set_value(filter_box.cb_body_part, 'Legs')
    set_value(filter_box.exer_name, 'squat')
    set_value(filter_box.rb_box_favorite, False)
    filter_box.bttn_filter.click()

    # ----- Step 2: Check exercise parameters in list -----
    list_exercises = tab_exercises.list_exercises
    basic_info_row = tab_exercises.exercise_data_editor.exercise_data_viewer.basic_info_row
    for row in range(list_exercises.model().rowCount()):
        list_exercises.select_index(row)
        exer_type = get_value(basic_info_row.row.info_grid.label_type_value)
        body_part = get_value(basic_info_row.row.info_grid.label_body_part_value)
        exer_name = get_value(basic_info_row.title_row.title)
        favorite = get_value(basic_info_row.title_row.bttn_favorite)
        assert exer_type == 'Strength', 'Exercise type is not correct'
        assert body_part == 'Legs', 'Body part is not correct'
        assert 'squat' in exer_name.lower(), 'Exercise name is not correct'
        assert favorite is False, 'Favorite is not correct'
    filter_box.bttn_reset.click()
    filter_box.bttn_filter.click()

    # ----- Step 3: set new filters and get exercises -----
    set_value(filter_box.cb_muscle_group, 'Chest')
    set_value(filter_box.cb_equipment, 'Dumbell')
    set_value(filter_box.rb_box_user_exer, False)
    filter_box.bttn_filter.click()

    # ----- Step 4: Check exercise parameters in list -----
    for row in range(5):
        list_exercises.select_index(row)
        muscle_group = get_value(basic_info_row.row.info_grid.label_main_muscles_value)
        equipment = get_value(basic_info_row.row.info_grid.label_equipment_value)
        user_exercise = basic_info_row.title_row.user_image.isVisible()
        assert muscle_group == 'Chest', 'Exercise muscle group is not correct'
        assert equipment == 'Dumbell', 'Exercise equipment is not correct'
        assert user_exercise is False, 'Exercise should be system exercise'
    filter_box.bttn_reset.click()
    filter_box.bttn_filter.click()

    # ----- Step 5: Add exercise to bookmarsk and check if it was added -----
    list_exercises.select_index(0)
    list_exer_name = list_exercises.model().rows[0].name
    event_type = QtCore.QEvent.Type.GraphicsSceneMouseDoubleClick
    list_exercises.mouseDoubleClickEvent(event_type)
    bttn_bookmark_label = tab_exercises.exercise_data_editor.bookmarks_bar.bttns_exercises[-1].label.text()
    assert list_exer_name == bttn_bookmark_label, \
        f'Exercise "{list_exer_name}" wasn\'t added to bookmarks'

    # ----- Step 6: Load exercise to Planner and checj it -----
    bttn_load_to_planner = tab_exercises.exercise_data_editor.toolbar.bttn_load_to_planner
    menu_load_to_planner = bttn_load_to_planner.menu()
    action_monday = find_button_by_text(menu_load_to_planner.children(), 'Monday')
    action_monday.triggered.emit()
    assert window.tab_widget.bar.bttn_planner.isChecked(), f'Tab Planner should be active.'
    monday_work_area = window.tab_widget.tab_planner.right.plan_editor.plan_area.workout_areas[0]
    table_exer_name = monday_work_area.table.model().exer_exec_rows[0].icon_and_name[1]
    assert list_exer_name == table_exer_name, 'Exercise wasn\'t added to table Monday'
    window.tab_widget.bar.bttn_exercises.click()
    filter_box.bttn_reset.click()
    filter_box.bttn_filter.click()

    # ----- Step 7: Edit exercise  -----
    # --- Save original values
    # - Set user exercises for editing -
    set_value(filter_box.rb_box_user_exer, True)
    filter_box.bttn_filter.click()
    exercise_data_viewer = tab_exercises.exercise_data_editor.exercise_data_viewer
    exer_name = basic_info_row.title_row.title
    exer_type = basic_info_row.row.info_grid.label_type_value
    body_part = basic_info_row.row.info_grid.label_body_part_value
    orig_exer_name = get_value(exer_name)
    orig_exer_type = get_value(exer_type)
    orig_body_part = get_value(body_part)
    # Edit exercise data
    toolbar = tab_exercises.exercise_data_editor.toolbar
    toolbar.bttn_edit_exercise.click()
    set_value(exer_name, 'New exer title')
    set_value(exer_type, 'Cardio')
    set_value(body_part, 'Legs')
    QtCore.QTimer.singleShot(100, lambda: handle_info_dialog(exercise_data_viewer))
    toolbar.bttn_save_changes.click()
    # Check if values were saved
    assert 'New exer title' == get_value(exer_name), 'Exercise name wasn\'t edited'
    assert 'Cardio' == get_value(exer_type), 'Exercise type wasn\'t edited'
    assert 'Legs' == get_value(body_part), 'Body part wasn\'t edited'

    # ------Reset values back ---
    toolbar.bttn_edit_exercise.click()
    set_value(exer_name, orig_exer_name)
    set_value(exer_type, orig_exer_type)
    set_value(body_part, orig_body_part)
    QtCore.QTimer.singleShot(100, lambda: handle_info_dialog(exercise_data_viewer))
    toolbar.bttn_save_changes.click()
    # This is to prevent Save plan dialog
    window.tab_widget.tab_planner.right.plan_editor.unsaved_changes = False
