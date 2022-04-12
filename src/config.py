import sys
from pathlib import Path
from enum import Enum

from PyQt5 import QtCore
from PyQt5 import QtWidgets


class AppMode(Enum):
    DEVELOPMENT_MODE = 0
    PRODUCTION_MODE = 1


# --- App constants --- #
#########################
APP_MODE = AppMode.PRODUCTION_MODE
APP_NAME = 'Motus'
COMPANY_NAME = 'MyCompany'
PLAN_FILE_EXTENSION = 'motplan'
WORKOUT_FILE_EXTENSION = 'motwork'

# Folder paths
SRC_DIR = str(Path(__file__).parent)
PROJ_DIR = str(Path(SRC_DIR).parent)
EXPORTS_DIR = str(Path(PROJ_DIR).joinpath('exports'))
DATA_DIR = str(Path(SRC_DIR).joinpath('data'))
IMAGES_DIR = str(Path(DATA_DIR).joinpath('images'))
# File paths
SESSION_JSON_FILE = str(Path(DATA_DIR).joinpath('sessions.json'))
DB_PATH = str(Path(DATA_DIR, 'motus.db'))
LOG_FILE = str(Path(DATA_DIR, 'motus_run.log'))
BOOKMARKS_FILE = str(Path(DATA_DIR, 'bookmarks.txt'))
SETTINGS_FILE = str(Path(DATA_DIR, 'settings.json'))
# Table data
DAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
DAYS_TITLE = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
