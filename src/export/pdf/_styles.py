from pathlib import Path

from gui.colors import Colors

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import DATA_DIR


# Registering new font
FONT_VERDANA_FP = Path(DATA_DIR).joinpath('fonts', 'verdana.ttf')
pdfmetrics.registerFont(TTFont('Verdana', FONT_VERDANA_FP))


ps_day_title = ParagraphStyle(
    'ps_title',
    fontName="Helvetica",
    fontSize=24,
    leading=30,
    alignment=1,
    borderWidth=1,
    borderRadius=5,
    wordWrap=1,
    borderColor=colors.Color(*Colors.DAY_TITLE.dec),
    textColor=colors.white,
    backColor=colors.Color(*Colors.DAY_TITLE.dec),
)
ps_day_summary = ParagraphStyle(
    'ps_title',
    fontName="Helvetica",
    fontSize=25,
    leading=40,
    alignment=1,
    borderWidth=1,
    borderRadius=10,
    borderPadding=5,
    borderColor=colors.Color(*Colors.DAY_TITLE.dec),
    textColor=colors.white,
    backColor=colors.Color(*Colors.DAY_TITLE.dec),
)
ps_workout_title = ParagraphStyle(
    'ps_workout',
    fontName="Verdana",
    fontSize=24,
    leading=30,
    alignment=1,
    borderWidth=1,
    borderRadius=5,
    wordWrap=1,
    borderColor=colors.Color(*Colors.WORKOUT_TITLE.dec),
    textColor=colors.white,
    backColor=colors.Color(*Colors.WORKOUT_TITLE.dec),
)
ps_workout_cell = ParagraphStyle(
    'ps_workout2',
    fontName="Verdana",
    fontSize=12,
    leading=14,
    alignment=1,
    leftIndent=20,
    rightIndent=20,
    wordWrap=1,
    borderWidth=1,
    borderRadius=5,
    borderPadding=5,
    textColor=colors.white,
    borderColor=colors.Color(*Colors.WORKOUT_TITLE.dec),
    backColor=colors.Color(*Colors.WORKOUT_TITLE.dec),
)
ps_header = ParagraphStyle(
    'ps_header',
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=18,
    alignment=1,
    borderWidth=1,
    borderRadius=3,
    borderPadding=0,
    borderColor=colors.Color(*Colors.TABLE_HEADER.dec),
    backColor=colors.Color(*Colors.TABLE_HEADER.dec)
)
ps_text = ParagraphStyle(
    'ps_text',
    fontName="Verdana",
    fontSize=12,
    leading=14,
    alignment=1,
)
ps_text_exercise = ParagraphStyle(
    'ps_text_exercise',
    fontName="Verdana",
    fontSize=12,
    leading=14,
    alignment=0,
)
ps_superset_top = ParagraphStyle(
    'ps_superset_top',
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=10,
    alignment=1,
    backColor=colors.Color(*Colors.SUPERSET_TOP.dec),
    borderWidth=0,
    borderPadding=0,
)
ps_superset_bottom = ParagraphStyle(
    'ps_superset_bottom',
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=10,
    alignment=1,
    backColor=colors.Color(*Colors.SUPERSET_BOTTOM.dec),
    borderWidth=0,
    borderPadding=0,
)
ps_superset_bottom_empty = ParagraphStyle(
    'ps_superset_bottom_empty',
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=10,
    alignment=1,
    textColor=colors.Color(*Colors.SUPERSET_BOTTOM.dec),
    backColor=colors.Color(*Colors.SUPERSET_BOTTOM.dec),
    borderWidth=0,
    borderPadding=0,
)
ps_text_summary = ParagraphStyle(
    'ps_text_summary',
    fontName="Helvetica",
    fontSize=10,
    leading=12,
    alignment=2,
    borderPadding=20,
)
ps_link = ParagraphStyle(
    'ps_link',
    fontName="Verdana",
    fontSize=13,
    leading=16,
    alignment=0,
    spaceAfter=1,
    borderWidth=0,
    borderPadding=0,
    leftIndent=5,
    textColor=colors.blue,
)
