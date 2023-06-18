import json
import os
import re
from pprint import pprint as pp  # noqa
import uuid


from anki.hooks import addHook
from aqt.qt import *
from aqt.utils import tooltip, restoreGeom, saveGeom

from .anki_version_detection import anki_point_version
from .config import gc, wcm
if qtmajor == 5:
    from .forms5 import addtable  # type: ignore  # noqa
else:
    from .forms6 import addtable  # type: ignore  # noqa


addon_path = os.path.dirname(__file__)

import markdown
from markdown.extensions.abbr import AbbrExtension
from markdown.extensions.codehilite import CodeHiliteExtension  # noqa
from markdown.extensions.def_list import DefListExtension  # noqa
from markdown.extensions.fenced_code import FencedCodeExtension  # noqa
from markdown.extensions.footnotes import FootnoteExtension  # noqa
from markdown.extensions.tables import TableExtension



def get_alignment(s):
    """
    Return the alignment of a table based on input `s`. If `s` not in the
    list, return the default value.
    >>> get_alignment(":-")
    u'left'
    >>> get_alignment(":-:")
    u'center'
    >>> get_alignment("-:")
    u'right'
    >>> get_alignment("random text")
    u'left'
    """
    alignments = {":-": "left", ":-:": "center", "-:": "right"}
    default = "left"
    s = re.sub("\\-{2,}","-",s) #Prune extra dashes.
    if s not in alignments:
        return default
    return alignments[s]


place_holder_table = {
    # "strings in source" : TableExtension["strings in result", "temporary placeholder"]
    "\|": ["&#124;", str(uuid.uuid4())],
}


def escape_html_chars(s):
    """
    Escape HTML characters in a string. Return a safe string.
    >>> escape_html_chars("this&that")
    u'this&amp;that'
    >>> escape_html_chars("#lorem")
    u'#lorem'
    """
    if not s:
        return ""
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
    }
    result = "".join(html_escape_table.get(c, c) for c in s)
    for i in place_holder_table.values():
        result = result.replace(i[1], i[0])
    return result


def insert_html_into_editor_at_cursor(editor, html):
    if anki_point_version <= 49:
        js = "document.execCommand('insertHTML', false, %s);" % json.dumps(html)                
    else:
        js = """
setTimeout(function() {
document.execCommand('insertHTML', false, %s);
}, 40); """ % json.dumps(html)
    editor.web.eval(js)        


stylesheet = """
QCheckBox { padding-top: 7%; }
QLabel    { padding-top: 7%; }
"""  # height: 10px; margin: 0px; }"


class TableBase:
    def insert_table(self, tstyle, head_row, body_rows):
        if head_row:
            html = """
            <table {0}>
                <thead><tr>{1}</tr></thead>
                <tbody>{2}</tbody>
            </table>""".format(tstyle, head_row, body_rows)
        else:
            html = """
            <table {0}>
                <tbody>{1}</tbody>
            </table>""".format(tstyle, body_rows)
        insert_html_into_editor_at_cursor(self.editor, html)


class TableDialog(QDialog):
    def __init__(self, parent):
        self.parent = parent
        QDialog.__init__(self, parent, Qt.WindowType.Window)
        self.dialog = addtable.Ui_Dialog()
        self.dialog.setupUi(self)
        self.setWindowTitle("Add Table ")
        self.setStyleSheet(stylesheet)
        self.fill()
        restoreGeom(self, "addon_add_table_dialog")

    def fill(self):
        d = self.dialog
        d.sb_columns.setMinimum(1)
        d.sb_columns.setMaximum(gc("Table_max_cols", 20))
        d.sb_columns.setValue(gc("SpinBox_column_default_value", 2))
        d.sb_rows.setMinimum(1)
        d.sb_rows.setMaximum(gc("Table_max_rows", 100))
        d.sb_rows.setValue(gc("SpinBox_row_default_value", 5))
        d.cb_width.setChecked(True if gc("table_style__column_width_fixed_default", False) else False)
        d.cb_first.setChecked(True if gc("table_style__first_row_is_head_default", False) else False)
        d.cb_prefill.setChecked(True if gc("table_pre-populate_head_fields", False) else False)
        d.cb_center.setChecked(True if gc("table_center_by_default", False) else False)

        smembers = [gc('table_style__default'), ]
        for s in gc('table_style_css_V4').keys():
            if s != gc('table_style__default'):
                smembers.append(s)
        d.sb_styling.addItems(smembers)

        hoptions = ["do not override global settings", 'left', 'right', 'center']
        d.sb_align_H.addItems(hoptions)
        if gc("table_style__h_align_default") in hoptions:
            index = hoptions.index(gc("table_style__h_align_default"))
            d.sb_align_H.setCurrentIndex(index)

        voptions = ["do not override global settings", "top", "middle", "bottom", "baseline"]
        d.sb_align_V.addItems(voptions)
        if gc("table_style__v_align_default") in voptions:
            index = voptions.index(gc("table_style__v_align_default"))
            d.sb_align_V.setCurrentIndex(index)

        d.cb_save.setChecked(True if gc("last_used_overrides_default") else False)

    def update_config(self):
        if self.save_as_default:
            newvalues = [
                 ["SpinBox_column_default_value", self.num_columns],
                 ["SpinBox_row_default_value", self.num_rows],
                 ["table_style__column_width_fixed_default", self.fixedwidth],
                 ["table_style__first_row_is_head_default", self.usehead],
                 ["table_pre-populate_head_fields", self.prefill],
                 ["table_pre-populate_body_fields", self.prefill],
                 ["table_center_by_default", self.center],
                 ["table_style__default", self.styling],
                 ["table_style__h_align_default", self.table_h_align],
                 ["table_style__v_align_default", self.table_v_align],
                 ['last_used_overrides_default', self.save_as_default],
                 ]
            wcm(newvalues)

    def accept(self):
        d = self.dialog
        self.num_columns = d.sb_columns.value()
        self.num_rows = d.sb_rows.value()
        self.fixedwidth = True if d.cb_width.isChecked() else False
        self.usehead = True if d.cb_first.isChecked() else False
        self.prefill = True if d.cb_prefill.isChecked() else False
        self.center = True if d.cb_center.isChecked() else False
        self.styling = d.sb_styling.currentText()
        self.table_h_align = d.sb_align_H.currentText()
        if self.table_h_align == "do not override global settings":
            self.table_h_align = ""
        self.table_v_align = d.sb_align_V.currentText()
        if self.table_v_align == "do not override global settings":
            self.table_v_align = ""
        self.save_as_default = d.cb_save.isChecked()
        self.update_config()
        saveGeom(self, "addon_add_table_dialog")
        QDialog.accept(self)


