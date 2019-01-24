# -*- coding: utf-8 -*-

# - Licensed under the GNU AGPLv3.
# - this is a modification and extension of the table function from the
#   Power Format Pack: Copyright 2014-2017 Stefan van den 
#   Akker <neftas@protonmail.com>
# - the function setupEditorButtonsFilter is taken from "Auto Markdown"
#   from https://ankiweb.net/shared/info/1030875226 which should be
#   Copyright 2018 anonymous
#      maybe reddit user /u/NavyTeal, see https://www.reddit.com/r/Anki/comments/9t7acy/bringing_markdown_to_anki_21/
# - the styling "less ugly" is from the add-on add "tables with less ugly tables",
#   https://ankiweb.net/shared/info/1467671504, Copyright 2018 anonymous

import json
import os
import re
import uuid
from anki import version
from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, wrap


from codecs import open

from anki import version
ANKI21 = version.startswith("2.1.")

if ANKI21:
    from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QShortcut, QVBoxLayout, QHBoxLayout, QDialog, QLabel, QLineEdit
    from PyQt5.QtGui import QKeySequence
else:
    from PyQt4.QtGui import QHBoxLayout, QPushButton, QShortcut, QVBoxLayout, QHBoxLayout, QDialog, QLabel, QLineEdit
    from PyQt4.QtGui import QKeySequence


addon_path = os.path.dirname(__file__)


def load_config(conf):
    global config
    config=conf
    config['dstyle'] = config["table_style__default"]
    config["table_style_align"] = config["table_style__align_default"]
    config["table_style_first_row_is_header"]  = config["table_style__first_row_is_header_default"]
    config["table_style_column_width_fixed"] = config["table_style__column_width_fixed_default"]
    config["columnSpinBox_value"] = config["SpinBox_column_default_value"]
    config["rowSpinBox_value"] = config["SpinBox_row_default_value"]


if ANKI21:
    load_config(mw.addonManager.getConfig(__name__))
    mw.addonManager.setConfigUpdatedAction(__name__,load_config) 
