import io
import logging
from pathlib import Path
from enum import Enum

from reportlab.platypus import SimpleDocTemplate, Image, Spacer, PageBreak
from reportlab.platypus.tables import Table, TableStyle
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors

from config import DAYS_TITLE, DAYS
from settings import Settings
from database.data_model import SupersetRow, SupersetTopRow, SupersetBottomRow
from gui.dialogs import ErrorMessage, QuestionDialog
from gui.colors import Colors
from gui.flags import ImageFp
from util.exception import log_and_show_method_exception, ExceptionWithMsg
from ._styles import (
    ps_day_title, ps_header, ps_text, ps_text_exercise, ps_superset_top,
    ps_superset_bottom, ps_superset_bottom_empty, ps_text_summary, ps_link,
    ps_workout_cell, ps_day_summary, ps_workout_title
)

# Global constants
styles = getSampleStyleSheet()

MARGIN = inch
PAGE_WIDTH, PAGE_HEIGHT = A4
CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN)
CONTENT_HEIGHT = PAGE_HEIGHT - (2 * MARGIN)

IMAGE_REST_DAY = Image(ImageFp.REST_DAY)


class ViewType(Enum):
    WORKOUT_VIEW = 0
    DAYS_VIEW = 1


def create_workout_table(view_type, workout_name, workout_rows):
    """Create and returns a <reportlab.platypus.tables.Table> object

    @:param title <title> Table title
    @:param workout <WorkoutPdfData> Workout data
    @:param rest_day <bool> Add rest days table or not
    """
    # ----- Title row -----
    _ps_style = ps_workout_title if view_type == ViewType.WORKOUT_VIEW else \
        ps_day_title
    title_row = [Paragraph(f'<i>{workout_name}</i>', style=_ps_style), '', '', '', '', '']
    # ----- Header row -----
    header_row = [
        Paragraph('#', style=ps_header),
        Paragraph('Exercise', style=ps_header),
        Paragraph('', style=ps_header),
        Paragraph('Sets', style=ps_header),
        Paragraph('Reps/Time', style=ps_header),
        Paragraph('Pause', style=ps_header),
    ]
    # ----- Exercise rows -----
    table_rows = []
    exer_row_indexes = [1, ]
    ss_top_row_indexes = []
    ss_bottom_row_indexes = []
    if not workout_rows:
        table_rows.append(['', IMAGE_REST_DAY, Paragraph('REST DAY', style=ps_text), '', '', ''])
    else:
        exer_row = 0
        for i, table_row in enumerate(workout_rows):
            if type(table_row) == SupersetTopRow:
                p_ss_top = Paragraph(table_row.text, style=ps_superset_top)
                table_rows.append([p_ss_top, '', '', '', '', ''])
                ss_top_row_indexes.append(i + 2)
            elif type(table_row) == SupersetBottomRow:
                p_ss_bottom_sets = Paragraph(str(table_row.sets), style=ps_superset_bottom)
                p_ss_bottom_pause = Paragraph(str(table_row.pause) + ' min', style=ps_superset_bottom)
                p_ss_bottom_empty = Paragraph('NO', style=ps_superset_bottom_empty)
                table_rows.append([p_ss_bottom_empty, p_ss_bottom_empty, p_ss_bottom_empty,
                                   p_ss_bottom_sets, p_ss_bottom_empty, p_ss_bottom_pause])
                ss_bottom_row_indexes.append(i + 2)
            else:
                p_i = Paragraph(str((exer_row + 1)), style=ps_text)
                icon_image = Image(io.BytesIO(table_row.icon_bytes))
                _exer_name = table_row.icon_and_name[1]
                p_name = Paragraph(_exer_name, style=ps_text_exercise)
                p_sets = Paragraph(str(table_row.sets), style=ps_text)
                reps = str(table_row.reps) if table_row.on_reps else str(table_row.reps) + ' min'
                p_reps = Paragraph(reps, style=ps_text)
                p_pause = Paragraph(str(table_row.pause), style=ps_text)
                table_rows.append([p_i, icon_image, p_name, p_sets, p_reps, p_pause])
                exer_row_indexes.append(i + 2)
                exer_row += 1

    data = [title_row, header_row, *table_rows]

    # ----- Set table style ----
    _numb_col_width = 30.0
    _icon_col_width = 50.0
    _sets_reps_pause_col_widths = (50.0, 80.0, 50.0)
    _exer_name_col_width = CONTENT_WIDTH - _numb_col_width - _icon_col_width - sum(_sets_reps_pause_col_widths)
    col_widths = [_numb_col_width, _icon_col_width, _exer_name_col_width, *_sets_reps_pause_col_widths]
    styles_span_ss_top = [('SPAN', (0, row), (-1, row)) for row in ss_top_row_indexes]
    styles_ss_top_bg = [('BACKGROUND', (0, row), (-1, row), colors.Color(*Colors.SUPERSET_TOP.dec, 1)) for
                        row in ss_top_row_indexes]
    styles_ss_bottom_bg = [('BACKGROUND', (0, row), (-1, row), colors.Color(*Colors.SUPERSET_BOTTOM.dec, 1)) for
                           row in ss_bottom_row_indexes]
    styles_exer_name = [('ALIGN', (2, row), (2, row), 'LEFT') for row in exer_row_indexes]
    style = [
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 5),
        ('LEFTPADDING', (0, 0), (-1, 1), 0),
        ('RIGHTPADDING', (0, 0), (-1, 1), 0),
        ('LEFTPADDING', (2, 2), (2, -1), 20),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, 0), (-1, 0)),
        ('SPAN', (1, 1), (2, 1)),
    ] + styles_span_ss_top + styles_ss_top_bg + styles_ss_bottom_bg + styles_exer_name
    table = Table(data, colWidths=col_widths)  # repeatRows=(0, 1)
    table.setStyle(TableStyle(style))
    return table


