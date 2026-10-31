import csv
import os
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QFrame, QLabel, QLineEdit, QScrollArea,
                               QVBoxLayout, QWidget)

import theme
from bo3_paths import tools_path

TABLE_FOLDER = os.path.join("gamedata", "weapons", "common")
MAPPINGS = "attachmentmappingsTable.csv"
DEFINITIONS = "attachmentTable.csv"
MAX_ATTACHMENTS = 6
SLOTS = ("Optics", "Barrel", "Underbarrel", "Magazine", "Rig", "Perks", "Other")
RIG_POINTS = {"muzzle": "Barrel", "bottom": "Underbarrel", "trigger": "Magazine",
              "gunperk": "Perks"}

_cache: Dict[str, Tuple[float, List[List[str]]]] = {}


def map_root(csv_path: Optional[str]) -> Optional[str]:
    if not csv_path:
        return None
    current = os.path.dirname(os.path.abspath(csv_path))
    while True:
        parent = os.path.dirname(current)
        if parent == current:
            return None
        if os.path.basename(parent).lower() == "usermaps":
            return current
        current = parent


def table_path(name: str, csv_path: Optional[str]) -> Optional[str]:
    candidates = []
    root = map_root(csv_path)
    if root:
        candidates.append(os.path.join(root, TABLE_FOLDER, name))
    tools = tools_path()
    if tools:
        candidates.append(os.path.join(tools, "share", "raw", TABLE_FOLDER, name))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _rows(path: str) -> List[List[str]]:
    stamp = os.path.getmtime(path)
    cached = _cache.get(path)
    if cached and cached[0] == stamp:
        return cached[1]
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as fh:
        rows = list(csv.reader(fh))
    _cache[path] = (stamp, rows)
    return rows


def load_mappings(path: str) -> Dict[str, List[str]]:
    found = {}
    for row in _rows(path):
        if len(row) < 2 or not row[0].strip() or row[0].startswith("#") \
                or row[0].strip() == "a0":
            continue
        found[row[0].strip()] = row[1].split()
    return found


def load_slots(path: str) -> Dict[str, str]:
    slots = {}
    for row in _rows(path):
        if len(row) < 5 or not row[0].strip().isdigit():
            continue
        point, group, reference = row[1].strip(), row[2].strip(), row[4].strip()
        if group == "optic":
            slots[reference] = "Optics"
        elif group == "mod":
            slots[reference] = ""
        elif group == "rig":
            slots[reference] = RIG_POINTS.get(point, "Rig")
    return slots


def slot_of(name: str, slots: Dict[str, str]) -> str:
    if name in slots:
        return slots[name]
    base = max((ref for ref in slots if name.startswith(ref + "_")),
               key=len, default=None)
    return slots[base] if base else "Other"


def choices(weapon: str, csv_path: Optional[str]):
    mappings_path = table_path(MAPPINGS, csv_path)
    definitions_path = table_path(DEFINITIONS, csv_path)
    if not mappings_path and not definitions_path:
        return None
    slots = load_slots(definitions_path) if definitions_path else {}
    mapping = load_mappings(mappings_path) if mappings_path else {}
    listed = weapon.strip() in mapping
    names = mapping[weapon.strip()] if listed else list(slots)
    grouped: Dict[str, List[str]] = {slot: [] for slot in SLOTS}
    for name in names:
        slot = slot_of(name, slots)
        if not slot:
            continue
        bucket = grouped[slot]
        if name not in bucket:
            bucket.append(name)
    for bucket in grouped.values():
        bucket.sort()
    return grouped, listed


class AttachmentPicker(QFrame):

    changed = Signal(str)

    def __init__(self, weapon: str, grouped: Dict[str, List[str]], listed: bool,
                 current: str, parent=None) -> None:
        super().__init__(parent, Qt.Popup)
        self.setObjectName("Picker")
        self._selected = current.split()
        self._boxes: Dict[str, theme.CheckBox] = {}

        known = {name for names in grouped.values() for name in names}
        extra = [name for name in self._selected
                 if name not in known and not name.startswith("gmod")]
        if extra:
            grouped = dict(grouped)
            grouped["Other"] = sorted(set(grouped["Other"]) | set(extra))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        note = QLabel(("Attachments %s accepts" % weapon) if listed else
                      ("%s isn't in the attachment mapping table,\n"
                       "so every attachment is listed" % (weapon or "This weapon")))
        note.setObjectName("MutedLabel")
        layout.addWidget(note)

        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter…")
        self._filter.textChanged.connect(self._apply_filter)
        layout.addWidget(self._filter)

        body = QWidget()
        rows = QVBoxLayout(body)
        rows.setContentsMargins(0, 0, 6, 0)
        rows.setSpacing(2)
        self._sections: List[Tuple[QLabel, List[theme.CheckBox]]] = []
        for slot in SLOTS:
            names = grouped.get(slot, [])
            if not names:
                continue
            heading = QLabel(slot)
            heading.setObjectName("FieldLabel")
            rows.addWidget(heading)
            boxes = []
            for name in names:
                box = theme.CheckBox(name)
                box.setMinimumHeight(24)
                box.setChecked(name in self._selected)
                box.clicked.connect(lambda checked, n=name: self._toggle(n, checked))
                rows.addWidget(box)
                self._boxes[name] = box
                boxes.append(box)
            self._sections.append((heading, boxes))
        rows.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidget(body)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(scroll, 1)

        self._count = QLabel("")
        self._count.setObjectName("MutedLabel")
        layout.addWidget(self._count)
        self._refresh()

    def _toggle(self, name: str, checked: bool) -> None:
        if checked and name not in self._selected:
            self._selected.append(name)
        elif not checked and name in self._selected:
            self._selected.remove(name)
        self._refresh()
        self.changed.emit(" ".join(self._selected))

    def _refresh(self) -> None:
        full = len(self._selected) >= MAX_ATTACHMENTS
        for name, box in self._boxes.items():
            box.setEnabled(name in self._selected or not full)
        self._count.setText("%d of %d chosen%s" % (
            len(self._selected), MAX_ATTACHMENTS,
            " - untick one to pick another" if full else ""))

    def _apply_filter(self, text: str) -> None:
        text = text.strip().lower()
        for heading, boxes in self._sections:
            shown = 0
            for box in boxes:
                visible = not text or text in box.text().lower()
                box.setVisible(visible)
                shown += visible
            heading.setVisible(shown > 0)

    def show_below(self, anchor: QWidget) -> None:
        width = 300
        height = 440
        corner = anchor.mapToGlobal(QPoint(anchor.width() - width, anchor.height() + 2))
        rect = QRect(corner.x(), corner.y(), width, height)
        screen = (QGuiApplication.screenAt(anchor.mapToGlobal(anchor.rect().center()))
                  or anchor.screen()).availableGeometry()
        if rect.bottom() > screen.bottom():
            rect.moveBottom(anchor.mapToGlobal(QPoint(0, -2)).y())
        if rect.left() < screen.left():
            rect.moveLeft(screen.left())
        self.setGeometry(rect)
        self.show()
        self._filter.setFocus()
