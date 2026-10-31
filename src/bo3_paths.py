import os
from typing import List, Optional, Tuple

WEAPON_TABLE_HEADER = "weapon_name,upgrade_name"
WEAPON_TABLE_FOLDER = os.path.join("gamedata", "weapons", "zm")


def tools_path() -> Optional[str]:
    return os.environ.get("TA_TOOLS_PATH") or None


def find_usermaps() -> Optional[str]:
    tools = tools_path()
    if not tools:
        return None
    usermaps = os.path.join(tools, "usermaps")
    return usermaps if os.path.isdir(usermaps) else None


def weapon_tables(map_dir: str) -> List[str]:
    folder = os.path.join(map_dir, WEAPON_TABLE_FOLDER)
    try:
        names = sorted(os.listdir(folder), key=str.lower)
    except OSError:
        return []
    tables = []
    for name in names:
        path = os.path.join(folder, name)
        if not name.lower().endswith(".csv"):
            continue
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as fh:
                header = fh.readline().strip().lower()
        except OSError:
            continue
        if header.startswith(WEAPON_TABLE_HEADER):
            tables.append(path)
    return tables


def list_usermaps(usermaps: str) -> List[Tuple[str, List[str]]]:
    try:
        names = sorted(os.listdir(usermaps), key=str.lower)
    except OSError:
        return []
    return [(name, weapon_tables(os.path.join(usermaps, name)))
            for name in names if os.path.isdir(os.path.join(usermaps, name))]
