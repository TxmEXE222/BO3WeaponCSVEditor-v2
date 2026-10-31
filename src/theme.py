from PySide6.QtCore import Property, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QCheckBox, QComboBox, QSpinBox

BG = "#18181b"
BG_ELEVATED = "#222226"
BG_BAR = "#27272a"
SURFACE = "#2f2f35"
SURFACE_HOVER = "#3a3a42"
BORDER = "#3f3f48"
ACCENT = "#0ea5e9"
FG = "#f4f4f5"
FG_MUTED = "#71717a"
FG_LABEL = "#a1a1aa"

BTN = "#3f3f46"
BTN_HOVER = "#52525b"
BTN_ACTIVE = "#35353b"
BTN_PRIMARY = "#0284c7"
BTN_PRIMARY_HOVER = "#0ea5e9"
BTN_PRIMARY_ACTIVE = "#0369a1"

ROW_STRIPE = "#1f1f23"
ROW_CHANGED = "#422006"
ROW_CHANGED_FG = "#fcd34d"

PREVIEW_BG = "#141417"
PREVIEW_GUTTER_BG = "#1c1c21"
PREVIEW_SELECT = "#1e3a5f"

FONT = "Segoe UI"
MONO_FONT = "Cascadia Code"

QSS = f"""
QWidget {{
    background: {BG};
    color: {FG};
    font-family: "{FONT}";
    font-size: 9pt;
}}
QMainWindow, QDialog {{ background: {BG}; }}

QMenuBar {{ background: {BG_BAR}; padding: 2px; }}
QMenuBar::item {{ padding: 5px 10px; background: transparent; border-radius: 4px; }}
QMenuBar::item:selected {{ background: {SURFACE}; }}
QMenu {{ background: {BG_BAR}; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background: {ACCENT}; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}
QToolButton#GithubButton {{
    background: transparent;
    border: none;
    padding: 2px 10px 2px 6px;
}}
QToolButton#GithubButton:hover {{ background: {SURFACE}; border-radius: 4px; }}

QLabel {{ background: transparent; }}
QLabel#FieldLabel {{ color: {FG_LABEL}; font-weight: bold; }}
QLabel#TitleLabel {{ color: {FG}; font-size: 11pt; font-weight: bold; }}
QLabel#MutedLabel {{ color: {FG_MUTED}; }}
QLabel#AccentDot {{ color: {ACCENT}; font-size: 11pt; }}
QLabel#Credit {{ color: {FG_MUTED}; }}

QFrame#Card {{
    background: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#Bar {{ background: {BG_BAR}; border: none; }}
QFrame#Divider {{ background: {BORDER}; border: none; }}

QLineEdit, QComboBox, QSpinBox, QPlainTextEdit {{
    background: {SURFACE};
    color: {FG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{ color: {FG_MUTED}; background: {BG_ELEVATED}; }}
QLineEdit[readOnly="true"] {{ background: {BG_ELEVATED}; color: {FG_LABEL}; }}
QLineEdit[invalid="true"] {{ border: 1px solid #ef4444; }}

QComboBox {{ padding-right: 24px; }}
QSpinBox {{ padding: 4px 24px 3px 8px; }}
QSpinBox::up-button, QSpinBox::down-button {{
    subcontrol-origin: border;
    width: 22px;
    background: transparent;
    border: none;
    border-left: 1px solid {BORDER};
}}
QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 6px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 6px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {SURFACE_HOVER}; }}
QSpinBox::up-arrow, QSpinBox::down-arrow {{ image: none; width: 0px; height: 0px; }}

QToolButton#PickerButton {{
    background: {SURFACE};
    color: {FG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 5px 12px 4px 12px;
}}
QToolButton#PickerButton:hover {{ background: {SURFACE_HOVER}; }}
QToolButton#PickerButton:disabled {{ color: {FG_MUTED}; background: {BG_ELEVATED}; }}
QFrame#Picker {{ background: {BG_BAR}; border: 1px solid {BORDER}; border-radius: 6px; }}
QFrame#Picker QWidget {{ background: {BG_BAR}; }}
QFrame#Picker QLineEdit {{ background: {SURFACE}; }}
QFrame#Picker QScrollArea {{ border: none; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    background: transparent;
    border-left: 1px solid {BORDER};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}
QComboBox::drop-down:hover {{ background: {SURFACE_HOVER}; }}
QComboBox::drop-down:disabled {{ border-left-color: {BG_ELEVATED}; }}

QComboBox QAbstractItemView {{
    background: {BG_BAR};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    min-height: 22px;
    padding: 2px 8px;
    border-radius: 4px;
    color: {FG};
}}
QComboBox QAbstractItemView::item:hover {{ background: {SURFACE_HOVER}; }}
QComboBox QAbstractItemView::item:selected {{
    background: {ACCENT};
    color: {FG};
}}

QPushButton {{
    background: {BTN};
    color: {FG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 7px 14px;
}}
QPushButton:hover {{ background: {BTN_HOVER}; }}
QPushButton:pressed {{ background: {BTN_ACTIVE}; }}
QPushButton:disabled {{ color: {FG_MUTED}; background: {BG_ELEVATED}; }}
QPushButton#Primary {{ background: {BTN_PRIMARY}; border: 1px solid {BTN_PRIMARY}; }}
QPushButton#Primary:hover {{ background: {BTN_PRIMARY_HOVER}; }}
QPushButton#Primary:pressed {{ background: {BTN_PRIMARY_ACTIVE}; }}

QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 8px; top: -1px; }}
QTabBar::tab {{
    background: {BG_BAR};
    color: {FG_LABEL};
    padding: 8px 20px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top: 2px solid {BG_BAR};
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {BG_ELEVATED};
    color: {ACCENT};
    border-top: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{ background: {SURFACE}; color: {FG}; }}

QTableView {{
    background: {BG_ELEVATED};
    alternate-background-color: {ROW_STRIPE};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 8px;
    selection-background-color: {ACCENT};
    selection-color: {FG};
    outline: none;
}}
QTableView::item {{ padding: 3px 6px; }}
QTableView QLineEdit, QTableView QComboBox, QTableView QSpinBox {{
    padding: 0px 5px;
    border: 1px solid {ACCENT};
    border-radius: 0px;
    background: {SURFACE};
    color: {FG};
    selection-background-color: {ACCENT};
    selection-color: {FG};
}}
QTableView QComboBox::drop-down {{ border-left: 1px solid {BORDER}; }}
QTableView::item:focus {{ border: none; }}
QHeaderView {{ background: {BG_BAR}; }}
QHeaderView::section {{
    background: {BG_BAR};
    color: {FG_LABEL};
    padding: 6px 8px;
    border: none;
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    font-weight: bold;
}}
QHeaderView::section:hover {{ background: {SURFACE}; }}
QTableCornerButton::section {{ background: {BG_BAR}; border: none; }}

QScrollBar:vertical {{ background: {BG}; width: 12px; margin: 0; }}
QScrollBar:horizontal {{ background: {BG}; height: 12px; margin: 0; }}
QScrollBar::handle {{ background: {SURFACE}; border-radius: 6px; min-height: 28px; min-width: 28px; }}
QScrollBar::handle:hover {{ background: {SURFACE_HOVER}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QStatusBar {{ background: {BG_BAR}; color: {FG_MUTED}; }}
QStatusBar::item {{ border: none; }}
QCheckBox {{ font-weight: bold; background: transparent; }}
QToolTip {{
    background: {BG_BAR};
    color: {FG};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 1px 3px;
    font-size: 8pt;
}}
"""


