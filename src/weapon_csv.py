import csv
import difflib
import io
from typing import Dict, List, Optional, Set, Union

COMMENT_PREFIX = "//"
NAME_FIELD = "weapon_name"
UPGRADE_SUFFIXES = ("_upgraded", "_up", "_rdw_up")

Key = Union[int, str]


def is_blank_csv_line(line: List[str]) -> bool:
    return not line or not any(cell.strip() for cell in line)


def diff_line_numbers(current: str, baseline: str) -> Set[int]:
    matcher = difflib.SequenceMatcher(None, baseline.splitlines(),
                                      current.splitlines(), autojunk=False)
    changed: Set[int] = set()
    for tag, _b1, _b2, c1, c2 in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            changed.update(range(c1 + 1, c2 + 1))
    return changed


def read_csv_lines(path: str) -> List[List[str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.reader(fh, strict=True))


def write_text(path: str, text: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        fh.write(text)


def upgrade_suggestions(name: str) -> List[str]:
    name = name.strip()
    return [name + suffix for suffix in UPGRADE_SUFFIXES] if name else []


def derive_upgrade_name(current_upgrade: str, old_name: str,
                        new_name: str) -> str:
    for suffix in UPGRADE_SUFFIXES:
        if current_upgrade == old_name + suffix:
            return new_name + suffix
    return current_upgrade


class Row:

    __slots__ = ("cells", "headers", "commented", "blanks_before", "changed")

    def __init__(self, cells: List[str], headers: List[str],
                 commented: bool = False,
                 blanks_before: Optional[List[int]] = None) -> None:
        self.cells = list(cells)
        self.headers = headers
        self.commented = commented
        self.blanks_before = list(blanks_before or [])
        self.changed = False

    def column(self, key: Key) -> Optional[int]:
        if isinstance(key, int):
            return key if key >= 0 else None
        try:
            return self.headers.index(key)
        except ValueError:
            return None

    def get(self, key: Key, default: str = "") -> str:
        col = self.column(key)
        if col is None or col >= len(self.cells):
            return default
        return self.cells[col]

    def set(self, key: Key, value: str) -> None:
        col = self.column(key)
        if col is None:
            return
        if col < len(self.cells):
            self.cells[col] = value
            return
        if not value:
            return
        self.cells.extend([""] * (col - len(self.cells)))
        self.cells.append(value)

    def __getitem__(self, key: Key) -> str:
        return self.get(key)

    def __setitem__(self, key: Key, value: str) -> None:
        self.set(key, value)

    def __contains__(self, key: Key) -> bool:
        return self.column(key) is not None

    def values(self) -> List[str]:
        return list(self.cells)

    def copy(self) -> "Row":
        return Row(self.cells, self.headers)


class WeaponCSV:

    def __init__(self) -> None:
        self.headers: List[str] = []
        self.rows: List[Row] = []
        self.trailing_blanks: List[int] = []

    def load_lines(self, lines: List[List[str]]) -> None:
        if not lines or is_blank_csv_line(lines[0]):
            raise ValueError("The first line must contain the CSV column headers.")
        self.headers = list(lines[0])
        self.rows = []

        blanks_before: List[int] = []
        for line in lines[1:]:
            if is_blank_csv_line(line):
                blanks_before.append(len(line))
                continue

            cells = list(line)
            commented = bool(cells and cells[0].startswith(COMMENT_PREFIX))
            if commented:
                cells[0] = cells[0][len(COMMENT_PREFIX):]

            self.rows.append(Row(cells, self.headers, commented, blanks_before))
            blanks_before = []

        self.trailing_blanks = blanks_before

    def render(self, terminator: str = "\n") -> str:
        if not self.headers:
            return ""

        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator=terminator)
        writer.writerow(self.headers)
        for row in self.rows:
            for count in row.blanks_before:
                writer.writerow([""] * count)
            cells = list(row.cells)
            if cells and row.commented:
                cells[0] = COMMENT_PREFIX + cells[0]
            writer.writerow(cells)

        for count in self.trailing_blanks:
            writer.writerow([""] * count)

        text = buf.getvalue()
        if text and not text.endswith(terminator):
            text += terminator
        return text

    def new_row(self) -> Row:
        return Row([""] * len(self.headers), self.headers)

    def valid_index(self, idx: Optional[int]) -> bool:
        return idx is not None and 0 <= idx < len(self.rows)

    def column_index(self, name: str) -> Optional[int]:
        try:
            return self.headers.index(name)
        except ValueError:
            return None

    def duplicate_headers(self) -> List[str]:
        seen: Set[str] = set()
        dupes: List[str] = []
        for header in self.headers:
            if header in seen and header not in dupes:
                dupes.append(header)
            seen.add(header)
        return dupes

    def duplicate_names(self) -> Dict[str, List[int]]:
        col = self.column_index(NAME_FIELD)
        if col is None:
            return {}
        found: Dict[str, List[int]] = {}
        for i, row in enumerate(self.rows):
            name = row.get(col).strip()
            if name and not row.commented:
                found.setdefault(name, []).append(i)
        return {name: rows for name, rows in found.items() if len(rows) > 1}

    def find_by_name(self, name: str,
                     exclude: Optional[int] = None) -> Optional[int]:
        target = name.strip()
        col = self.column_index(NAME_FIELD)
        if not target or col is None:
            return None
        for i, row in enumerate(self.rows):
            if i == exclude or row.commented:
                continue
            if row.get(col).strip() == target:
                return i
        return None

    def row_matches(self, row: Row, query: str) -> bool:
        if not query:
            return True
        return any(query in cell.lower() for cell in row.cells)

    def distinct_values(self, column: Key) -> Set[str]:
        found: Set[str] = set()
        for row in self.rows:
            value = row.get(column).strip()
            if value:
                found.add(value)
        return found

    def blanks_before(self, idx: int) -> int:
        if not self.valid_index(idx):
            return 0
        return len(self.rows[idx].blanks_before)

    def append_row(self, row: Row) -> int:
        self.rows.append(row)
        return len(self.rows) - 1

    def duplicate_row(self, idx: int) -> Row:
        return self.rows[idx].copy()

    def delete_row(self, idx: int) -> None:
        deleted = self.rows.pop(idx)

        if idx < len(self.rows):
            nxt = self.rows[idx]
            nxt.blanks_before = deleted.blanks_before + nxt.blanks_before
        else:
            self.trailing_blanks = deleted.blanks_before + self.trailing_blanks

    def toggle_comment(self, idx: int) -> None:
        self.rows[idx].commented = not self.rows[idx].commented

    def add_blank_before(self, idx: int) -> None:
        self.rows[idx].blanks_before = self.rows[idx].blanks_before + [0]

    def remove_blank_before(self, idx: int) -> None:
        self.rows[idx].blanks_before = self.rows[idx].blanks_before[:-1]

    def is_section_label(self, idx: int) -> bool:
        row = self.rows[idx]
        if not row.commented:
            return False
        return not any(cell.strip() for cell in row.cells[1:])
