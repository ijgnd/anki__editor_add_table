# this is a small modification of the hyperlink/unlink function
# from the Power Format Pack: Copyright 2014-2017 Stefan van den Akker <neftas@protonmail.com>

# the code from the PFP (mostfly from table.py and utilities.py)
# is mostly the icon and from L54-323.
# the function setupEditorButtonsFilter is taken from "Auto Markdown"
# from https://ankiweb.net/shared/info/1030875226 which should be
# Copyright 2018 anonymous
#      probably reddit user /u/NavyTeal, see https://www.reddit.com/r/Anki/comments/9t7acy/bringing_markdown_to_anki_21/


import json
import os
from anki import version
from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, wrap



from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QShortcut, QVBoxLayout, QHBoxLayout, QDialog, QLabel, QLineEdit
from PyQt5.QtGui import QKeySequence


addon_path = os.path.dirname(__file__)


def load_config(conf):
    global config
    config=conf

load_config(mw.addonManager.getConfig(__name__))
mw.addonManager.setConfigUpdatedAction(__name__,load_config) 


def get_alignment(s):
    """
    Return the alignment of a table based on input `s`. If `s` not in the
    list, return the default value.
    >>> get_alignment(u":-")
    u'left'
    >>> get_alignment(u":-:")
    u'center'
    >>> get_alignment(u"-:")
    u'right'
    >>> get_alignment(u"random text")
    u'left'
    """
    alignments = {":-": "left", ":-:": "center", "-:": "right"}
    default = "left"
    if s not in alignments:
        return default
    return alignments[s]


