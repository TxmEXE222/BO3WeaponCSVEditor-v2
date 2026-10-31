from typing import Set

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

import theme


class CSVHighlighter(QSyntaxHighlighter):

    def __init__(self, document) -> None:
        super().__init__(document)
        self._columns = [self._format(color) for color in
                         ("#6688cc", "#225588", "#ddbb88", "#384887",
                          "#22aa44", "#2277ff", "#f280d0", "#ffeebb",
                          "#22aa44", "#a22d44")]
        self._columns[5].setFontItalic(True)
        self._columns[7].setFontUnderline(True)
        self._columns[8].setFontWeight(QFont.Bold)
        self._comment = self._format("#384887")

    @staticmethod
    def _format(color):
        result = QTextCharFormat()
        result.setForeground(QColor(color))
        return result

    def highlightBlock(self, text: str) -> None:
        previous = self.previousBlockState()
        quoted = previous > 0
        column = previous - 1 if quoted else 0
        if not quoted and text.lstrip().startswith("//"):
            self.setFormat(0, len(text.encode("utf-16-le")) // 2, self._comment)
            self.setCurrentBlockState(0)
            return
        start = 0
        index = 0
        offsets = [0]
        for char in text:
            offsets.append(offsets[-1] + (2 if ord(char) > 65535 else 1))
        while index <= len(text):
            if index == len(text) or (text[index] == ',' and not quoted):
                style = self._columns[column % len(self._columns)]
                self.setFormat(offsets[start], offsets[index] - offsets[start], style)
                if index < len(text):
                    self.setFormat(offsets[index], 1, style)
                    column += 1
                start = index + 1
            elif text[index] == '"':
                if quoted:
                    if index + 1 < len(text) and text[index + 1] == '"':
                        index += 1
                    else:
                        quoted = False
                elif index == start:
                    quoted = True
            index += 1
        self.setCurrentBlockState(column + 1 if quoted else 0)


class _LineNumberArea(QWidget):

    def __init__(self, editor) -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor.paint_line_numbers(event)


class PreviewView(QPlainTextEdit):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._changed: Set[int] = set()
        self._gutter = _LineNumberArea(self)
        self._highlighter = CSVHighlighter(self.document())

        font = QFont(theme.MONO_FONT, 10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFrameShape(QPlainTextEdit.NoFrame)
        self.setStyleSheet(
            "QPlainTextEdit { background: %s; color: %s; border: 1px solid %s;"
            " border-radius: 8px; selection-background-color: %s; }"
            % (theme.PREVIEW_BG, theme.FG, theme.BORDER, theme.PREVIEW_SELECT))

        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._update_gutter)
        self._update_gutter_width()

    def set_content(self, text: str, changed: Set[int]) -> None:
        scroll = self.verticalScrollBar().value()
        self._changed = changed
        self.blockSignals(True)
        self.setPlainText(text)
        self.blockSignals(False)
        self.verticalScrollBar().setValue(scroll)
        self._highlight_changed()
        self._gutter.update()

    def line_number_width(self) -> int:
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def paint_line_numbers(self, event) -> None:
        painter = QPainter(self._gutter)
        painter.fillRect(event.rect(), QColor(theme.PREVIEW_GUTTER_BG))

        block = self.firstVisibleBlock()
        number = block.blockNumber() + 1
        top = self.blockBoundingGeometry(block).translated(
            self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if number in self._changed:
                    painter.setPen(QColor(theme.ROW_CHANGED_FG))
                else:
                    painter.setPen(QColor(theme.FG_MUTED))
                painter.drawText(0, int(top), self._gutter.width() - 8, height,
                                 Qt.AlignRight, str(number))
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            number += 1

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        rect = self.contentsRect()
        self._gutter.setGeometry(
            QRect(rect.left(), rect.top(), self.line_number_width(), rect.height()))

    def _update_gutter_width(self) -> None:
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def _update_gutter(self, rect, dy) -> None:
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_gutter_width()

    def _highlight_changed(self) -> None:
        selections = []
        doc = self.document()
        for number in sorted(self._changed):
            block = doc.findBlockByNumber(number - 1)
            if not block.isValid():
                continue
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(theme.ROW_CHANGED))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            cursor = QTextCursor(block)
            cursor.clearSelection()
            selection.cursor = cursor
            selections.append(selection)
        self.setExtraSelections(selections)