class TableFromDialog(TableBase):
    def __init__(self, editor, parent_window):
        self.editor = editor
        self.parent_window = parent_window
        self.show_dialog()

    def show_dialog(self):
        d = TableDialog(self.parent_window)
        if d.exec():
            if d.usehead:
                num_rows = d.num_rows - 1
            else:
                num_rows = d.num_rows
            Tstyle = gc('table_style_css_V4')[d.styling]['TABLE_STYLING']
            Hstyle = gc('table_style_css_V4')[d.styling]['HEAD_STYLING']
            Bstyle = gc('table_style_css_V4')[d.styling]['BODY_STYLING']

            if d.center:
                if "style='" in Tstyle:
                    Tstyle = Tstyle.replace("style='", "style='margin-left:auto; margin-right:auto; ")
                elif "style=\"" in Tstyle:
                    Tstyle = Tstyle.replace("style=\"", "style=\"margin-left:auto; margin-right:auto; ")
                else:
                    Tstyle += " style='margin-left:auto; margin-right:auto;' "

            style = ""
            if d.fixedwidth:
                style += "width:{0:.0f}%; ".format(100/d.num_columns)
            if d.table_h_align:
                style += ' text-align:%s; ' % d.table_h_align
            if d.table_v_align:
                style += ' vertical-align:%s; ' % d.table_v_align

            head_row = ""
            if d.usehead:
                if d.prefill:
                    head_html = "<th {0}>head{1}</th>"
                else:
                    head_html = "<th {0}>&#x200b;</th>"
                for i in range(d.num_columns):
                    head_row += head_html.format(Hstyle.format(style), str(i+1))

            if d.prefill:
                body_html = "<td {0}>data{1}</td>"
            else:
                body_html = "<td {0}>&#x200b;</td>"
            body_column = ""
            for i in range(d.num_columns):
                body_column += body_html.format(Bstyle.format(style), str(i+1))
            body_rows = "<tr>{}</tr>".format(body_column) * num_rows
            self.insert_table(Tstyle, head_row, body_rows)


