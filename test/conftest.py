import pdb
from pathlib import Path

import config

TEST_DIR = str(Path(__file__).parent)
CONFIG_DIR = str(Path(TEST_DIR).joinpath('config'))
EXPORTS_DIR = str(Path(TEST_DIR).joinpath('exports'))
TEST_DB_PATH = str(Path(TEST_DIR).joinpath('data', 'test_motus.db'))
BOOKMARKS_FILE = str(Path(CONFIG_DIR).joinpath('bookmarks.txt'))
SETTINGS_FILE = str(Path(CONFIG_DIR).joinpath('settings.json'))
SESSION_JSON_FILE = str(Path(CONFIG_DIR, 'sessions.json'))


# ----- Setting config file and dir paths -----

test_config_consts = {
    'BOOKMARKS_FILE': BOOKMARKS_FILE,
    'SETTINGS_FILE': SETTINGS_FILE,
    'SESSION_JSON_FILE': SESSION_JSON_FILE,
    'APP_MODE': config.AppMode.PRODUCTION_MODE,
    'DB_PATH': TEST_DB_PATH,
    'EXPORTS_DIR': EXPORTS_DIR,
}
for key, value in test_config_consts.items():
    setattr(config, key, value)