def escape_html_chars(s):
    """
    Escape HTML characters in a string. Return a safe string.
    >>> escape_html_chars(u"this&that")
    u'this&amp;that'
    >>> escape_html_chars(u"#lorem")
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
    return result


def create_counter(start=0, step=1):
    """
    Generator that creates infinite numbers. `start` indicates the first
    number that will be returned, `step` the number that should be added
    or subtracted from the previous number on subsequent call to the
    generator.
    
    >>> c = create_counter(10, 2)
    >>> c.next()
    10
    >>> c.next()
    12
    """
    num = start
    while True:
        yield num
        num += step


class Table(object):
    """
    Create a table.
    """

    def __init__(self, other, parent_window, selected_text):
        self.editor_instance    = other
        self.parent_window      = parent_window
        self.selected_text      = selected_text

        if config["STYLE_TABLE"]:
            self.TABLE_STYLING = \
                u"style='font-size: 1em; width: 100%; border-collapse: collapse;'"
            self.HEAD_STYLING = \
                u"align=\"{0}\" style=\"width: {1}%; padding: 5px;" \
                + u"border-bottom: 2px solid #00B3FF\""
            self.BODY_STYLING = \
                u"style='text-align: {0}; padding: 5px;" \
                + u"border-bottom: 1px solid #B0B0B0'"
        else:
            self.TABLE_STYLING = self.HEAD_STYLING = self.BODY_STYLING = u""

        self.setup()

    def setup(self):
        """
        Set the number of columns and rows for a new table.
        """

        # if the user has selected text, try to make a table out of it
        if self.selected_text:
            is_table_created = self.create_table_from_selection()
            # if we could not make a table out of the selected text, present
            # user with dialog, otherwise do nothing
            if is_table_created:
                return None

        dialog = QDialog(self.parent_window)
        dialog.setWindowTitle("table")

        form = QFormLayout()
        form.addRow(QLabel("Enter the number of columns and rows"))

        columnSpinBox = QSpinBox(dialog)
        columnSpinBox.setMinimum(1)
        columnSpinBox.setMaximum(config['table_max_cols'])
        columnSpinBox.setValue(2)
        columnLabel = QLabel("Number of columns:")
        form.addRow(columnLabel, columnSpinBox)

        rowSpinBox = QSpinBox(dialog)
        rowSpinBox.setMinimum(1)
        rowSpinBox.setMaximum(config["table_max_rows"])
        rowSpinBox.setValue(3)
        rowLabel = QLabel("Number of rows:")
        form.addRow(rowLabel, rowSpinBox)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                           QDialogButtonBox.Cancel,
                                           Qt.Horizontal,
                                           dialog)

        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        form.addRow(buttonBox)

        dialog.setLayout(form)

        if dialog.exec_() == QDialog.Accepted:

            num_columns = columnSpinBox.value()
            num_rows = rowSpinBox.value() - 1

            num_header = create_counter(start=1, step=1)
            num_data = create_counter(start=1, step=1)

            # set width of each column equal
            width = 100 / num_columns

            header_html = u"<th {0}>header{1}</th>"
            header_column = "".join(header_html.format(
                self.HEAD_STYLING.format("left", width), next(num_header))
                for _ in range(num_columns))
            body_html = u"<td {0}>data{1}</td>"
            body_column = "".join(body_html.format(
                self.BODY_STYLING.format(width), next(num_data))
                for _ in range(num_columns))
            body_row = "<tr>{}</tr>".format(body_column) * num_rows

            html = u"""
            <table {0}>
                <thead><tr>{1}</tr></thead>
                <tbody>{2}</tbody>
            </table>""".format(self.TABLE_STYLING, header_column, body_row)

            self.editor_instance.web.eval(
                    "document.execCommand('insertHTML', false, %s);"
                    % json.dumps(html))

    def create_table_from_selection(self):
        """
        Create a table out of the selected text.
        """

        # there is no text to make a table from
        if not self.selected_text:
            return False

        # there is a single line of text
        if not self.selected_text.count(u"\n"):
            return False

        # there is no content in table
        if all(c in (u"|", u"\n") for c in self.selected_text):
            return False

        # split on newlines
        first = [x for x in self.selected_text.split(u"\n") if x]

        # split on pipes
        second = list()
        for elem in first[:]:
            new_elem = [x.strip() for x in elem.split(u"|")]
            new_elem = [escape_html_chars(word) for word in new_elem]
            second.append(new_elem)

        # keep track of the max number of cols
        # so as to make all rows of equal length
        max_num_cols = len(max(second, key=len))

        # decide how much horizontal space each column may take
        width = 100 / max_num_cols

        # check for "-|-|-" alignment row
        if all(x.strip(u":") in (u"-", u"") for x in second[1]):
            start = 2
            align_line = second[1]
            len_align_line = len(align_line)
            if len_align_line < max_num_cols:
                align_line += [u"-"] * (max_num_cols - len_align_line)
            alignments = list()
            for elem in second[1]:
                alignments.append(get_alignment(elem))
        else:
            alignments = [u"left"] * max_num_cols
            start = 1

        # create a table
        head_row = u""
        head_html = u"<th {0}>{1}</th>"
        for elem, alignment in zip(second[0], alignments):
            head_row += head_html.format(
                    self.HEAD_STYLING.format(alignment, width), elem)
        extra_cols = u""
        if len(second[0]) < max_num_cols:
            diff = len(second[0]) - max_num_cols
            assert diff < 0, \
                "Difference between len(second[0]) and max_num_cols is positive"
            for alignment in alignments[diff:]:
                extra_cols += head_html.format(
                        self.HEAD_STYLING.format(alignment, width), u"")
        head_row += extra_cols

        body_rows = u""
        for row in second[start:]:
            body_rows += u"<tr>"
            body_html = u"<td {0}>{1}</td>"
            for elem, alignment in zip(row, alignments):
                body_rows += body_html.format(
                        self.BODY_STYLING.format(alignment), elem)
            # if particular row is not up to par with number of cols
            extra_cols = ""
            if len(row) < max_num_cols:
                diff = len(row) - max_num_cols
                assert diff < 0, \
                    "Difference between len(row) and max_num_cols is positive"
                # use the correct alignment for the last few rows
                for alignment in alignments[diff:]:
                    extra_cols += body_html.format(
                            self.BODY_STYLING.format(alignment), u"")
            body_rows += extra_cols + u"</tr>"

        html = u"""
        <table {0}>
            <thead>
                <tr>
                    {1}
                </tr>
            </thead>
            <tbody>
                {2}
            </tbody>
        </table>""".format(self.TABLE_STYLING, head_row, body_rows)

        self.editor_instance.web.eval(
                "document.execCommand('insertHTML', false, %s);"
                % json.dumps(html))

        return True





def toggle_table(editor):
    selection = editor.web.selectedText()
    Table(editor, editor.parentWindow, selection if selection else None)
    

def setupEditorButtonsFilter(buttons, editor):
    global editor_instance
    editor_instance = editor

    key = QKeySequence(config['shortcut_insert_table'])
    keyStr = key.toString(QKeySequence.NativeText)

    if config['shortcut_insert_table']:
        b = editor.addButton(
            os.path.join(addon_path, "icons", "table.png"), 
            "tablebutton", 
            toggle_table, 
            tip="Insert Hyperlink ({})".format(keyStr),
            keys=config['shortcut_insert_table']) 
        buttons.append(b)

    return buttons

addHook("setupEditorButtons", setupEditorButtonsFilter)
