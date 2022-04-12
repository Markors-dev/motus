import json
import pdb
from pathlib import Path
from collections import namedtuple

from PyQt5 import QtCore

from config import EXPORTS_DIR, SETTINGS_FILE
from util.obj import SingletonDecorator


# ----- Constatnts -----

ICON_SIZES = [
    (50, 50),
    (60, 60),
    (70, 70),
]

EXER_PER_PAGE = ('15', '30', '50')

# Settings properties with DEFAULT values
DEFAULT_PROPERTIES = {
    'main_display': 'display1',
    'font_family': 'Helvetica',
    'icon_size': ICON_SIZES[0],
    'reload_plan': False,
    'exer_per_page': EXER_PER_PAGE[1],
    'pdf_folderpath': str(Path(EXPORTS_DIR).joinpath('pdf')),
    'motfiles_folderpath': str(Path(EXPORTS_DIR).joinpath('motfiles')),
}


@SingletonDecorator
class Settings:

    def __init__(self, screens=None):
        """ Method is run only once per runtime.

        :param screens_geometries: list(<QtCore.QRect>)
        """
        if not Path(SETTINGS_FILE).exists():
            # Create props on initial app run(or if settings are deleted)
            assert screens, 'Screens are not provided'
            screens_geometries = [scr.geometry() for scr in screens]
            self._create_props(screens_geometries)
        # ----- Data -----
        self.values = self._get_props()

    def setValue(self, key, value):
        # --- Write to settings file ---
        with open(SETTINGS_FILE, 'r') as infile:
            props_json = json.load(infile)
        props_json[key] = value
        self._write_to_json(props_json)
        # --- Write to attribute values ---
        self.values[key] = value

    def getValue(self, prop_key):
        value = self.values[prop_key]
        if type(value) == list:
            value = tuple(value)
        return value

    @staticmethod
    def _get_props():
        with open(SETTINGS_FILE, 'r') as infile:
            props_dict = json.load(infile)
        return props_dict

    def _create_props(self, screens_geometries):
        """This method is used(only once) on initial run

        Sets App settings in OS registry.
        """
        # --- Get properties in json ---
        geometries = {}
        for i, scr_geo in enumerate(screens_geometries):
            geo_tuple = (scr_geo.x(), scr_geo.y(), scr_geo.width(), scr_geo.height())
            geometries[f'display{i + 1}_geometry'] = geo_tuple
        props_dict = DEFAULT_PROPERTIES.copy()
        props_dict.update(geometries)
        # --- Write settings to json file ---
        self._write_to_json(props_dict)

    @staticmethod
    def _write_to_json(props_dict):
        props_json_str = json.dumps(props_dict, indent=4)
        with open(SETTINGS_FILE, 'w') as outfile:
            outfile.write(props_json_str)

    def get_available_displays(self):
        displays = []
        for screen_key in [sc_key for sc_key in self.values.keys() if
                           '_geometry' in sc_key]:
            geometry_tuple = self.values[screen_key]
            resolution = f'({geometry_tuple[2]} x {geometry_tuple[3]})'
            item = f'{screen_key.split("_")[0]}{resolution}'
            displays.append(item)
        return displays
