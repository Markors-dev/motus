import logging
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from session import Session
from config import APP_MODE, AppMode
from settings import Settings
from log import run_logging_setup
from gui.main_window import MainWindow
from gui.flags import ExitCode, ImageFp
from gui.util import get_center_pos
from util.hooks import my_exception_hook


class App(QtWidgets.QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        Settings(self.screens())
        self.window = MainWindow()
        self.window.hide()
        if APP_MODE == AppMode.PRODUCTION_MODE:
            sys.excepthook = my_exception_hook
        run_logging_setup()

    def run(self):
        # ----- Preload GUI actions -----
        Session.start_session()
        pixmap = QtGui.QPixmap(ImageFp.MOTUS_LOGO)
        splash = QtWidgets.QSplashScreen(pixmap)
        splash_pos = get_center_pos(splash)
        splash.setGeometry(splash_pos.x(), splash_pos.y(),
                           splash.width(), splash.height())
        splash.show()
        self.processEvents()
        # ----- Load GUI -----
        self.window.init_ui()
        splash.finish(self.window)
        self.window.show()
        # ----- APP RUN ---
        _exit_code = self.exec()
        Session.end_session()
        return _exit_code


if __name__ == "__main__":
    exit_code = ExitCode.RESTART
    while exit_code == ExitCode.RESTART:
        app = App()
        exit_code = app.run()
        del app
    sys.exit(exit_code)
