from enum import Enum


class ThemeType(Enum):
    LIGHT = 0
    GREEN = 1
    DARK = 2


class Theme:
    def __init__(self, bg_theme):
        if bg_theme == ThemeType.LIGHT:
            self.bg_color = '#FFFFFF'
            self.text_color = '#000000'
        elif bg_theme == ThemeType.GREEN:
            self.bg_color = Colors.INFO_LIGHT_ROW.hex
            self.text_color = '#000000'
        elif bg_theme == ThemeType.DARK:
            self.bg_color = Colors.INFO_DARK_ROW.hex
            self.text_color = '#FFFFFF'


class Color:
    def __init__(self, hex_, desc=None):
        self.hex = hex_
        self.rgb = self._hex_to_rgb()
        self.dec = self._hex_to_decimal()
        self.desc = desc if desc else 'NOT_SET'

    def _hex_to_rgb(self):
        hex_stripped = self.hex.lstrip('#')
        assert len(hex_stripped) == 6, 'Color hex value must have length 6.'
        return tuple(int(hex_stripped[i:i + 2], 16) for i in (0, 2, 4))

    def _hex_to_decimal(self):
        return tuple([round((1 / 255 * channel), 4) for channel in self.rgb])

    def __repr__(self):
        return f'Color(desc="{self.desc}", hex={self.hex}, rgb={self.rgb}, dec={self.dec})'


class Colors:
    # ----- Panes -----
    MAIN_WINDOW = Color('#E0E0E0', 'light_grey')
    CONTAINER = Color('#D3D3D3', 'LightGrey')
    SELECTED_CONTAINER = Color('#90EE90', 'LightGreen')
    # ----- Buttons -----
    BTTN = Color('#99CCFF')
    BTTN_HOVER = Color('#B2FF66')
    BTTN_DISABLED = Color('#EBEBE4')
    BTTN_PRESSED = Color('#3399FF')
    # ----- Table -----
    DAY_TITLE = Color('#3399FF', 'blue')
    TABLE_HEADER = Color('#CCFFCC', 'green')
    ROW = Color('#FFFF99')
    ROW_ALT = Color('#E6FFE6')
    SUPERSET_TOP = Color('#FFEFD5', 'light blue')
    SUPERSET_BOTTOM = Color('#FFDAB9', 'light blue')
    # ----- Titles -----
    TITLE = Color('#009999', 'greenish')
    PLAN_TITLE = Color('#4169E1', 'Dark Cyan')
    WORKOUT_TITLE = Color('#008080', 'Teal')
    EXERCISE_TITLE = Color('#8FBC8F', 'LightSkyBlue')
    PLAN_TYPE = Color('#F0FFF0', 'FloralWhite')
    IMAGE_CAPTION = Color('#4682B4', 'SteelBlue')
    # ----- Info rows -----
    INFO_DARK_ROW = Color('#336699', 'dark_blue')
    INFO_LIGHT_ROW = Color('#CCFFCC', 'light_green')
    # ----- Validation -----
    INVALID_INPUT = Color('#FF9999', 'light-red')
