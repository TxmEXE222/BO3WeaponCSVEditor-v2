from typing import List, Optional, Tuple

from weapon_csv import Row

State = Tuple[List[str], List[tuple], List[int]]


def snapshot(csv) -> State:
    return (list(csv.headers),
            [(list(r.cells), r.commented, list(r.blanks_before))
             for r in csv.rows],
            list(csv.trailing_blanks))


def restore(csv, state: State) -> None:
    headers, rows, trailing = state
    csv.headers = list(headers)
    csv.rows = [Row(cells, csv.headers, commented, blanks)
                for cells, commented, blanks in rows]
    csv.trailing_blanks = list(trailing)


class Entry:

    __slots__ = ("label", "key", "state", "row")

    def __init__(self, label: str, key, state: State,
                 row: Optional[int]) -> None:
        self.label = label
        self.key = key
        self.state = state
        self.row = row


class UndoHistory:

    LIMIT = 200

    def __init__(self, csv) -> None:
        self._csv = csv
        self._undo: List[Entry] = []
        self._redo: List[Entry] = []
        self._merge_key = None
        self._busy = False

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._merge_key = None

    def break_merge(self) -> None:
        self._merge_key = None

    def record(self, label: str, key=None,
               row: Optional[int] = None) -> None:
        if self._busy:
            return
        if key is not None and key == self._merge_key and self._undo:
            self._redo.clear()
            return
        self._undo.append(Entry(label, key, snapshot(self._csv), row))
        if len(self._undo) > self.LIMIT:
            self._undo.pop(0)
        self._redo.clear()
        self._merge_key = key

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo_label(self) -> str:
        return self._undo[-1].label if self._undo else ""

    def redo_label(self) -> str:
        return self._redo[-1].label if self._redo else ""

    def undo(self) -> Optional[Entry]:
        return self._step(self._undo, self._redo)

    def redo(self) -> Optional[Entry]:
        return self._step(self._redo, self._undo)

    def _step(self, source: List[Entry],
              target: List[Entry]) -> Optional[Entry]:
        if not source:
            return None
        entry = source.pop()
        self._busy = True
        try:
            target.append(Entry(entry.label, None, snapshot(self._csv),
                                entry.row))
            restore(self._csv, entry.state)
        finally:
            self._busy = False
        self._merge_key = None
        return entry
