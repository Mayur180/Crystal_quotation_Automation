"""Minimal XLSX reader (first sheet) without third-party packages.

Only used by the customer importer, so it favours robustness for plain
data workbooks over full Excel feature support: shared strings, inline
strings, and numeric cells are read as text.
"""

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
}

_COL_RE = re.compile(r"([A-Z]+)")


def _col_index(ref):
    match = _COL_RE.match(ref or "")
    if not match:
        return None
    index = 0
    for ch in match.group(1):
        index = index * 26 + (ord(ch) - 64)
    return index - 1


def _shared_strings(zf):
    try:
        with zf.open("xl/sharedStrings.xml") as fh:
            root = ET.parse(fh).getroot()
    except KeyError:
        return []
    values = []
    for si in root.findall("main:si", _NS):
        parts = [node.text or "" for node in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")]
        values.append("".join(parts))
    return values


def _first_sheet_path(zf):
    with zf.open("xl/workbook.xml") as fh:
        root = ET.parse(fh).getroot()
    sheets = root.find("main:sheets", _NS)
    if sheets is None or not len(sheets):
        raise ValueError("Workbook has no sheets")
    sheet = sheets[0]
    rel_id = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    if not rel_id:
        return "xl/worksheets/sheet1.xml"

    with zf.open("xl/_rels/workbook.xml.rels") as fh:
        rels = ET.parse(fh).getroot()
    for rel in rels.findall("pkg:Relationship", _NS):
        if rel.get("Id") == rel_id:
            target = (rel.get("Target") or "").lstrip("/")
            return target if target.startswith("xl/") else f"xl/{target}"
    return "xl/worksheets/sheet1.xml"


def read_first_sheet(path):
    """Return the first sheet as a list of rows (lists of strings)."""
    path = Path(path)
    with zipfile.ZipFile(path) as zf:
        shared = _shared_strings(zf)
        sheet_path = _first_sheet_path(zf)
        with zf.open(sheet_path) as fh:
            root = ET.parse(fh).getroot()

    rows_by_index = {}
    max_col = -1
    for row in root.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
        r_index = int(row.get("r") or len(rows_by_index) + 1)
        cells = {}
        for cell in row.findall("main:c", _NS):
            col = _col_index(cell.get("r"))
            if col is None:
                continue
            cell_type = cell.get("t")
            value = ""
            if cell_type == "inlineStr":
                parts = [n.text or "" for n in cell.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")]
                value = "".join(parts)
            else:
                v = cell.find("main:v", _NS)
                if v is not None:
                    raw = v.text or ""
                    if cell_type == "s" and raw.strip().isdigit():
                        idx = int(raw)
                        value = shared[idx] if idx < len(shared) else ""
                    else:
                        value = raw
            cells[col] = str(value).strip()
            max_col = max(max_col, col)
        rows_by_index[r_index] = cells

    if not rows_by_index:
        return []

    width = max_col + 1
    result = []
    for r_index in range(1, max(rows_by_index) + 1):
        cells = rows_by_index.get(r_index, {})
        result.append([cells.get(col, "") for col in range(width)])
    return result
