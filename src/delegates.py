from typing import Optional

from PySide6.QtCore import QEvent, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import (QApplication, QComboBox, QStyle,
                               QStyledItemDelegate, QStyleOptionViewItem)

import theme
from fields import BASE_OPTIONS, COMBO_TYPES, EDITABLE_COMBOS, FIELD_TYPES
from weapon_csv import upgrade_suggestions


class CellEditorDelegate(QStyledItemDelegate):

    def __init__(self, model, proxy, parent=None) -> None:
        super().__init__(parent)
        self._model = model
        self._proxy = proxy

    def _field(self, index) -> Optional[str]:
        column = self._proxy.mapToSource(index).column()
        headers = self._model.headers
        if 0 <= column < len(headers):
            return headers[column]
        return None

    def createEditor(self, parent, option, index):
        field = self._field(index)
        wtype = FIELD_TYPES.get(field)
        if wtype == "count":
            return theme.SpinBox(parent)
        if wtype not in COMBO_TYPES:
            return super().createEditor(parent, option, index)

        combo = theme.ChevronComboBox(parent)
        combo.setEditable(wtype in EDITABLE_COMBOS)
        if wtype == "upgrade":
            row = self._proxy.mapToSource(index).row()
            combo.addItems(upgrade_suggestions(self._model.name_of(row)))
        else:
            combo.addItems(self._model.options_for(field, BASE_OPTIONS[wtype]))
        if combo.isEditable():
            combo.setInsertPolicy(QComboBox.NoInsert)
        combo.activated.connect(lambda _i: self._finish(combo))
        return combo

    def _finish(self, combo) -> None:
        self.commitData.emit(combo)
        self.closeEditor.emit(combo)

    def setEditorData(self, editor, index) -> None:
        if isinstance(editor, theme.SpinBox):
            editor.raw = index.data(Qt.EditRole) or ""
            return
        if isinstance(editor, theme.ChevronComboBox):
            editor.value = index.data() or ""
            if editor.isEditable():
                editor.lineEdit().setCursorPosition(0)
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index) -> None:
        if isinstance(editor, theme.SpinBox):
            model.setData(index, editor.raw)
            return
        if isinstance(editor, theme.ChevronComboBox):
            model.setData(index, editor.value)
            return
        super().setModelData(editor, model, index)


class SectionBreakDelegate(CellEditorDelegate):

    GAP_PER_LINE = 9
    MAX_GAP = 27

    def gap_for(self, index) -> int:
        if not index.isValid() or not self._proxy.shows_file_order():
            return 0
        row = self._proxy.mapToSource(index).row()
        blanks = self._model.blanks_before(row)
        if not blanks:
            return 0
        return min(blanks * self.GAP_PER_LINE, self.MAX_GAP)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(size.height() + self.gap_for(index))
        return size

    def paint(self, painter, option, index) -> None:
        gap = self.gap_for(index)
        if not gap:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setPen(QPen(QColor(theme.BORDER), 1))
        y = option.rect.top() + gap // 2
        painter.drawLine(option.rect.left(), y, option.rect.right(), y)
        painter.restore()

        shifted = QStyleOptionViewItem(option)
        shifted.rect = QRect(option.rect.left(), option.rect.top() + gap,
                             option.rect.width(), option.rect.height() - gap)
        super().paint(painter, shifted, index)


class CheckDelegate(SectionBreakDelegate):

    BOX = 16
    INDENT = 7

    def _cell(self, option, index) -> QRect:
        gap = self.gap_for(index)
        return QRect(option.rect.left(), option.rect.top() + gap,
                     option.rect.width(), option.rect.height() - gap)

    def _box(self, cell: QRect) -> QRectF:
        return QRectF(cell.left() + self.INDENT + 0.5,
                      cell.top() + (cell.height() - self.BOX) / 2 + 0.5,
                      self.BOX, self.BOX)

    def paint(self, painter, option, index) -> None:
        gap = self.gap_for(index)
        if gap:
            painter.save()
            painter.setPen(QPen(QColor(theme.BORDER), 1))
            y = option.rect.top() + gap // 2
            painter.drawLine(option.rect.left(), y, option.rect.right(), y)
            painter.restore()

        cell = self._cell(option, index)
        styled = QStyleOptionViewItem(option)
        self.initStyleOption(styled, index)
        styled.rect = cell
        styled.features &= ~QStyleOptionViewItem.HasCheckIndicator
        styled.text = ""
        widget = styled.widget
        style = widget.style() if widget else QApplication.style()
        style.drawPrimitive(QStyle.PE_PanelItemViewItem, styled, painter, widget)
        theme.draw_check(painter, self._box(cell),
                         index.data(Qt.CheckStateRole) == Qt.Checked,
                         selected=bool(option.state & QStyle.State_Selected))

    def editorEvent(self, event, model, option, index) -> bool:
        kind = event.type()
        if kind in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick):
            return (event.button() == Qt.LeftButton
                    and self._box(self._cell(option, index)).contains(event.position()))
        if kind == QEvent.MouseButtonRelease:
            if (event.button() != Qt.LeftButton
                    or not self._box(self._cell(option, index)).contains(event.position())):
                return False
        elif kind == QEvent.KeyPress:
            if event.key() not in (Qt.Key_Space, Qt.Key_Select):
                return False
        else:
            return False
        checked = index.data(Qt.CheckStateRole) == Qt.Checked
        return model.setData(index, Qt.Unchecked if checked else Qt.Checked,
                             Qt.CheckStateRole)