class TableFromMarkdownLike(TableBase):
    def __init__(self, editor, parent_window, selected_text):
        self.editor = editor
        self.parent_window = parent_window
        self.selected_text = selected_text
        self.create_table_from_selection()

    def create_table_from_selection(self):
        # - split on newlines
        # - strip to remove leading/trailing spaces: Otherwise the detection of
        #   markdown tables might not work and a space might generate a new column
        # - To include a pipe as content escape the backslash (as in GFM spec)
        stx = self.selected_text

        if False:  # gc("md: format selection with markdown package"):
            # noqa
            # seems to be working
            # html = markdown.markdown(stx, extensions=[
            #     AbbrExtension(),
            #     # CodeHiliteExtension(
            #     #     noclasses = True, 
            #     #     linenums = config.shouldShowCodeLineNums(), 
            #     #     pygments_style = config.getCodeColorScheme()
            #     # ),
            #     DefListExtension(),
            #     FencedCodeExtension(),
            #     FootnoteExtension(),
            #     TableExtension(),
            #     ], output_format="html5")

            # seems to be working
            html = markdown.markdown(stx, extensions=[
                    AbbrExtension(),
                    TableExtension(),
                ], output_format="html")

            # not working: table extension not found
            # html = markdown.markdown(stx, extensions=["tables"], output_format="html5")

            # print(html)
            self.editor.web.eval(
                    "document.execCommand('insertHTML', false, %s);"
                    % json.dumps(html))
            return


        for k, v in place_holder_table.items():
            stx = stx.replace(k, v[1])
        first = [x.strip() for x in stx.split("\n") if x]

        # split on pipes
        second = list()
        for elem in first[:]:
            if elem.startswith('|') and elem.endswith('|'):
                elem = elem[1:-1]
            new_elem = [x.strip() for x in elem.split("|")]
            new_elem = [escape_html_chars(word) for word in new_elem]
            second.append(new_elem)

        if len(second) < 2:
            tooltip("Add-on 'Add Table': Something went wrong. Aborting ...")
            return

        # keep track of the max number of cols
        # so as to make all rows of equal length
        max_num_cols = len(max(second, key=len))

        # decide how much horizontal space each column may take
        width = 100 / max_num_cols

        # check for "-|-|-" alignment row
        def alignment_row(cell_list):
            l = [re.sub(r"-+", '-', x) for x in cell_list]
            return all(x.strip(":") in ("-", "") for x in l)

        one = alignment_row(second[0])
        two = alignment_row(second[1])
        
        if all([one, two]):
            tooltip("Error. The top two rows seem to be alignment rows.")
            return

        align_line = []
        alignments = []

        if one:
            use_header = False
            align_line = second[0]
            start = 1
        elif two:
            use_header = second[0]
            align_line = second[1]
            start = 2
        else:
            use_header = second[0] if gc("md: format selection text, default to head") else False
            alignments = ["left"] * max_num_cols
            start = 1 if gc("md: format selection text, default to head") else 0

        if one or two:
            len_align_line = len(align_line)  # noqa
            if len_align_line < max_num_cols:
                align_line += ["-"] * (max_num_cols - len_align_line)
            for elem in align_line:
                alignments.append(get_alignment(elem))

        # create a table
        styling = gc("table_style__default")
        Tstyle = gc('table_style_css_V4')[styling]['TABLE_STYLING']
        Hstyle = gc('table_style_css_V4')[styling]['HEAD_STYLING']
        Bstyle = gc('table_style_css_V4')[styling]['BODY_STYLING']

        head_row = ""
        if use_header:
            head_html = "<th {0}>{1}</th>"
            for elem, alignment in zip(use_header, alignments):
                style = "width:{0:.0f}%; text-align:{1};".format(width, alignment)
                head_row += head_html.format(Hstyle.format(style), elem)
            extra_cols = ""
            if len(use_header) < max_num_cols:
                diff = len(use_header) - max_num_cols
                assert diff < 0, \
                    "Difference between len(use_header) and max_num_cols is positive"
                for alignment in alignments[diff:]:
                    style = "width:{0:.0f}%; text-align:{1};".format(width, alignment)
                    extra_cols += head_html.format(Hstyle.format(style), "")
            head_row += extra_cols

        body_rows = ""
        for row in second[start:]:
            body_rows += "<tr>"
            body_html = "<td {0}>{1}</td>"
            for elem, alignment in zip(row, alignments):
                style = "width:{0:.0f}%; text-align:{1};".format(width, alignment)
                body_rows += body_html.format(Bstyle.format(style), elem)
            # if particular row is not up to par with number of cols
            extra_cols = ""
            if len(row) < max_num_cols:
                diff = len(row) - max_num_cols
                assert diff < 0, \
                    "Difference between len(row) and max_num_cols is positive"
                # use the correct alignment for the last few rows
                for alignment in alignments[diff:]:
                    style = "width:{0:.0f}%; text-align:{1};".format(width, alignment)
                    extra_cols += body_html.format(Bstyle.format(style), "")
            body_rows += extra_cols + "</tr>"

        self.insert_table(Tstyle, head_row, body_rows)


def toggle_table(editor):
    selection = editor.web.selectedText()
    if not selection:
        TableFromDialog(editor, editor.parentWindow)
    else:
        if not selection.count("\n"):  # there is a single line of text
            tooltip("Select more than one line to create a table. Aborting ...")
        elif all(c in ("|", "\n") for c in selection):  # there is no content in table
            tooltip("No content for table. Aborting ...")
        else:
            TableFromMarkdownLike(editor, editor.parentWindow, selection)


def setupEditorButtonsFilter(buttons, editor):
    key = QKeySequence(gc('Key_insert_table'))
    keyStr = key.toString(QKeySequence.SequenceFormat.NativeText)
    if gc('Key_insert_table'):
        b = editor.addButton(
            os.path.join(addon_path, "icons", "table.png"),
            "tablebutton",
            toggle_table,
            tip="Insert table ({})".format(keyStr),
            keys=gc('Key_insert_table')
            )
        buttons.append(b)
    return buttons
addHook("setupEditorButtons", setupEditorButtonsFilter)