def tooltip(body: str = "", title: str = "", hint: str = "") -> str:
    parts = ['<div style="white-space:nowrap">']
    if title:
        parts.append('<span style="color:%s"><b>%s</b></span>' % (ACCENT, title))
        if body or hint:
            parts.append("<br>")
    if body:
        parts.append('<span style="color:%s">%s</span>'
                     % (FG, body.replace("\n", "<br>")))
        if hint:
            parts.append("<br>")
    if hint:
        parts.append('<span style="color:%s">%s</span>' % (FG_MUTED, hint))
    parts.append("</div>")
    return "".join(parts)


class ChevronComboBox(QComboBox):

    ARROW_BOX = 22

    valueChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.currentTextChanged.connect(self._emit_value)

    def _emit_value(self, *_args) -> None:
        self.valueChanged.emit(self._get_value())

    def _get_value(self) -> str:
        if not self.isEditable() and self.currentIndex() < 0:
            return ""
        return self.currentText()

    def _set_value(self, text) -> None:
        text = "" if text is None else str(text)
        index = self.findText(text)
        if index < 0 and text and not self.isEditable():
            self.addItem(text)
            index = self.count() - 1
        self.setCurrentIndex(index)
        if self.isEditable():
            self.setCurrentText(text)

    value = Property(str, _get_value, _set_value, notify=valueChanged)

    def clear_value(self) -> None:
        if self.isEditable():
            self.setCurrentText("")
        else:
            self.setCurrentIndex(-1)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)

        if not self.isEnabled():
            color = QColor(FG_MUTED)
        elif self.underMouse():
            color = QColor(ACCENT)
        else:
            color = QColor(FG_LABEL)

        box = QRect(self.width() - self.ARROW_BOX, 0,
                    self.ARROW_BOX, self.height())
        painter = QPainter(self)
        draw_chevron(painter, box.center().x() + 0.5, box.center().y() + 0.5,
                     self.view().isVisible(), color)

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self.update()

    def wheelEvent(self, event) -> None:
        event.ignore()

    def showPopup(self) -> None:
        super().showPopup()
        self._fit_popup_to_items()
        self.update()

    def _fit_popup_to_items(self) -> None:
        view = self.view()
        popup = view.window()
        needed = (view.sizeHintForColumn(0)
                  + popup.width() - view.viewport().width())
        if needed <= popup.width():
            return
        rect = popup.geometry()
        rect.setWidth(needed)
        screen = (QGuiApplication.screenAt(self.mapToGlobal(self.rect().center()))
                  or self.screen()).availableGeometry()
        if rect.right() > screen.right():
            rect.moveRight(screen.right())
        popup.setGeometry(rect)

    def hidePopup(self) -> None:
        super().hidePopup()
        self.update()


