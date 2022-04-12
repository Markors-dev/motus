import os
import sys
import pdb
from pathlib import Path


PROJ_DIR = str(Path(os.getcwd()).parent)
SRC_DIR = str(Path(os.getcwd()).parent.joinpath('src'))
sys.path.append(SRC_DIR)
