import os
from typing import Optional

from PySide6.QtCore import (QItemSelectionModel, QModelIndex, QSize,
                            QStandardPaths, Qt, QUrl, Signal)
from PySide6.QtGui import (QAction, QColor, QDesktopServices, QIcon, QImage,
                           QKeySequence, QPalette, QPixmap)
from PySide6.QtWidgets import (QAbstractItemDelegate, QAbstractItemView,
                               QFileDialog, QFrame, QHBoxLayout,
                               QHeaderView, QInputDialog, QLabel, QLineEdit,
                               QListView, QMainWindow, QMessageBox, QPushButton,
                               QSplitter, QStackedWidget, QTableView, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

import theme
from bo3_paths import find_usermaps, list_usermaps
from delegates import CellEditorDelegate, CheckDelegate, SectionBreakDelegate
from fields import COMBO_TYPES, FIELD_TYPES
from form_panel import FormPanel
from models import WeaponFilterProxy, WeaponTableModel
from preview import PreviewView
from weapon_csv import NAME_FIELD

APP_NAME = "BO3 Weapon CSV Editor"
VERSION = "2.0"
CREDIT = "BO3 Weapon CSV Editor By TxmEXE222 - Inspired by WeaponCSV (MakeCentsGaming)"
GITHUB_URL = "https://github.com/TxmEXE222"
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

TAB_EDITOR, TAB_PREVIEW = 0, 2
ROW_HEIGHT = 26


class UsermapPicker(theme.ChevronComboBox):

    # Signals
    aboutToShowPopup = Signal()

    # Navigation
    OPEN_KEYS = (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown,
                 Qt.Key_Home, Qt.Key_End)

    # Refresh
    def showPopup(self) -> None:
        self.aboutToShowPopup.emit()
        super().showPopup()

    def keyPressEvent(self, event) -> None:
        if event.key() in self.OPEN_KEYS or event.text().strip():
            self.showPopup()
            return
        super().keyPressEvent(event)


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1080, 720)
        self.setAcceptDrops(True)

        icon_path = os.path.join(ASSET_DIR, "CSVEdit.ico")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._editing_preview = False
        self._undo_buttons = []
        self._redo_buttons = []
        self._sized_headers = ()
        self._rows_have_gaps = False
        self._last_dir: Optional[str] = None

        self.model = WeaponTableModel(self)
        self.proxy = WeaponFilterProxy(self)
        self.proxy.setSourceModel(self.model)

        self._build_ui()
        self._build_menu()
        self._build_github_button()
        self._connect()
        self._refresh_maps()
        self._update_actions()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 6)
        layout.setSpacing(8)
        layout.addWidget(self._build_topbar())

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_editor_tab(), "Editor")
        self.tabs.addTab(self._build_sheet_tab(), "Spreadsheet")
        self.tabs.addTab(self._build_preview_tab(), "Preview")
        layout.addWidget(self.tabs, 1)

        self.setCentralWidget(central)

        self.status_label = QLabel("No file open")
        self.dirty_label = QLabel("")
        self.dirty_label.setObjectName("MutedLabel")
        self.statusBar().addWidget(self.status_label, 1)
        self.statusBar().addPermanentWidget(self.dirty_label)

    def _build_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("Bar")
        rows = QVBoxLayout(bar)
        rows.setContentsMargins(4, 2, 4, 6)
        rows.setSpacing(4)
        row = QHBoxLayout()
        row.setSpacing(8)
        rows.addLayout(row)

        dot = QLabel("●")
        dot.setObjectName("AccentDot")
        title = QLabel(APP_NAME)
        title.setObjectName("TitleLabel")
        row.addWidget(dot)
        row.addWidget(title)

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("No file open")
        row.addWidget(self.path_edit, 1)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search weapons…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setFixedWidth(220)
        self.search_edit.setToolTip(theme.tooltip(
            "Filter the weapon list and the grid by any column"))
        row.addWidget(self.search_edit)

        version = QLabel("Release v" + VERSION)
        version.setObjectName("MutedLabel")
        row.addWidget(version)

        self.open_btn = QPushButton("Open")
        self.open_btn.setObjectName("Primary")
        self.open_btn.setToolTip(theme.tooltip("Open a weapon .csv", hint="Ctrl+O"))
        row.addWidget(self.open_btn)

        self.path_edit.setToolTip(theme.tooltip("Path of the file being edited"))

        maps_row = QHBoxLayout()
        maps_row.setSpacing(8)
        maps_row.addStretch(1)
        maps_label = QLabel("usermaps:")
        maps_label.setObjectName("MutedLabel")
        maps_row.addWidget(maps_label)
        self.map_combo = UsermapPicker()
        self.map_combo.setFixedWidth(220)
        self.map_combo.setPlaceholderText("Choose a map…")
        self.map_combo.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.map_combo.setMaxVisibleItems(15)
        self.map_combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        maps_row.addWidget(self.map_combo)
        rows.addLayout(maps_row)
        return bar

    def _build_editor_tab(self) -> QWidget:
        self.editor_stack = QStackedWidget()
        self.editor_stack.addWidget(self._build_empty_state())

        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        split = QSplitter(Qt.Horizontal)

        self.weapon_list = QListView()
        self.weapon_list.setModel(self.proxy)
        self.weapon_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.weapon_list.setMinimumWidth(180)
        self.weapon_list.setItemDelegate(
            SectionBreakDelegate(self.model, self.proxy, self))
        split.addWidget(self.weapon_list)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self.form = FormPanel(self.model)
        right_layout.addWidget(self.form, 1)

        self.row_label = QLabel("")
        self.row_label.setObjectName("MutedLabel")
        right_layout.addWidget(self.row_label)

        split.addWidget(right)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([220, 820])
        outer.addWidget(split, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(6)
        self.add_btn = QPushButton("Add Weapon")
        self.add_btn.setToolTip(theme.tooltip(
            "Append a blank weapon row", hint="Ctrl+N"))
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setToolTip(theme.tooltip(
            "Duplicate this weapon under a new name", hint="Ctrl+D"))
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setToolTip(theme.tooltip(
            "Remove this weapon from the file", hint="Ctrl+Del"))
        self.comment_btn = QPushButton("Comment Out")
        self.break_btn = QPushButton("Section Break")
        self.undo_btn, self.redo_btn = self._history_buttons()
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("Primary")
        self.save_btn.setToolTip(theme.tooltip(
            "Write the file back to disk", hint="Ctrl+S"))
        for btn in (self.add_btn, self.copy_btn, self.delete_btn,
                    self.comment_btn, self.break_btn,
                    self.undo_btn, self.redo_btn):
            buttons.addWidget(btn)
        buttons.addStretch(1)
        buttons.addWidget(self.save_btn)
        outer.addLayout(buttons)

        credit = QLabel(CREDIT)
        credit.setObjectName("Credit")
        credit.setAlignment(Qt.AlignCenter)
        outer.addWidget(credit)

        self.editor_stack.addWidget(page)
        return self.editor_stack

    @staticmethod
    def _make_scrolling_smooth(view, base: str) -> None:
        view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        palette = view.palette()
        palette.setColor(QPalette.Base, QColor(base))
        palette.setColor(QPalette.AlternateBase, QColor(theme.ROW_STRIPE))
        palette.setColor(QPalette.Text, QColor(theme.FG))
        palette.setColor(QPalette.Highlight, QColor(theme.ACCENT))
        palette.setColor(QPalette.HighlightedText, QColor(theme.FG))
        view.setPalette(palette)
        view.viewport().setPalette(palette)
        view.viewport().setAutoFillBackground(True)

    def _history_buttons(self):
        undo = QPushButton("Undo")
        undo.clicked.connect(self.undo)
        redo = QPushButton("Redo")
        redo.clicked.connect(self.redo)
        self._undo_buttons.append(undo)
        self._redo_buttons.append(redo)
        return undo, redo

    def _build_empty_state(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addStretch(1)

        image = QLabel()
        image.setAlignment(Qt.AlignCenter)
        drop_png = os.path.join(ASSET_DIR, "dragdrop.png")
        if os.path.isfile(drop_png):
            pixmap = QPixmap(drop_png)
            if not pixmap.isNull():
                image.setPixmap(pixmap.scaledToHeight(
                    140, Qt.SmoothTransformation))
        layout.addWidget(image)

        text = QLabel("Drag and drop your .csv here, or press Ctrl+O")
        text.setObjectName("MutedLabel")
        text.setAlignment(Qt.AlignCenter)
        layout.addWidget(text)
        layout.addStretch(1)

        credit = QLabel(CREDIT)
        credit.setObjectName("Credit")
        credit.setAlignment(Qt.AlignCenter)
        layout.addWidget(credit)
        return page

    def _build_sheet_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked
                                   | QAbstractItemView.SelectedClicked
                                   | QAbstractItemView.EditKeyPressed
                                   | QAbstractItemView.AnyKeyPressed)
        self.sheet_delegate = SectionBreakDelegate(self.model, self.proxy, self)
        self.plain_delegate = CellEditorDelegate(
            self.model, self.proxy, self)
        self.check_delegate = CheckDelegate(self.model, self.proxy, self)
        self._check_cols = []
        self.table.setItemDelegate(self.plain_delegate)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        if hasattr(header, "setSortIndicatorClearable"):
            header.setSortIndicatorClearable(True)
        header.setSortIndicator(-1, Qt.AscendingOrder)
        self.proxy.sort(-1)
        layout.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(6)
        self.sheet_undo_btn, self.sheet_redo_btn = self._history_buttons()
        bottom.addWidget(self.sheet_undo_btn)
        bottom.addWidget(self.sheet_redo_btn)
        bottom.addStretch(1)

        hint = QLabel("Double-click a cell to edit it. Sorting changes this view "
                      "only, row order in the saved file is untouched.")
        hint.setObjectName("MutedLabel")
        bottom.addWidget(hint)
        layout.addLayout(bottom)
        return page

    def _build_preview_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        head = QHBoxLayout()
        title = QLabel("CSV Preview")
        title.setObjectName("FieldLabel")
        muted = QLabel("Edit the CSV directly")
        muted.setObjectName("MutedLabel")
        self.preview_status = QLabel("")
        self.preview_status.setStyleSheet("color: " + theme.ACCENT + ";")
        head.addWidget(title)
        head.addWidget(muted)
        head.addStretch(1)
        head.addWidget(self.preview_status)
        undo, redo = self._history_buttons()
        head.addWidget(undo)
        head.addWidget(redo)
        self.preview_save_btn = QPushButton("Save")
        self.preview_save_btn.setObjectName("Primary")
        self.preview_save_btn.setToolTip(theme.tooltip(
            "Save the CSV", hint="Ctrl+S"))
        self.preview_save_btn.clicked.connect(self.save_file)
        head.addWidget(self.preview_save_btn)
        layout.addLayout(head)

        self.preview = PreviewView()
        self.preview.textChanged.connect(self._on_preview_edited)
        layout.addWidget(self.preview, 1)
        return page

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        self.act_open = QAction("&Open…", self, shortcut=QKeySequence.Open,
                                triggered=self.open_file)
        self.act_save = QAction("&Save", self, shortcut=QKeySequence.Save,
                                triggered=self.save_file)
        self.act_save_as = QAction("Save &As…", self,
                                   shortcut=QKeySequence.SaveAs,
                                   triggered=self.save_file_as)
        act_exit = QAction("E&xit", self, shortcut=QKeySequence.Quit,
                           triggered=self.close)
        for action in (self.act_open, self.act_save, self.act_save_as):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction(act_exit)

        edit_menu = self.menuBar().addMenu("&Edit")
        self.act_undo = QAction("&Undo", self, shortcut=QKeySequence.Undo,
                                triggered=self.undo)
        self.act_redo = QAction("&Redo", self, shortcut=QKeySequence.Redo,
                                triggered=self.redo)
        self.act_redo_alt = QAction(self, shortcut="Ctrl+Shift+Z",
                                    triggered=self.redo)
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)
        edit_menu.addSeparator()
        self.addActions([self.act_undo, self.act_redo, self.act_redo_alt])
        self.act_add = QAction("&Add Weapon", self, shortcut="Ctrl+N",
                               triggered=self.add_row)
        self.act_copy = QAction("&Copy Weapon…", self, shortcut="Ctrl+D",
                                triggered=self.copy_row)
        self.act_delete = QAction("&Delete Weapon", self, shortcut="Ctrl+Del",
                                  triggered=self.delete_row)
        self.act_comment = QAction("Toggle Comment &Out", self, shortcut="Ctrl+/",
                                   triggered=self.toggle_comment)
        self.act_break = QAction("Insert Section &Break Above", self,
                                 shortcut="Ctrl+B", triggered=self.insert_break)
        for action in (self.act_add, self.act_copy, self.act_delete,
                       self.act_comment, self.act_break):
            edit_menu.addAction(action)
        self.addActions([self.act_add, self.act_copy, self.act_delete,
                         self.act_comment, self.act_break])

    # Logo
    @staticmethod
    def _github_mark(colour: str, size: int = 18) -> QPixmap:
        source = QImage(os.path.join(ASSET_DIR, "github.png"))
        if source.isNull():
            return QPixmap()
        source = source.scaled(size * 2, size * 2, Qt.KeepAspectRatio,
                               Qt.SmoothTransformation)
        mark = QImage(source.size(), QImage.Format_ARGB32_Premultiplied)
        mark.fill(Qt.transparent)
        tint = QColor(colour)
        for y in range(source.height()):
            for x in range(source.width()):
                pixel = source.pixelColor(x, y)
                if pixel.alpha() > 100 and pixel.value() < 110:
                    mark.setPixelColor(x, y, QColor(
                        tint.red(), tint.green(), tint.blue(), pixel.alpha()))
        pixmap = QPixmap.fromImage(mark)
        pixmap.setDevicePixelRatio(2.0)
        return pixmap

    def _build_github_button(self) -> None:
        normal = self._github_mark(theme.FG_LABEL)
        if normal.isNull():
            return
        icon = QIcon(normal)
        icon.addPixmap(self._github_mark(theme.ACCENT), QIcon.Active)

        button = QToolButton()
        button.setObjectName("GithubButton")
        button.setIcon(icon)
        button.setIconSize(QSize(18, 18))
        button.setAutoRaise(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip(theme.tooltip("Open TxmEXE222's Github",
                                        title="TxmEXE222"))
        button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        self.menuBar().setCornerWidget(button, Qt.TopRightCorner)
        self.github_btn = button

    # Signals
    def _connect(self) -> None:
        self.open_btn.clicked.connect(self.open_file)
        self.map_combo.aboutToShowPopup.connect(self._refresh_maps)
        self.map_combo.activated.connect(self._open_map)
        self.save_btn.clicked.connect(self.save_file)
        self.add_btn.clicked.connect(self.add_row)
        self.copy_btn.clicked.connect(self.copy_row)
        self.delete_btn.clicked.connect(self.delete_row)
        self.comment_btn.clicked.connect(self.toggle_comment)
        self.break_btn.clicked.connect(self.insert_break)

        self.search_edit.textChanged.connect(self.proxy.set_query)
        self.search_edit.textChanged.connect(lambda _t: self._relayout_rows())
        self.proxy.layoutChanged.connect(self._relayout_rows)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.weapon_list.setSelectionModel(self.table.selectionModel())
        selection = self.table.selectionModel()
        selection.currentRowChanged.connect(self._on_current_changed)

        self.model.modelReset.connect(self._on_model_reset)
        self.model.dirtyChanged.connect(self._on_dirty_changed)
        self.model.validationFailed.connect(self._on_validation_failed)
        self.model.loadWarning.connect(self._on_load_warning)
        self.model.historyChanged.connect(self._update_history_actions)
        self.model.dataChanged.connect(lambda *_a: self._on_model_touched())
        self.model.structureChanged.connect(self._on_model_touched)
        self.model.structureChanged.connect(self._relayout_rows)
        self.model.rowsInserted.connect(lambda *_a: self._on_model_touched())
        self.model.rowsRemoved.connect(lambda *_a: self._on_model_touched())
        self.form.rowRenamed.connect(lambda _r: self._update_row_label())

    def open_file(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open level_common_weapon.csv", self._open_dir(),
            "CSV files (*.csv);;All files (*.*)")
        if path:
            self.load_file(path)

    def _refresh_maps(self) -> None:
        combo = self.map_combo
        usermaps = find_usermaps()
        combo.blockSignals(True)
        combo.clear()
        if usermaps is None:
            combo.setEnabled(False)
            combo.setToolTip(theme.tooltip(
                "Set up the BO3 mod tools to list your maps here",
                title="usermaps not found"))
        else:
            combo.setEnabled(True)
            combo.setToolTip(theme.tooltip(
                "Open a map's weapons CSV", hint=usermaps))
            for name, tables in list_usermaps(usermaps):
                if not tables:
                    combo.addItem(name, "")
                for table in tables:
                    label = name
                    if len(tables) > 1:
                        label += " (" + os.path.basename(table) + ")"
                    combo.addItem(label, table)
        combo.blockSignals(False)
        self._sync_map_combo()

    def _is_open(self, path: str) -> bool:
        if not path or not self.model.path:
            return False
        return (os.path.normcase(os.path.abspath(path))
                == os.path.normcase(os.path.abspath(self.model.path)))

    def _sync_map_combo(self) -> None:
        index = -1
        for i in range(self.map_combo.count()):
            if self._is_open(self.map_combo.itemData(i)):
                index = i
                break
        self.map_combo.blockSignals(True)
        self.map_combo.setCurrentIndex(index)
        self.map_combo.blockSignals(False)

    def _open_map(self, index: int) -> None:
        table = self.map_combo.itemData(index)
        if not table:
            QMessageBox.information(
                self, "No Weapons CSV",
                self.map_combo.itemText(index)
                + " has no weapons CSV in gamedata\\weapons\\zm.")
        elif not self._is_open(table) and self._confirm_discard():
            self.load_file(table)
        self._sync_map_combo()

    # Folder
    def _open_dir(self) -> str:
        if self._last_dir and os.path.isdir(self._last_dir):
            return self._last_dir
        return find_usermaps() or QStandardPaths.writableLocation(
            QStandardPaths.DocumentsLocation)

    def load_file(self, path: str) -> None:
        try:
            self.model.load(path)
        except Exception as exc:
            QMessageBox.critical(self, "Open Error", str(exc))
            return
        self._last_dir = os.path.dirname(os.path.abspath(path))
        self._sync_map_combo()
        self.path_edit.setText(path)
        self.search_edit.clear()
        self._on_dirty_changed(self.model.dirty)
        self.editor_stack.setCurrentIndex(1)
        if self.model.rowCount():
            self._select_source_row(0)
        self._update_actions()
        self._relayout_rows()
        self._refresh_preview()

# If prov3ntus is reading this, i hope you di- have a lovely day.

    def save_file(self) -> None:
        self._commit_pending()
        if not self.model.path:
            self.save_file_as()
            return
        self._write(self.model.path)

    def save_file_as(self) -> None:
        self._commit_pending()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", self.model.path or "level_common_weapon.csv",
            "CSV files (*.csv);;All files (*.*)")
        if path:
            self._write(path)

    def undo(self) -> None:
        if self.model.preview_error:
            self.model.preview_error = ""
            self.model.set_dirty(self.model.render() != self.model._baseline)
            self._refresh_preview()
            self._update_history_actions()
            return
        if not self.model.can_undo():
            return
        label = self.model.undo_label()
        self._step_history(self.model.undo(), "Undid " + label)

    def redo(self) -> None:
        if self.model.preview_error or not self.model.can_redo():
            return
        label = self.model.redo_label()
        self._step_history(self.model.redo(), "Redid " + label)

    def _step_history(self, row: Optional[int], message: str) -> None:
        if row is not None:
            self._select_source_row(row)
        self._relayout_rows()
        self._update_row_label()
        self._update_actions()
        if self.tabs.currentIndex() == TAB_PREVIEW:
            self._refresh_preview()
        self.statusBar().showMessage(message, 4000)

    def add_row(self) -> None:
        self._commit_pending()
        if not self.model.headers:
            return
        name = self._unique_name("new_weapon")
        row = self.model.add_row({NAME_FIELD: name})
        self._select_source_row(row)
        self.tabs.setCurrentIndex(TAB_EDITOR)
        self.form.focus_name()
        self.statusBar().showMessage("Added '" + name + "'", 4000)

    def copy_row(self) -> None:
        self._commit_pending()
        row = self._current_source_row()
        if row is None:
            return
        old_name = self.model.name_of(row)
        suggested = self._unique_name(old_name + "_copy")
        name, ok = QInputDialog.getText(self, "Copy Weapon", "New weapon name",
                                        QLineEdit.Normal, suggested)
        if not ok:
            return
        name = name.strip()
        if not name:
            QMessageBox.warning(self, "Invalid", "Name cannot be empty.")
            return
        if self.model.csv.find_by_name(name) is not None:
            QMessageBox.warning(self, "Duplicate", "'" + name + "' already exists.")
            return
        new_row = self.model.duplicate_row(row, name)
        if new_row is not None:
            self._select_source_row(new_row)

    def delete_row(self) -> None:
        self._commit_pending()
        row = self._current_source_row()
        if row is None:
            return
        name = self.model.name_of(row) or "row " + str(row + 1)
        if QMessageBox.question(self, "Confirm Delete",
                                "Delete '" + name + "'?") != QMessageBox.Yes:
            return
        self.model.delete_row(row)
        if self.model.rowCount():
            self._select_source_row(min(row, self.model.rowCount() - 1))
        else:
            self.form.set_row(-1)
        self._update_actions()

    def toggle_comment(self) -> None:
        row = self._current_source_row()
        if row is None:
            return
        if not self.model.toggle_comment(row):
            return
        self._update_row_label()
        self._update_actions()
        state = "commented out" if self.model.is_commented(row) else "uncommented"
        self.statusBar().showMessage(
            "'" + self.model.name_of(row) + "' " + state, 4000)

    def insert_break(self) -> None:
        row = self._current_source_row()
        if row is None:
            return
        if self.model.blanks_before(row):
            self.model.remove_blank_before(row)
        else:
            self.model.add_blank_before(row)
        self._update_row_label()
        self._update_actions()
        self._relayout_rows()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._make_scrolling_smooth(self.table, theme.BG_ELEVATED)
        self._make_scrolling_smooth(self.weapon_list, theme.BG)

    def dragEnterEvent(self, event) -> None:
        if self._dropped_csv(event) is not None:
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        path = self._dropped_csv(event)
        if path is None:
            return
        event.acceptProposedAction()
        if self._confirm_discard():
            self.load_file(path)

    def closeEvent(self, event) -> None:
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()

    def _write(self, path: str) -> None:
        try:
            self.model.save(path)
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))
            return
        self._last_dir = os.path.dirname(os.path.abspath(path))
        self._sync_map_combo()
        self.path_edit.setText(path)
        self._refresh_preview()
        self.statusBar().showMessage("Saved " + path, 6000)

    def _dropped_csv(self, event) -> Optional[str]:
        data = event.mimeData()
        if not data.hasUrls():
            return None
        for url in data.urls():
            path = url.toLocalFile()
            if path.lower().endswith(".csv"):
                return path
        return None

    def _commit_pending(self) -> None:
        editor = self.table.indexWidget(self.table.currentIndex())
        if editor is not None:
            self.table.commitData(editor)
            self.table.closeEditor(editor, QAbstractItemDelegate.NoHint)
        self.form.commit_pending()

    # Unsaved
    def _confirm_discard(self) -> bool:
        self._commit_pending()
        if not self.model.dirty:
            return True
        choice = QMessageBox.warning(
            self, "Unsaved Changes", "You have unsaved changes.",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if choice == QMessageBox.Save:
            self.save_file()
            return not self.model.dirty
        return choice == QMessageBox.Discard

    def _unique_name(self, base: str) -> str:
        if self.model.csv.find_by_name(base) is None:
            return base
        index = 2
        while self.model.csv.find_by_name(base + "_" + str(index)) is not None:
            index += 1
        return base + "_" + str(index)

    # Selected & Selection
    def _current_source_row(self) -> Optional[int]:
        index = self.table.selectionModel().currentIndex()
        if not index.isValid():
            return None
        return self.proxy.mapToSource(index).row()

    def _select_source_row(self, row: int) -> None:
        if row < 0 or row >= self.model.rowCount():
            return
        source = self.model.index(row, 0)
        index = self.proxy.mapFromSource(source)
        if not index.isValid():
            self.search_edit.clear()
            index = self.proxy.mapFromSource(source)
        if not index.isValid():
            return
        self.table.selectionModel().setCurrentIndex(
            index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.table.scrollTo(index)
        self.weapon_list.scrollTo(self.proxy.index(index.row(),
                                                   self.weapon_list.modelColumn()))

    def _on_model_reset(self) -> None:
        self.form.rebind()
        name_col = self.model.column_of(NAME_FIELD)
        self.weapon_list.setModelColumn(name_col if name_col is not None else 0)
        header = self.table.horizontalHeader()
        if header.sortIndicatorSection() < 0:
            self.proxy.sort(-1)

        headers = tuple(self.model.headers)
        if headers == self._sized_headers:
            return
        self._sized_headers = headers
        for col in self._check_cols:
            self.table.setItemDelegateForColumn(col, None)
        self._check_cols = [col for col in range(self.model.columnCount())
                            if self.model.is_bool_column(col)]
        for col in self._check_cols:
            self.table.setItemDelegateForColumn(col, self.check_delegate)
        self.table.resizeColumnsToContents()
        for col in range(self.model.columnCount()):
            width = min(max(header.sectionSize(col), 70), 320)
            if FIELD_TYPES.get(self.model.headers[col]) in COMBO_TYPES | {"count"}:
                width += theme.ChevronComboBox.ARROW_BOX
            header.resizeSection(col, width)

    def _on_current_changed(self, current: QModelIndex, _previous) -> None:
        if not current.isValid():
            self.form.set_row(-1)
            self._update_row_label()
            self._update_actions()
            return
        self.model.history.break_merge()
        self.form.set_row(self.proxy.mapToSource(current).row())
        self._update_row_label()
        self._update_actions()

    # Heights
    def _relayout_rows(self) -> None:
        has_breaks = any(self.model.blanks_before(i)
                         for i in range(self.model.rowCount()))

        wanted = self.sheet_delegate if has_breaks else self.plain_delegate
        if self.table.itemDelegate() is not wanted:
            self.table.setItemDelegate(wanted)

        if has_breaks:
            for row in range(self.proxy.rowCount()):
                gap = self.sheet_delegate.gap_for(self.proxy.index(row, 0))
                self.table.setRowHeight(row, ROW_HEIGHT + gap)
        elif self._rows_have_gaps:
            for row in range(self.proxy.rowCount()):
                self.table.setRowHeight(row, ROW_HEIGHT)
        self._rows_have_gaps = has_breaks
        self.weapon_list.doItemsLayout()

    def _on_model_touched(self) -> None:
        self._update_row_label()
        if self.tabs.currentIndex() == TAB_PREVIEW:
            self._refresh_preview()

    # Title
    def _on_dirty_changed(self, dirty: bool) -> None:
        name = os.path.basename(self.model.path) if self.model.path else ""
        title = APP_NAME + (" - " + name if name else "")
        self.setWindowTitle(title + (" *" if dirty else ""))
        self.dirty_label.setText("Unsaved changes" if dirty else "Saved")
        self._update_actions()

    def _on_load_warning(self, title: str, message: str) -> None:
        self.statusBar().showMessage(message.splitlines()[0], 10000)
        QMessageBox.warning(self, title, message)

    def _on_validation_failed(self, message: str) -> None:
        self.statusBar().showMessage(message, 6000)

    def _on_tab_changed(self, index: int) -> None:
        if self.model.preview_error and index != TAB_PREVIEW:
            self.tabs.setCurrentIndex(TAB_PREVIEW)
            self.statusBar().showMessage("Fix the CSV in Preview before switching tabs", 6000)
            return
        self.model.history.break_merge()
        self._commit_pending()
        if index == TAB_PREVIEW:
            self._refresh_preview()

    def _on_preview_edited(self) -> None:
        self._editing_preview = True
        try:
            self.model.replace_text(self.preview.toPlainText())
            self.preview._changed = self.model.changed_lines()
            self.preview._highlight_changed()
            self.preview._gutter.update()
            self._update_preview_status()
        except ValueError as exc:
            self.preview_status.setText("Invalid CSV: " + str(exc))
            self.preview_status.setToolTip("")
        finally:
            self._editing_preview = False
            self._update_actions()

    def _refresh_preview(self) -> None:
        if self._editing_preview or self.model.preview_error:
            return
        self.preview.setReadOnly(not bool(self.model.path))
        if not self.model.headers and not self.model.path:
            self.preview.set_content(
                "No CSV loaded.\n\nOpen a file to preview it here.", set())
            self.preview_status.setText("")
            return
        text = self.model.render()
        changed = self.model.changed_lines()
        self.preview.set_content(text, changed)
        self._update_preview_status()

    def _update_preview_status(self) -> None:
        names = self.model.csv.duplicate_names()
        if names:
            self.preview_status.setText("Warning: duplicate weapon names: "
                                        + ", ".join(names))
            details = "\n".join(name + " (rows "
                                + ", ".join(str(i + 1) for i in rows) + ")"
                                for name, rows in names.items())
            self.preview_status.setToolTip(theme.tooltip(
                "Duplicate live weapons:\n" + details
                + "\nRename or comment out the extras; the game only keeps the last one's settings."))
            return
        self.preview_status.setToolTip("")
        changed = self.model.changed_lines()
        if not self.model.dirty:
            self.preview_status.setText("Matches last saved version")
        elif changed:
            self.preview_status.setText(
                str(len(changed)) + " line(s) changed since last save")
        else:
            self.preview_status.setText("Unsaved changes")

    # Status
    def _update_row_label(self) -> None:
        row = self._current_source_row()
        if row is None:
            self.row_label.setText("")
            self.status_label.setText(
                "No file open" if not self.model.headers else "No row selected")
            return
        bits = ["Row " + str(row + 1) + " of " + str(self.model.rowCount())]
        if self.model.is_commented(row):
            bits.append("commented out")
        blanks = self.model.blanks_before(row)
        if blanks:
            bits.append(str(blanks) + " blank line(s) above")
        self.row_label.setText(" • ".join(bits))
        self.status_label.setText(
            "Editing " + (self.model.name_of(row) or "row " + str(row + 1)))

    # Undo/Redo
    def _update_history_actions(self) -> None:
        can_undo = self.model.can_undo() or bool(self.model.preview_error)
        can_redo = self.model.can_redo() and not self.model.preview_error
        self.act_undo.setEnabled(can_undo)
        self.act_redo.setEnabled(can_redo)
        self.act_redo_alt.setEnabled(can_redo)

        undo_tip = theme.tooltip(
            "Undo " + self.model.undo_label() if can_undo else "Nothing to undo",
            hint="Ctrl+Z")
        redo_tip = theme.tooltip(
            "Redo " + self.model.redo_label() if can_redo else "Nothing to redo",
            hint="Ctrl+Y")
        for button in self._undo_buttons:
            button.setEnabled(can_undo)
            button.setToolTip(undo_tip)
        for button in self._redo_buttons:
            button.setEnabled(can_redo)
            button.setToolTip(redo_tip)

    # Enable
    def _update_actions(self) -> None:
        self._update_history_actions()
        loaded = bool(self.model.headers)
        row = self._current_source_row()
        for widget in (self.save_btn, self.act_save, self.act_save_as,
                       self.preview_save_btn):
            widget.setEnabled(bool(self.model.path) or loaded)
        for widget in (self.add_btn, self.act_add):
            widget.setEnabled(loaded)
        for widget in (self.copy_btn, self.delete_btn, self.comment_btn,
                       self.break_btn, self.act_copy, self.act_delete,
                       self.act_comment, self.act_break):
            widget.setEnabled(loaded and row is not None)
        if row is not None and self.model.blanks_before(row):
            self.break_btn.setText("Remove Break")
            self.break_btn.setToolTip(theme.tooltip(
                "Delete the blank line above this row", hint="Ctrl+B"))
        else:
            self.break_btn.setText("Section Break")
            self.break_btn.setToolTip(theme.tooltip(
                "Insert a blank line above this row", hint="Ctrl+B"))

        if row is not None and self.model.is_commented(row):
            self.comment_btn.setText("Uncomment")
            self.comment_btn.setToolTip(theme.tooltip(
                "Remove the // so the game reads this weapon again",
                hint="Ctrl+/"))
        else:
            self.comment_btn.setText("Comment Out")
            self.comment_btn.setToolTip(theme.tooltip(
                "Prefix this row with // so the game skips it", hint="Ctrl+/"))