def create_table_week_workouts(workouts):
    # ----- Create table rows -----
    table_rows = []
    for i, day_title in enumerate(DAYS_TITLE):
        table_row = []
        day_text = f'<div vertical-align="middle">{day_title}</div>'
        table_row.append(Paragraph(day_text, style=ps_day_summary))
        workout = workouts[i]
        if workout:
            workout_text = workout.name
            table_row.append(Paragraph(workout_text, style=ps_workout_cell))
            workout_type_image = Image(io.BytesIO(workout.type_icon_bytes))
            table_row.append(workout_type_image)
        else:
            table_row.append('')
            table_row.append('')
        table_rows.append(table_row)
    # ----- Set table style -----
    col1_width = 150
    col2_width = 250
    col3_width = CONTENT_WIDTH - col1_width - col2_width
    col_widths = [col1_width, col2_width, col3_width]
    style = [
        ('TOPPADDING', (0, 0), (-1, -1), 18),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
        ('LEFTPADDING', (1, 0), (1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    # ----- Create table and return -----
    table = Table(table_rows, colWidths=col_widths)  # repeatRows=(0, 1)
    table.setStyle(TableStyle(style))
    return table


class _PdfDocument:
    def __init__(self, pdf_fp):
        """PDF abstract type object for exporting plan or workout in pdf

        :param pdf_fp <str>: PDF filepath
        """
        # ----- Data -----
        self.doc = SimpleDocTemplate(pdf_fp)
        self.doc.pagesize = A4
        self.elements = []

    @log_and_show_method_exception(f'Create PDF failed')
    def export(self):
        kwargs = {'onFirstPage': self.myFirstPage} if self.pdf_settings['title'] else {}
        try:
            self.doc.build(self.elements, onLaterPages=self.myLaterPages, **kwargs)
            return True
        except IOError as ex:
            return ExceptionWithMsg(ex, f'Plan "{self.title}" was not exported.')
        except Exception as ex:
            return ExceptionWithMsg(ex, f'Plan "{self.title}" was not exported.')

    def _add_links(self):
        p_links_title = Paragraph(f'Youtube video tutorials', style=styles['Heading1'])
        self.elements.append(p_links_title)
        for exercise_name, link in self.links.items():
            p_link = Paragraph(f'<bullet>&bull</bullet> <link href="{link}">{exercise_name}</link>',
                               style=ps_link)
            self.elements.append(p_link)

    def _add_workout_time(self, workout_time):
        self.elements.append(Spacer(1, inch * 0.5))
        workout_time_str = f"{workout_time // 60}h:{workout_time % 60}min"
        time_paragraph = Paragraph(f'Workout time:\t{workout_time_str}', style=ps_text_summary)
        self.elements.append(time_paragraph)

    def myFirstPage(self, canvas, doc):
        canvas.saveState()
        # ---- Draw title image -----
        x_middle = PAGE_WIDTH / 2.0
        y_middle = PAGE_HEIGHT / 2.0
        x, y = x_middle - 75, y_middle + 150
        canvas.drawImage(self.title_image_fp, x, y, mask='auto')
        # ---- Draw title text -----
        canvas.setFont('Times-Bold', 30)
        title_lines = self._split_title(self.title)
        i = 0
        for i, line in enumerate(title_lines):
            x, y = x_middle, y_middle - i * cm
            canvas.drawCentredString(x, y, line)
        canvas.setFont('Times-Roman', 18)
        x, y = x_middle, y_middle - 50 - i * cm
        canvas.drawCentredString(x, y, f'- {self.doc_type} -')
        canvas.restoreState()

    @staticmethod
    def myLaterPages(canvas, doc):
        canvas.saveState()
        canvas.line(MARGIN, CONTENT_HEIGHT + MARGIN, CONTENT_WIDTH + MARGIN,
                    CONTENT_HEIGHT + MARGIN)
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(PAGE_WIDTH / 2.0, 0.75 * MARGIN, "Page %d" % doc.page)
        canvas.restoreState()

    @staticmethod
    def _split_title(title):
        lines = []
        line = ''
        for word in title.split(' '):
            if len(line) + len(word) > 25:
                lines.append(line.strip())
                line = word + ' '
            else:
                line += word + ' '
        lines.append(line.strip())
        return lines


class PdfPlanDocument(_PdfDocument):
    def __init__(self, plan_pdf_fp, plan_pdf_data, pdf_settings, title_image_fp):
        """PDF abstract type object for exporting plan in pdf

        :param pdf_fp <str>: PDF filepath
        :param plan_data <PlanPdfData>
        :param links <dict> Format {%Exercise name%: %link%}
        """
        super().__init__(plan_pdf_fp)
        # ----- Data -----
        self.doc_type = 'workout plan'
        self.plan_pdf_data = plan_pdf_data
        self.pdf_settings = pdf_settings
        self.title = plan_pdf_data.name
        self.title_image_fp = title_image_fp
        self.links = self.plan_pdf_data.links
        self._create_elements()

    def _create_elements(self):
        # (if title is needed) Add page break on 1st page
        if self.pdf_settings['title']:
            self.elements.append(PageBreak())
        # (if plan view type is "workout view") Add week workout summary table
        if self.pdf_settings['view_type'] == 'workout_view':
            self.elements.append(Paragraph('Week plan summary', style=styles['Title']))
            table_week_workouts = create_table_week_workouts(self.plan_pdf_data.workouts)
            self.elements.append(table_week_workouts)
            self.elements.append(PageBreak())
        # For every workout create day/workout table
        _plan_view_type = ViewType.WORKOUT_VIEW if self.pdf_settings['view_type'] == 'workout_view' \
            else ViewType.DAYS_VIEW
        workouts_added = []
        for i, workout in enumerate(self.plan_pdf_data.workouts):
            if _plan_view_type == ViewType.DAYS_VIEW:
                if not workout:
                    if not self.pdf_settings['rest_days']:
                        # No workout for that day and no need to write empty days
                        continue
                    _table_rows = None
                else:
                    _table_rows = workout.table_rows
                table = create_workout_table(_plan_view_type, DAYS_TITLE[i], _table_rows)
            else:  # == ViewType.WORKOUT_VIEW
                if not workout or workout.name in workouts_added:
                    continue
                else:
                    table = create_workout_table(_plan_view_type, workout.name, workout.table_rows)
                    workouts_added.append(workout.name)
            self.elements.append(Spacer(1, inch * 0.5))
            self.elements.append(table)
            if hasattr(workout, 'workout_time'):
                self._add_workout_time(workout.workout_time)
            self.elements.append(PageBreak())
        # last page with video tutorial links
        if self.pdf_settings['links']:
            self._add_links()


class PdfWorkoutDocument(_PdfDocument):
    def __init__(self, workout_pdf_fp, workout_pdf_data, pdf_settings, title_image_fp, links):
        """PDF abstract type object for exporting workout in pdf

        :param plan_data <PlanPdfData(namedtuple)>
        :param export_rest_days <bool>
        :param links <dict> Format {%Exercise name%: %link%}
        """
        super().__init__(workout_pdf_fp)
        # ----- Data -----
        self.doc_type = 'workout'
        self.workout_pdf_data = workout_pdf_data
        self.pdf_settings = pdf_settings
        self.title = workout_pdf_data.name
        self.title_image_fp = title_image_fp
        self.links = links
        # ----- Create all elements -----
        self._create_elements()

    def _create_elements(self):
        if self.pdf_settings['title']:
            # Add page break on 1st page which has the title
            self.elements.append(PageBreak())
        table = create_workout_table(
            ViewType.WORKOUT_VIEW, self.workout_pdf_data.name,
            self.workout_pdf_data.table_rows)
        self.elements.append(table)
        self._add_workout_time(self.workout_pdf_data.workout_time)
        self.elements.append(PageBreak())
        if self.pdf_settings['links']:
            self._add_links()


def _get_pdf_fp(motus_obj_name):
    pdf_folderpath = Settings().getValue('pdf_folderpath')
    if not Path(pdf_folderpath).exists():
        _msg = f'Create folder "{pdf_folderpath}" or set other directory(in Settings)\n' \
               f'for PDF exports.'
        ErrorMessage('Exports folder not found', _msg).exec()
        return False
    pdf_filename = motus_obj_name.replace(' ', '_').lower() + '.pdf'
    pdf_fp = str(Path(pdf_folderpath).joinpath(pdf_filename))
    if Path(pdf_fp).exists():
        _msg = f'PDF file "{pdf_filename}" already exists in directory:\n' \
               f'"{pdf_folderpath}"\n\n' \
               f'Do you want to overwrite it ?'
        overwrite = QuestionDialog('Overwrite PDF file', _msg).exec()
        if not overwrite:
            return False
    return pdf_fp


_type_to_image_fp_dict = {
    'bodybuilding': ImageFp.BODYBUILDING,
    'calisthenics': ImageFp.CALISTHENICS,
    'hiit': ImageFp.HIIT,
    'cardio': ImageFp.CARDIO,
    'powerlifting': ImageFp.POWERLIFTING,
    'olympic weightlifting': ImageFp.OLYMPIC_WEIGHTLIFTING,
}


def create_plan_pdf(plan_pdf_data, pdf_settings):
    plan_pdf_fp = _get_pdf_fp(plan_pdf_data.name)
    if not plan_pdf_fp:
        return False
    title_image_fp = _type_to_image_fp_dict[plan_pdf_data.type.lower()]
    pdf_doc = PdfPlanDocument(plan_pdf_fp, plan_pdf_data, pdf_settings, title_image_fp)
    exported = pdf_doc.export()
    return exported


def create_workout_pdf(workout_pdf_data, pdf_settings, links):
    workout_pdf_fp = _get_pdf_fp(workout_pdf_data.name)
    if not workout_pdf_fp:
        return False
    title_image_fp = _type_to_image_fp_dict[workout_pdf_data.type.lower()]
    pdf_doc = PdfWorkoutDocument(workout_pdf_fp, workout_pdf_data, pdf_settings, title_image_fp, links)
    exported = pdf_doc.export()
    return exported