else:
    moduleDir, _ = os.path.split(__file__)
    path = os.path.join(moduleDir, 'config.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data=f.read()
        load_config(json.loads(data))



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


place_holder_table = {
    #"strings in source" : ["strings in result", "temporary placeholder"]
    "\|":["&#124;",str(uuid.uuid4())],
}


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

    for i in place_holder_table.values():
        result = result.replace(i[1],i[0])

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
        self.setup()

    def setup(self):
        """
        Set the number of columns and rows for a new table.
        """

        # if the user has selected text, try to make a table out of it
        if self.selected_text:
            styling = config['dstyle']
            self.TABLE_STYLING = config['table_style_css'][styling]['TABLE_STYLING']
            self.HEAD_STYLING  = config['table_style_css'][styling]['HEAD_STYLING']
            self.BODY_STYLING  = config['table_style_css'][styling]['BODY_STYLING']
            is_table_created = self.create_table_from_selection()
            # if we could not make a table out of the selected text, present
            # user with dialog, otherwise do nothing
            if is_table_created:
                return None

        dialog = QDialog(self.parent_window)
        dialog.setWindowTitle("table")
        dialog.setStyleSheet(""" QCheckBox { padding-top: 7%; }  
                                 QLabel    { padding-top: 7%; }  """)  #height: 10px; margin: 0px; }")

        form = QFormLayout()
        form.addRow(QLabel("Enter table properties"))


        columnSpinBox = QSpinBox(dialog)
        columnSpinBox.setMinimum(1)
        columnSpinBox.setMaximum(config['Table_max_cols'])
        columnSpinBox.setValue(config["columnSpinBox_value"])
        columnLabel = QLabel("Number of columns:")
        #in QFormlayout I can't top align the labels - maybe https://stackoverflow.com/a/34656712
        #columnLabel.setAlignment(Qt.AlignTop)
        form.addRow(columnLabel, columnSpinBox)

        rowSpinBox = QSpinBox(dialog)
        rowSpinBox.setMinimum(1)
        rowSpinBox.setMaximum(config["Table_max_rows"])
        rowSpinBox.setValue(config["rowSpinBox_value"])
        rowLabel = QLabel("Number of rows:")
        form.addRow(rowLabel, rowSpinBox)

        cwidth = QCheckBox()
        cwidth.setText("")
        if config["table_style_column_width_fixed"] :
            cwidth.setChecked(True)
        cwidthLabel = QLabel("Fixed Width columns:")
        form.addRow(cwidthLabel, cwidth)

        frheader = QCheckBox()
        frheader.setText("")
        if config["table_style_first_row_is_header"] :
            frheader.setChecked(True)
        frheaderLabel = QLabel("first row is header:")
        form.addRow(frheaderLabel, frheader)

        ppheader = QCheckBox()
        ppheader.setText("")
        if config["table_pre-populate_header_fields"] :
            ppheader.setChecked(True)
        ppheaderLabel = QLabel("prefill fields:")
        form.addRow(ppheaderLabel, ppheader)

        styleComboBox = QComboBox(dialog)
        members = [config['dstyle'],]
        for s in config['table_style_css'].keys():
            if s != config['dstyle']: 
                members.append(s)
        styleComboBox.addItems(members)
        styleLabel = QLabel("styling:")
        form.addRow(styleLabel, styleComboBox)

        table_align = QComboBox(dialog)
        options = ['left','right','center',""]
        rest = [item for item in options if item != config["table_style_align"]]
        members = [config["table_style_align"]]
        for i in rest:
            members.append(i)
        table_align.addItems(members)
        table_align_label = QLabel("Table alignment (if existing):")
        form.addRow(table_align_label, table_align)

        useasdefault = QCheckBox()
        useasdefault.setText("")
        if config["last_used_overrides_default"] :
            useasdefault.setChecked(True)
        useasdefaultLabel = QLabel("Save these settings as\ndefault for next table:")
        form.addRow(useasdefaultLabel, useasdefault)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                           QDialogButtonBox.Cancel,
                                           Qt.Horizontal,
                                           dialog)

        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)

        form.addRow(buttonBox)

        dialog.setLayout(form)

        if dialog.exec_() == QDialog.Accepted:

            styling = styleComboBox.currentText()
            useheader = True if frheader.isChecked() else False
            fixedcolumnwidth = True if cwidth.isChecked() else False
            table_align = table_align.currentText()
            prefill = True if ppheader.isChecked() else False

            config['last_used_overrides_default'] =  True if useasdefault.isChecked() else False

            if config['last_used_overrides_default']:
                config['dstyle'] = styling
                config["table_style_align"] = table_align
                config["table_style_first_row_is_header"] = useheader
                config["table_style_column_width_fixed"] = fixedcolumnwidth
                config["columnSpinBox_value"] = columnSpinBox.value()
                config["rowSpinBox_value"] = rowSpinBox.value()
                config["table_pre-populate_header_fields"] = prefill
                config["table_pre-populate_body_fields"] = prefill

            num_columns = columnSpinBox.value()
            if useheader:
                num_rows = rowSpinBox.value() - 1
            else:
                num_rows = rowSpinBox.value()

            self.TABLE_STYLING = config['table_style_css'][styling]['TABLE_STYLING']
            self.HEAD_STYLING  = config['table_style_css'][styling]['HEAD_STYLING']
            self.BODY_STYLING  = config['table_style_css'][styling]['BODY_STYLING']

            num_header = create_counter(start=1, step=1)
            num_data = create_counter(start=1, step=1)


            # set width of each column equal
            if fixedcolumnwidth:
                width = 100 / num_columns
            else:
                width = ""

            if config["table_pre-populate_header_fields"]:
                header_html = u"<th {0}>header{1}</th>"
            else:
                header_html = u"<th {0}>&#x200b;</th>"
            if useheader:
                header_column = "".join(header_html.format(
                    self.HEAD_STYLING.format(table_align, width), next(num_header))
                    for _ in range(num_columns))

            if config["table_pre-populate_body_fields"]:
                body_html = u"<td {0}>data{1}</td>"
            else:
                body_html = u"<td {0}>&#x200b;</td>"
            body_column = "".join(body_html.format(
                self.BODY_STYLING.format(table_align,width), next(num_data))
                for _ in range(num_columns))
            body_row = "<tr>{}</tr>".format(body_column) * num_rows

            if useheader:
                html = u"""
                <table {0}>
                    <thead><tr>{1}</tr></thead>
                    <tbody>{2}</tbody>
                </table>""".format(self.TABLE_STYLING, header_column, body_row)
            else:
                html = u"""
                <table {0}>
                    <tbody>{1}</tbody>
                </table>""".format(self.TABLE_STYLING, body_row)

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

        # - split on newlines
        # - strip to remove leading/trailing spaces: Otherwise the detection of
        #   markdown tables might not work and a space might generate a new column
        # - To include a pipe as content escape the backslash (as in GFM spec)
        stx = self.selected_text
        for k,v in place_holder_table.items():
            stx = stx.replace(k,v[1])
        first = [x.strip() for x in stx.split(u"\n") if x]

        # split on pipes
        second = list()
        for elem in first[:]:
            if elem.startswith('|') and elem.endswith('|'):
                elem = elem[1:-1]
            new_elem = [x.strip() for x in elem.split(u"|")]
            new_elem = [escape_html_chars(word) for word in new_elem]
            second.append(new_elem)

        # keep track of the max number of cols
        # so as to make all rows of equal length
        max_num_cols = len(max(second, key=len))

        # decide how much horizontal space each column may take
        width = 100 / max_num_cols

        # check for "-|-|-" alignment row
        second[1] = [re.sub(r"-+",'-',x) for x in second[1]]
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
                        self.BODY_STYLING.format(alignment,width), elem)
            # if particular row is not up to par with number of cols
            extra_cols = ""
            if len(row) < max_num_cols:
                diff = len(row) - max_num_cols
                assert diff < 0, \
                    "Difference between len(row) and max_num_cols is positive"
                # use the correct alignment for the last few rows
                for alignment in alignments[diff:]:
                    extra_cols += body_html.format(
                            self.BODY_STYLING.format(alignment,width), u"")
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
    

if ANKI21:
    def setupEditorButtonsFilter(buttons, editor):
        global editor_instance
        editor_instance = editor
        key = QKeySequence(config['Key_insert_table'])
        keyStr = key.toString(QKeySequence.NativeText)
        if config['Key_insert_table']:
            b = editor.addButton(
                os.path.join(addon_path, "icons", "table.png"), 
                "tablebutton", 
                toggle_table, 
                tip="Insert table ({})".format(keyStr),
                keys=config['Key_insert_table']) 
            buttons.append(b)
        return buttons
    addHook("setupEditorButtons", setupEditorButtonsFilter)
else:
    key = QKeySequence(config['Key_insert_table'])
    keyStr = key.toString(QKeySequence.NativeText)
    
    from aqt.editor import Editor
    def mySetupButtons(self):
        b = self._addButton("my_pfp_html_table", lambda s=self: toggle_table(self),
                text=" ", tip="Insert table ({})".format(keyStr), key=config['Key_insert_table'])
        b.setIcon(QIcon(os.path.join(mw.pm.addonFolder(), 'add_table', 'icons', 'table.png')))
    Editor.setupButtons = wrap(Editor.setupButtons, mySetupButtons)
