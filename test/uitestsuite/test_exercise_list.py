from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import pytest
import pytestqt

from gui.util import get_value, set_value, find_button_by_text
from test.uitest.manip import window
from test.uitest.handle_dialog import handle_info_dialog


def test_exercise_list(window, qtbot):
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
    # Step check:  all filtered exercises must have set filters
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

    # ----- Step 2: Reset exercises
    filter_box.bttn_reset.click()
    filter_box.bttn_filter.click()
    # Step check: number of exercise pages must be at least 25
    page_selector = tab_exercises.exercise_list_viewer.exercises_box.page_selector
    assert page_selector.numb_of_pages >= 25, 'Number of pages must be at least 25'

    # ----- Step 3: set new filters and get exercises -----
    # import pdb; pdb.set_trace()
    set_value(filter_box.cb_muscle_group, 'Chest')
    set_value(filter_box.cb_equipment, 'Dumbell')
    set_value(filter_box.rb_box_user_exer, False)
    filter_box.bttn_filter.click()
    # Step check: all filtered exercises must have set filters
    for row in range(5):
        list_exercises.select_index(row)
        muscle_group = get_value(basic_info_row.row.info_grid.label_main_muscles_value)
        equipment = get_value(basic_info_row.row.info_grid.label_equipment_value)
        user_exercise = basic_info_row.title_row.user_image.isVisible()
        assert muscle_group == 'Chest', 'Exercise muscle group is not correct'
        assert equipment == 'Dumbell', 'Exercise equipment is not correct'
        assert user_exercise is False, 'Exercise should be system exercise'

    # ----- Step 4: Reset exercises
    filter_box.bttn_reset.click()
    filter_box.bttn_filter.click()
    # Step check: number of exercise pages must be at least 25
    page_selector = tab_exercises.exercise_list_viewer.exercises_box.page_selector
    assert page_selector.numb_of_pages >= 25, 'Number of pages must be at least 25'