def draw_chevron(painter, cx: float, cy: float, up: bool, color: QColor) -> None:
    path = QPainterPath()
    if up:
        path.moveTo(cx - 4.0, cy + 2.0)
        path.lineTo(cx, cy - 2.5)
        path.lineTo(cx + 4.0, cy + 2.0)
    else:
        path.moveTo(cx - 4.0, cy - 2.0)
        path.lineTo(cx, cy + 2.5)
        path.lineTo(cx + 4.0, cy - 2.0)
    pen = QPen(color, 1.6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(path)
    painter.restore()


class SpinBox(QSpinBox):

    BLANK = -1
    LIMIT = 8
    ARROW_BOX = 22

    rawChanged = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._raw = ""
        self._quiet = False
        self.setRange(self.BLANK, self.LIMIT)
        self.setSpecialValueText("–")
        self.valueChanged.connect(self._on_changed)

    def _on_changed(self, number: int) -> None:
        if self._quiet:
            return
        self._raw = "" if number == self.BLANK else str(number)
        self.rawChanged.emit(self._raw)

    def _get_raw(self) -> str:
        return self._raw

    def _set_raw(self, text) -> None:
        self._raw = "" if text is None else str(text)
        stripped = self._raw.strip()
        number = int(stripped) if stripped.isdigit() else self.BLANK
        self._quiet = True
        self.setMaximum(max(self.LIMIT, number))
        self.setValue(number)
        self._quiet = False

    raw = Property(str, _get_raw, _set_raw, notify=rawChanged)

    def clear_value(self) -> None:
        self._set_raw("")

    def wheelEvent(self, event) -> None:
        event.ignore()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self.isEnabled():
            color = QColor(FG_MUTED)
        elif self.underMouse():
            color = QColor(ACCENT)
        else:
            color = QColor(FG_LABEL)
        cx = self.width() - self.ARROW_BOX / 2 + 0.5
        painter = QPainter(self)
        draw_chevron(painter, cx, self.height() * 0.25 + 1, True, color)
        draw_chevron(painter, cx, self.height() * 0.75 - 1, False, color)

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self.update()


def draw_check(painter, box: QRectF, checked: bool, enabled: bool = True,
               hot: bool = False, selected: bool = False) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    if checked and enabled:
        painter.setPen(QPen(QColor(FG if selected else ACCENT), 1))
        painter.setBrush(QColor(ACCENT))
    else:
        painter.setPen(QPen(QColor(FG if selected else ACCENT if hot else BORDER), 1))
        painter.setBrush(QColor(SURFACE if enabled else BG_ELEVATED))
    painter.drawRoundedRect(box, 4, 4)

    if checked:
        tick = QPainterPath()
        tick.moveTo(box.left() + 4, box.center().y() + 0.5)
        tick.lineTo(box.left() + 7, box.bottom() - 4.5)
        tick.lineTo(box.right() - 3.5, box.top() + 4.5)
        pen = QPen(QColor(FG if enabled else FG_MUTED), 2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(tick)
    painter.restore()


class CheckBox(QCheckBox):

    BOX = 16
    GAP = 8

    valueChanged = Signal(str)

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self._raw = ""
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, checked: bool) -> None:
        self._raw = "TRUE" if checked else "FALSE"
        self.valueChanged.emit(self._raw)

    def _get_value(self) -> str:
        return self._raw

    def _set_value(self, text) -> None:
        self._raw = "" if text is None else str(text)
        self.setChecked(self._raw.strip().lower() == "true")

    value = Property(str, _get_value, _set_value, notify=valueChanged)

    def clear_value(self) -> None:
        self._set_value("")

    def sizeHint(self) -> QSize:
        metrics = self.fontMetrics()
        return QSize(self.BOX + self.GAP + metrics.horizontalAdvance(self.text()) + 4,
                     max(self.BOX + 4, metrics.height()))

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, event) -> None:
        enabled = self.isEnabled()
        box = QRectF(0.5, (self.height() - self.BOX) / 2 + 0.5, self.BOX, self.BOX)

        painter = QPainter(self)
        draw_check(painter, box, self.isChecked(), enabled,
                   enabled and (self.underMouse() or self.hasFocus()))

        painter.setPen(QColor(FG_LABEL if enabled else FG_MUTED))
        text_left = self.BOX + self.GAP
        painter.drawText(QRectF(text_left, 0, self.width() - text_left, self.height()),
                         Qt.AlignVCenter | Qt.AlignLeft, self.text())

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self.update()
