import csv
import io
from typing import List, Optional, Set

from PySide6.QtCore import (QAbstractTableModel, QModelIndex, QSortFilterProxyModel,
                            Qt, Signal)
from PySide6.QtGui import QBrush, QColor, QFont

import theme
from fields import BOOL_FIELDS
from history import UndoHistory
from weapon_csv import (NAME_FIELD, Row, WeaponCSV, derive_upgrade_name,
                        diff_line_numbers, read_csv_lines, write_text)

_DISPLAY = int(Qt.DisplayRole)
_EDIT = int(Qt.EditRole)
_FONT = int(Qt.FontRole)
_FOREGROUND = int(Qt.ForegroundRole)
_BACKGROUND = int(Qt.BackgroundRole)
_TOOLTIP = int(Qt.ToolTipRole)
_CHECK = int(Qt.CheckStateRole)
_HANDLED_ROLES = frozenset((_DISPLAY, _EDIT, _FONT, _FOREGROUND, _BACKGROUND,
                            _TOOLTIP, _CHECK))


class WeaponTableModel(QAbstractTableModel):

    dirtyChanged = Signal(bool)
    historyChanged = Signal()
    loadWarning = Signal(str, str)
    validationFailed = Signal(str)
    structureChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.csv = WeaponCSV()
        self.history = UndoHistory(self.csv)
        self.path: Optional[str] = None
        self.preview_error = ""
        self._dirty = False
        self._baseline = ""
        self._baseline_rows = set()
        self._bool_cols = frozenset()

        self._font_plain = QFont(theme.FONT, 9)
        self._font_italic = QFont(self._font_plain)
        self._font_italic.setItalic(True)
        self._font_bold = QFont(self._font_plain)
        self._font_bold.setBold(True)
        self._brush_muted = QBrush(QColor(theme.FG_MUTED))
        self._brush_label = QBrush(QColor(theme.FG_LABEL))
        self._brush_changed_fg = QBrush(QColor(theme.ROW_CHANGED_FG))
        self._brush_changed_bg = QBrush(QColor(theme.ROW_CHANGED))

    @property
    def headers(self) -> List[str]:
        return self.csv.headers

    @property
    def rows(self) -> List[Row]:
        return self.csv.rows

    @property
    def dirty(self) -> bool:
        return self._dirty

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.csv.rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.csv.headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.csv.headers[section].replace("_", " ")
            if role == Qt.ToolTipRole:
                return self.csv.headers[section]
        elif role == Qt.DisplayRole:
            return str(section + 1)
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() in self._bool_cols:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        role = int(role)
        if role not in _HANDLED_ROLES:
            return None
        rows = self.csv.rows
        line = index.row()
        if line < 0 or line >= len(rows):
            return None
        row = rows[line]

        if role == _CHECK:
            if index.column() not in self._bool_cols:
                return None
            return (Qt.Checked if row.get(index.column()).strip().lower() == "true"
                    else Qt.Unchecked)
        if role == _DISPLAY and index.column() in self._bool_cols:
            return None
        if role == _DISPLAY or role == _EDIT:
            return row.get(index.column())
        if role == _FONT:
            if not row.commented:
                return self._font_plain
            return (self._font_bold if self.csv.is_section_label(line)
                    else self._font_italic)
        if role == _FOREGROUND:
            if row.commented:
                return (self._brush_label if self.csv.is_section_label(line)
                        else self._brush_muted)
            return self._brush_changed_fg if row.changed else None
        if role == _BACKGROUND:
            return self._brush_changed_bg if row.changed else None

        bits = []
        if row.commented:
            bits.append("commented out with //")
        blanks = len(row.blanks_before)
        if blanks:
            bits.append(str(blanks) + " blank line(s) above")
        return "\n".join(bits) or None

    def setData(self, index, value, role=Qt.EditRole) -> bool:
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole and index.column() in self._bool_cols:
            value = "TRUE" if Qt.CheckState(value) == Qt.Checked else "FALSE"
        elif role != Qt.EditRole:
            return False
        if index.column() == self.csv.column_index(NAME_FIELD):
            return self.rename_row(index.row(), str(value))

        row = self.csv.rows[index.row()]
        text = "" if value is None else str(value)
        if row.get(index.column()) == text:
            return True
        self._record("edit " + self.csv.headers[index.column()].replace("_", " "),
                     key=("cell", index.row(), index.column()), row=index.row())
        row.set(index.column(), text)
        self._touch(index.row())
        self.dataChanged.emit(index, index)
        return True

    def rename_row(self, row_idx: int, name: str) -> bool:
        if not self.csv.valid_index(row_idx):
            return False
        row = self.csv.rows[row_idx]
        name_col = self.csv.column_index(NAME_FIELD)
        if name_col is None:
            return False
        old_name = row.get(name_col)
        new_name = name.strip()
        if new_name == old_name:
            return True
        if not new_name:
            self.validationFailed.emit("weapon_name cannot be empty.")
            self._refresh_row(row_idx)
            return False
        clash = (None if row.commented
                 else self.csv.find_by_name(new_name, exclude=row_idx))
        if clash is not None:
            self.validationFailed.emit(
                "'" + new_name + "' already exists on row " + str(clash + 1) + ".")
            self._refresh_row(row_idx)
            return False

        self._record("rename weapon", key=("name", row_idx), row=row_idx)
        row.set(name_col, new_name)
        upgrade_col = self.csv.column_index("upgrade_name")
        if upgrade_col is not None:
            row.set(upgrade_col, derive_upgrade_name(
                row.get(upgrade_col), old_name, new_name))
        self._touch(row_idx)
        self._refresh_row(row_idx)
        return True

    def load(self, path: str) -> None:
        lines = read_csv_lines(path)
        if not lines:
            raise ValueError("The file contains no data.")
        replacement = WeaponCSV()
        replacement.load_lines(lines)
        self.beginResetModel()
        self.csv.headers = replacement.headers
        self.csv.rows = replacement.rows
        self.csv.trailing_blanks = replacement.trailing_blanks
        self._bool_cols = frozenset(i for i, header in enumerate(self.csv.headers)
                                    if header in BOOL_FIELDS)
        self.path = path
        self.preview_error = ""
        self.endResetModel()
        self._set_baseline(self.csv.render())
        self.history.clear()
        self.historyChanged.emit()
        self.set_dirty(False)
        self.structureChanged.emit()

        dupes = self.csv.duplicate_headers()
        if dupes:
            self.loadWarning.emit(
                "Column Warning",
                "This file has more than one column called: "
                + ", ".join(dupes)
                + ".\n\nEvery one of them is kept and saved separately, but the "
                "Editor tab can only show the first of each name. Use the "
                "Spreadsheet tab to edit the others.")

        names = self.csv.duplicate_names()
        if names:
            self.loadWarning.emit(
                "Duplicate Weapons",
                "This file has more than one live weapon called:\n\n"
                + "\n".join(name + " (rows "
                            + ", ".join(str(i + 1) for i in rows) + ")"
                            for name, rows in names.items())
                + "\n\nThe game only keeps the last one's settings. Rename "
                "or comment out the extras.")

    def replace_text(self, text: str) -> None:
        try:
            lines = list(csv.reader(io.StringIO(text), strict=True))
            replacement = WeaponCSV()
            if lines:
                replacement.load_lines(lines)
        except (csv.Error, ValueError) as exc:
            self.preview_error = str(exc)
            self.set_dirty(True)
            raise ValueError(self.preview_error) from exc
        self.preview_error = ""
        if replacement.render() == self.csv.render():
            self.set_dirty(self.csv.render() != self._baseline)
            return
        self._record("Edit CSV preview", key="preview")
        self.beginResetModel()
        self.csv.headers = replacement.headers
        self._bool_cols = frozenset(i for i, header in enumerate(self.csv.headers)
                                    if header in BOOL_FIELDS)
        self.csv.rows = replacement.rows
        self.csv.trailing_blanks = replacement.trailing_blanks
        for row in self.csv.rows:
            row.changed = self._row_key(row) not in self._baseline_rows
        self.endResetModel()
        self.set_dirty(self.csv.render() != self._baseline)
        self.structureChanged.emit()

    def save(self, path: str) -> None:
        if self.preview_error:
            raise ValueError("Fix the CSV in Preview before saving: " + self.preview_error)
        text = self.csv.render()
        write_text(path, self.csv.render("\r\n"))
        self._set_baseline(text)
        self.path = path
        for row in self.csv.rows:
            row.changed = False
        self.history.break_merge()
        self.set_dirty(False)
        self._refresh_all()

    def add_row(self, values: Optional[dict] = None) -> int:
        row = self.csv.new_row()
        for field, value in (values or {}).items():
            row.set(field, value)
        pos = len(self.csv.rows)
        self._record("add weapon", row=pos)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self.csv.append_row(row)
        self.endInsertRows()
        self._touch(pos)
        self.structureChanged.emit()
        return pos

    def duplicate_row(self, row_idx: int, new_name: str) -> Optional[int]:
        if not self.csv.valid_index(row_idx):
            return None
        self._record("copy weapon", row=len(self.csv.rows))
        src = self.csv.duplicate_row(row_idx)
        old_name = src.get(NAME_FIELD)
        src.set(NAME_FIELD, new_name)
        src.set("upgrade_name", derive_upgrade_name(
            src.get("upgrade_name"), old_name, new_name))
        pos = len(self.csv.rows)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self.csv.append_row(src)
        self.endInsertRows()
        self._touch(pos)
        self.structureChanged.emit()
        return pos

    def delete_row(self, row_idx: int) -> None:
        if not self.csv.valid_index(row_idx):
            return
        self._record("delete weapon", row=row_idx)
        self.beginRemoveRows(QModelIndex(), row_idx, row_idx)
        self.csv.delete_row(row_idx)
        self.endRemoveRows()
        self.set_dirty(self.csv.render() != self._baseline)
        self.structureChanged.emit()

    def toggle_comment(self, row_idx: int) -> bool:
        if not self.csv.valid_index(row_idx):
            return False
        row = self.csv.rows[row_idx]
        if row.commented:
            name = row.get(NAME_FIELD).strip()
            clash = self.csv.find_by_name(name, exclude=row_idx)
            if clash is not None:
                self.validationFailed.emit(
                    "Can't uncomment: '" + name + "' already exists on row "
                    + str(clash + 1) + ".")
                return False
        self._record("uncomment" if row.commented else "comment out",
                     row=row_idx)
        self.csv.toggle_comment(row_idx)
        self._touch(row_idx)
        self._refresh_row(row_idx)
        self.structureChanged.emit()
        return True

    def remove_blank_before(self, row_idx: int) -> None:
        if not self.csv.valid_index(row_idx) or not self.blanks_before(row_idx):
            return
        self._record("remove section break", row=row_idx)
        self.csv.remove_blank_before(row_idx)
        self._touch(row_idx)
        self._refresh_row(row_idx)
        self.structureChanged.emit()

    def is_section_label(self, row_idx: int) -> bool:
        if not self.csv.valid_index(row_idx):
            return False
        return self.csv.is_section_label(row_idx)

    def add_blank_before(self, row_idx: int) -> None:
        if not self.csv.valid_index(row_idx):
            return
        self._record("section break", row=row_idx)
        self.csv.add_blank_before(row_idx)
        self._touch(row_idx)
        self._refresh_row(row_idx)
        self.structureChanged.emit()

    def _record(self, label: str, key=None, row: Optional[int] = None) -> None:
        self.history.record(label, key, row)
        self.historyChanged.emit()

    def can_undo(self) -> bool:
        return self.history.can_undo()

    def can_redo(self) -> bool:
        return self.history.can_redo()

    def undo_label(self) -> str:
        return self.history.undo_label()

    def redo_label(self) -> str:
        return self.history.redo_label()

    def undo(self) -> Optional[int]:
        if not self.can_undo():
            return None
        return self._apply(self.history.undo)

    def redo(self) -> Optional[int]:
        if not self.can_redo():
            return None
        return self._apply(self.history.redo)

    def _apply(self, step) -> Optional[int]:
        self.beginResetModel()
        try:
            entry = step()
            self.preview_error = ""
            self._bool_cols = frozenset(i for i, header in enumerate(self.csv.headers)
                                        if header in BOOL_FIELDS)
            for row in self.csv.rows:
                row.changed = self._row_key(row) not in self._baseline_rows
        finally:
            self.endResetModel()
        self.set_dirty(self.csv.render() != self._baseline)
        self.historyChanged.emit()
        self.structureChanged.emit()
        if entry.row is None:
            return None
        return max(0, min(entry.row, len(self.csv.rows) - 1))

    def is_bool_column(self, col: int) -> bool:
        return col in self._bool_cols

    def column_of(self, field: str) -> Optional[int]:
        return self.csv.column_index(field)

    def name_of(self, row_idx: int) -> str:
        if not self.csv.valid_index(row_idx):
            return ""
        return self.csv.rows[row_idx].get(NAME_FIELD)

    def blanks_before(self, row_idx: int) -> int:
        return self.csv.blanks_before(row_idx)

    def is_commented(self, row_idx: int) -> bool:
        if not self.csv.valid_index(row_idx):
            return False
        return self.csv.rows[row_idx].commented

    def render(self) -> str:
        return self.csv.render()

    def changed_lines(self) -> Set[int]:
        if not self._dirty:
            return set()
        return diff_line_numbers(self.csv.render(), self._baseline)

    def options_for(self, field: str, base: List[str]) -> List[str]:
        if self.column_of(field) is None:
            return list(base)
        found = self.csv.distinct_values(field)
        extra = [v for v in found if v not in base]
        if base and all(v.isdigit() for v in list(base) + extra):
            return sorted(set(base) | set(extra), key=int)
        return list(base) + sorted(extra)

    def set_dirty(self, dirty: bool) -> None:
        if self._dirty == dirty:
            return
        self._dirty = dirty
        self.dirtyChanged.emit(dirty)

    def _set_baseline(self, text: str) -> None:
        self._baseline = text
        self._baseline_rows = {self._row_key(row) for row in self.csv.rows}

    @staticmethod
    def _row_key(row: Row) -> tuple:
        return (tuple(row.cells), row.commented, tuple(row.blanks_before))

    def _touch(self, row_idx: int) -> None:
        if self.csv.valid_index(row_idx):
            row = self.csv.rows[row_idx]
            row.changed = self._row_key(row) not in self._baseline_rows
        self.set_dirty(self.csv.render() != self._baseline)

    def _refresh_row(self, row_idx: int) -> None:
        if not self.csv.headers:
            return
        left = self.index(row_idx, 0)
        right = self.index(row_idx, len(self.csv.headers) - 1)
        self.dataChanged.emit(left, right)

    def _refresh_all(self) -> None:
        if not self.csv.rows or not self.csv.headers:
            return
        left = self.index(0, 0)
        right = self.index(len(self.csv.rows) - 1, len(self.csv.headers) - 1)
        self.dataChanged.emit(left, right)


class WeaponFilterProxy(QSortFilterProxyModel):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._query = ""
        self.setSortRole(Qt.EditRole)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.setDynamicSortFilter(False)

    def set_query(self, text: str) -> None:
        self._query = text.strip().lower()
        self.invalidateFilter()

    def shows_file_order(self) -> bool:
        return not self._query and self.sortColumn() < 0

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        if not self._query:
            return True
        model = self.sourceModel()
        if model is None or source_row >= len(model.rows):
            return True
        return model.csv.row_matches(model.rows[source_row], self._query)
