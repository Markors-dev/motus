import sys
from pathlib import Path


PROJ_DIR = str(Path(__file__).parent.parent)
SRC_DIR = str(Path(PROJ_DIR).joinpath('src'))
TEST_DIR = str(Path(PROJ_DIR).joinpath('test'))

sys.path.append(SRC_DIR)
sys.path.append(TEST_DIR)
