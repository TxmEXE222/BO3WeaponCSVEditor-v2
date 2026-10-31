from typing import Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QDataWidgetMapper, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QLineEdit, QSizePolicy,
                               QToolButton, QVBoxLayout, QWidget)

import attachments
import theme
from fields import (BASE_OPTIONS, COMBO_TYPES, EDITABLE_COMBOS, EDITOR_LAYOUT,
                    FIELD_TIPS)
from weapon_csv import NAME_FIELD, upgrade_suggestions


class FormPanel(QWidget):

    rowRenamed = Signal(int)

    def __init__(self, model, parent=None) -> None:
        super().__init__(parent)
        self._model = model
        self._widgets: Dict[str, QWidget] = {}
        self._labels: Dict[str, QLabel] = {}
        self._types: Dict[str, str] = {}
        self._row = -1

        self._mapper = QDataWidgetMapper(self)
        self._mapper.setModel(model)
        self._mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        card = QFrame()
        card.setObjectName("Card")
        split = QHBoxLayout(card)
        split.setContentsMargins(16, 14, 16, 16)
        split.setSpacing(18)
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(4)
        split.addLayout(grid, 1)

        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedWidth(1)
        split.addWidget(divider)

        checks = QVBoxLayout()
        checks.setSpacing(6)
        split.addLayout(checks)

        for field, row, col, span, wtype in EDITOR_LAYOUT:
            label_text = field.replace("_", " ")
            tip = theme.tooltip(FIELD_TIPS.get(field, ""), title=label_text)
            if wtype == "bool":
                widget = theme.CheckBox(label_text)
                widget.setToolTip(tip)
                widget.setMinimumHeight(30)
                checks.addWidget(widget)
                label = widget
            else:
                label = QLabel(label_text)
                label.setObjectName("FieldLabel")
                label.setToolTip(tip)
                label.setCursor(Qt.WhatsThisCursor)
                grid.addWidget(label, row * 2, col, 1, span)

                widget = self._make_widget(field, wtype)
                widget.setToolTip(tip)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                if wtype == "attachments":
                    grid.addLayout(self._with_picker(widget), row * 2 + 1, col,
                                   1, span)
                else:
                    grid.addWidget(widget, row * 2 + 1, col, 1, span)

            self._widgets[field] = widget
            self._labels[field] = label
            self._types[field] = wtype
            if field != NAME_FIELD:
                self._connect_live_commit(widget)

        for col in range(2):
            grid.setColumnStretch(col, 1)
        checks.addStretch(1)

        outer.addWidget(card)

        self._extra_label = QLabel("")
        self._extra_label.setObjectName("MutedLabel")
        self._extra_label.setWordWrap(True)
        self._extra_label.hide()
        outer.addWidget(self._extra_label)
        outer.addStretch(1)

        name_edit = self._widgets[NAME_FIELD]
        name_edit.editingFinished.connect(self._commit_name)
        name_edit.textEdited.connect(
            lambda _t: self._set_invalid(name_edit, False))
        model.validationFailed.connect(self._on_invalid)
        model.dataChanged.connect(self._on_data_changed)

        self.set_row(-1)

    def _make_widget(self, field: str, wtype: str) -> QWidget:
        if wtype == "count":
            return theme.SpinBox()
        if wtype in COMBO_TYPES:
            combo = theme.ChevronComboBox()
            combo.setEditable(wtype in EDITABLE_COMBOS)
            combo.addItems(BASE_OPTIONS.get(wtype, []))
            if combo.isEditable():
                combo.setInsertPolicy(QComboBox.NoInsert)
            return combo
        return QLineEdit()

    def _with_picker(self, field: QLineEdit) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(field, 1)
        self._picker_button = QToolButton()
        self._picker_button.setObjectName("PickerButton")
        self._picker_button.setText("Choose…")
        self._picker_button.setCursor(Qt.PointingHandCursor)
        self._picker_button.clicked.connect(self._open_picker)
        row.addWidget(self._picker_button)
        return row

    def _connect_live_commit(self, widget: QWidget) -> None:
        if isinstance(widget, theme.CheckBox):
            widget.clicked.connect(lambda _c: self.submit())
        elif isinstance(widget, theme.SpinBox):
            widget.rawChanged.connect(lambda _t: self.submit())
        elif isinstance(widget, QComboBox):
            widget.activated.connect(lambda _i: self.submit())
            if widget.isEditable():
                widget.lineEdit().textEdited.connect(lambda _t: self.submit())
        else:
            widget.textEdited.connect(lambda _t: self.submit())

    def submit(self) -> None:
        if self._row < 0:
            return
        self._mapper.submit()

    def commit_pending(self) -> None:
        self._commit_name()
        self.submit()

    def rebind(self) -> None:
        self._mapper.clearMapping()

        for field, widget in self._widgets.items():
            col = self._model.column_of(field)
            widget.setEnabled(col is not None)
            if col is None:
                self._clear_widget(widget)
                continue

            wtype = self._types[field]
            if wtype in COMBO_TYPES and wtype != "upgrade":
                current = widget.value
                widget.blockSignals(True)
                widget.clear()
                widget.addItems(self._model.options_for(field, BASE_OPTIONS[wtype]))
                widget.value = current
                widget.blockSignals(False)

            if field == NAME_FIELD:
                continue
            if wtype in COMBO_TYPES or wtype == "bool":
                self._mapper.addMapping(widget, col, b"value")
            elif wtype == "count":
                self._mapper.addMapping(widget, col, b"raw")
            else:
                self._mapper.addMapping(widget, col)

        known = {f for f, *_ in EDITOR_LAYOUT}
        extra = [h for h in self._model.headers if h not in known]
        if extra:
            self._extra_label.setText(
                "Columns in this file with no form field (edit them in the "
                "Spreadsheet tab): " + ", ".join(extra))
            self._extra_label.show()
        else:
            self._extra_label.hide()

    def set_row(self, row: int) -> None:
        self._row = row
        if row < 0:
            self._mapper.setCurrentIndex(-1)
            for widget in self._widgets.values():
                self._clear_widget(widget)
                widget.setEnabled(False)
            self._picker_button.setEnabled(False)
            self._update_ammo_hint()
            return

        for field, widget in self._widgets.items():
            widget.setEnabled(self._model.column_of(field) is not None)
        self._mapper.setCurrentIndex(row)
        self._reload_name()
        self._refresh_upgrade_options()
        self._update_ammo_hint()
        tables = (attachments.table_path(attachments.MAPPINGS, self._model.path)
                  or attachments.table_path(attachments.DEFINITIONS, self._model.path))
        self._picker_button.setEnabled(
            bool(tables) and self._model.column_of("force_attachments") is not None)
        self._picker_button.setToolTip(theme.tooltip(
            "Pick from the game's attachment tables" if tables else
            "Needs the BO3 mod tools (TA_TOOLS_PATH) to find the attachment tables"))

    def _on_data_changed(self, top_left, bottom_right, *_roles) -> None:
        if not top_left.row() <= self._row <= bottom_right.row():
            return
        columns = range(top_left.column(), bottom_right.column() + 1)
        if self._model.column_of(NAME_FIELD) in columns:
            self._reload_name()
            self._refresh_upgrade_options()
        if self._model.column_of("cost") in columns:
            self._update_ammo_hint()

    def _refresh_upgrade_options(self) -> None:
        widget = self._widgets["upgrade_name"]
        current = widget.value
        widget.blockSignals(True)
        widget.clear()
        widget.addItems(upgrade_suggestions(self._model.name_of(self._row)))
        widget.value = current
        widget.blockSignals(False)

    def _update_ammo_hint(self) -> None:
        line = self._widgets["ammo_cost"].lineEdit()
        if self._row < 0 or self._model.column_of("cost") is None:
            line.setPlaceholderText("")
            return
        cost = self._model.rows[self._row].get("cost").strip()
        if not cost.isdigit():
            line.setPlaceholderText("auto: half the cost")
            return
        half = int(int(cost) * 0.5)
        auto = half if half % 10 == 0 else half - half % 10 + 10
        line.setPlaceholderText("auto: %d (half the cost)" % auto)

    def _open_picker(self) -> None:
        if self._row < 0:
            return
        weapon = self._model.name_of(self._row)
        found = attachments.choices(weapon, self._model.path)
        if found is None:
            return
        grouped, listed = found
        field = self._widgets["force_attachments"]
        picker = attachments.AttachmentPicker(weapon, grouped, listed, field.text(),
                                              self)
        picker.setAttribute(Qt.WA_DeleteOnClose)
        picker.changed.connect(self._set_attachments)
        picker.show_below(self._picker_button)

    def _set_attachments(self, text: str) -> None:
        self._widgets["force_attachments"].setText(text)
        self.submit()

    def focus_name(self) -> None:
        widget = self._widgets[NAME_FIELD]
        widget.setFocus()
        widget.selectAll()

    def _commit_name(self) -> None:
        if self._row < 0:
            return
        widget = self._widgets[NAME_FIELD]
        if self._model.rename_row(self._row, widget.text()):
            self._set_invalid(widget, False)
            self.rowRenamed.emit(self._row)

    def _on_invalid(self, _message: str) -> None:
        self._reload_name()
        self._set_invalid(self._widgets[NAME_FIELD], True)

    def _reload_name(self) -> None:
        widget = self._widgets[NAME_FIELD]
        if self._row < 0:
            widget.clear()
            return
        widget.blockSignals(True)
        widget.setText(self._model.name_of(self._row))
        widget.blockSignals(False)
        self._set_invalid(widget, False)

    def _set_invalid(self, widget: QWidget, invalid: bool) -> None:
        widget.setProperty("invalid", invalid)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    @staticmethod
    def _clear_widget(widget: QWidget) -> None:
        widget.blockSignals(True)
        if isinstance(widget, (QComboBox, theme.CheckBox, theme.SpinBox)):
            widget.clear_value()
        else:
            widget.clear()
        widget.blockSignals(False)
