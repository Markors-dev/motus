from gui.colors import Colors

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

# NOTE: read "ps"(e.g. "ps_title") as "Paragraph style"

ps_day_title = ParagraphStyle(
    'ps_title',
    fontName="Helvetica",  # old: Helvetica-Bold
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
    fontName="Helvetica",  # old: Helvetica-Bold
    fontSize=25,
    leading=40,  # old = 60
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
    fontName="Helvetica",
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
    fontName="Helvetica",
    fontSize=12,
    leading=14,  # old= 50
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
    fontName="Helvetica-Bold",  # old: Source Sans Pro
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
    fontName="Helvetica",
    fontSize=12,
    leading=14,  # old= 14
    alignment=1,
    # wordWrap=1,
    # borderWidth=0,
    # borderPadding=0,
)
ps_text_exercise = ParagraphStyle(
    'ps_text_exercise',
    fontName="Helvetica",
    fontSize=12,
    leading=14,  # old= 14
    alignment=0,
    # wordWrap=1,
    # borderWidth=0,
    # borderPadding=0,
)
ps_superset_top = ParagraphStyle(
    'ps_superset_top',
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=10,  # old= 10
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
    leading=12,  # old= 20
    alignment=2,
    borderPadding=20,
)
ps_link = ParagraphStyle(
    'ps_link',
    fontName="Helvetica",
    fontSize=13,
    leading=16,  # old= 20
    alignment=0,
    spaceAfter=1,
    borderWidth=0,
    borderPadding=0,
    leftIndent=5,
    textColor=colors.blue,
)
