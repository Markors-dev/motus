import datetime
import pdb
from tkinter import Tk
from os import remove
from pathlib import Path

import pytest
import pytestqt

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui

from gui.main_window import MainWindow
from session import Session
from settings import Settings
import config

from conftest import BOOKMARKS_FILE, SETTINGS_FILE, EXPORTS_DIR


def files_cleanup():
    # Remove bookmarks and settings file
    for config_fp in (BOOKMARKS_FILE, SETTINGS_FILE):
        if Path(config_fp).exists():
            remove(config_fp)
    # Remove all exported files - PDFs and motfiles
    for export_dir in Path(EXPORTS_DIR).iterdir():
        for export_fp in Path(export_dir).iterdir():
            remove(export_fp)


@pytest.fixture
def window(qtbot):
    _root = Tk()
    screens_geometries = [QtCore.QRect(0, 0, _root.winfo_screenwidth(),
                                       _root.winfo_screenheight()), ]
    # pdb.set_trace()
    Settings(screens_geometries)
    Session.start_session()
    window = MainWindow()
    window.init_ui()
    qtbot.addWidget(window)
    window.show()
    yield window
    Session.end_session()
    files_cleanup()
    # app_manip.end()
    # pdb.set_trace()
    # QtCore.QCoreApplication.exit()
