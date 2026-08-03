"""Dependency-free .xlsx reading helpers (zipfile + ElementTree).

The NixOS dev venv has no pip, so we parse the OOXML package directly:
an .xlsx is a ZIP of XML parts. Shared strings are resolved once, then each
worksheet is streamed with iterparse (elem.clear()) so the 13 MB / 150k-row
workbook stays memory-friendly.
"""

from __future__ import annotations

import io
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def col_to_idx(ref: str) -> int:
    """Convert a cell reference like 'AB12' to a 1-based column index."""
    letters = "".join(c for c in ref if c.isalpha())
    idx = 0
    for c in letters:
        idx = idx * 26 + (ord(c) - 64)
    return idx


def load_shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    ss: list[str] = []
    for si in root.iter(NS + "si"):
        ss.append("".join(t.text or "" for t in si.iter(NS + "t")))
    return ss


def sheet_names(z: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(z.read("xl/workbook.xml"))
    return [sh.get("name") for sh in root.iter(NS + "sheet")]


def worksheet_paths(z: zipfile.ZipFile) -> list[str]:
    """Worksheet XML parts sorted by their sheetN.xml numeric suffix."""
    return sorted(
        [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")],
        key=lambda p: int("".join(ch for ch in p if ch.isdigit()) or 0),
    )


class Workbook:
    """Thin wrapper bundling a zip handle with its shared strings + sheet map."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._zip = zipfile.ZipFile(self.path)
        self.shared = load_shared_strings(self._zip)
        names = sheet_names(self._zip)
        paths = worksheet_paths(self._zip)
        self.sheets: dict[str, str] = {}
        for i, wsf in enumerate(paths):
            nm = names[i] if i < len(names) else wsf
            self.sheets[nm] = wsf

    def close(self) -> None:
        self._zip.close()

    def __enter__(self) -> "Workbook":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def iter_rows(self, sheet_name: str):
        """Yield (row_number, {col_idx: value}) for every row in a sheet."""
        ws_path = self.sheets[sheet_name]
        data = self._zip.read(ws_path)
        row_count = 0
        for _event, elem in ET.iterparse(io.BytesIO(data), events=("end",)):
            if elem.tag != NS + "row":
                continue
            row_count += 1
            r = int(elem.get("r", row_count))
            cells: dict[int, str] = {}
            for c in elem.findall(NS + "c"):
                ref = c.get("r", "")
                t = c.get("t", "")
                v = c.find(NS + "v")
                inl = c.find(NS + "is")
                val = ""
                if t == "s" and v is not None:
                    val = self.shared[int(v.text)]
                elif t == "inlineStr" and inl is not None:
                    val = "".join(x.text or "" for x in inl.iter(NS + "t"))
                elif v is not None:
                    val = v.text or ""
                ci = col_to_idx(ref) if ref else len(cells) + 1
                cells[ci] = val
            yield r, cells
            elem.clear()

    def read_records(self, sheet_name: str) -> tuple[list[str], list[dict[str, str]]]:
        """Read a sheet into (header_names, [ {header: value} ... ])."""
        header: list[str] = []
        col_map: dict[int, str] = {}
        records: list[dict[str, str]] = []
        for r, cells in self.iter_rows(sheet_name):
            if r == 1:
                max_col = max(cells) if cells else 0
                header = [cells.get(i, "").strip() for i in range(1, max_col + 1)]
                col_map = {i: cells.get(i, "").strip() for i in range(1, max_col + 1)}
                continue
            rec = {name: cells.get(i, "") for i, name in col_map.items()}
            records.append(rec)
        return header, records
