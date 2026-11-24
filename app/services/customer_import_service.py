"""Import customer contacts from an Excel ledger workbook.

Used by the Customer Database window ("Import Excel") and by the
one-off migration script, so it handles both common header layouts:
the ArmaTech ledger (Particulars / Contact Name / Mobile Nos. / ...)
and a plain Company / Contact / Phone / Email table.
"""

import re
from pathlib import Path

from app.services.xlsx_reader import read_first_sheet
from app.services import customer_service


_TITLE_RE = re.compile(r"^(m/s\.?|messrs\.?|mr\.?|mrs\.?|ms\.?|miss\.?)\s*", re.I)
_SPLIT_RE = re.compile(r"[/,;|]| or ", re.I)
# Excel stores control chars in shared strings as literal "_x0004_" markers.
_XESC_RE = re.compile(r"_x[0-9A-Fa-f]{4}_")


def _clean_text(value):
    text = _XESC_RE.sub(" ", str(value or ""))
    text = "".join(" " if ord(ch) < 32 else ch for ch in text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_company(value):
    text = _clean_text(value)
    return text.strip(" ,.")


def _clean_contact(value):
    text = _clean_text(value)
    previous = None
    while text and text != previous:
        previous = text
        text = _TITLE_RE.sub("", text).strip(" .,-")
    if not re.search(r"[A-Za-z]", text):
        return ""
    return text


def _norm_phone(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) > 12:
        digits = digits[-10:]
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits if len(digits) >= 7 else ""


def _pick_phone(*values):
    for value in values:
        for token in _SPLIT_RE.split(str(value or "")):
            phone = _norm_phone(token)
            if phone:
                return phone
    return ""


def _clean_email(value):
    text = _clean_text(value)
    if "@" in text and "." in text.split("@")[-1]:
        return text
    return ""


def _find_header(rows):
    """Return (header_row_index, column_map) or fall back to defaults."""
    for index, row in enumerate(rows[:40]):
        cells = [_clean_text(c).lower() for c in row]
        if not any("particulars" in c or "company" in c for c in cells):
            continue

        def find(*needles, default=None):
            for needle in needles:
                for col, cell in enumerate(cells):
                    if needle in cell:
                        return col
            return default

        mapping = {
            "company": find("particulars", "company", default=0),
            "contact": find("contact", default=1),
            "mobile": find("mobile", default=2),
            "phone": find("phone no", "phone", default=4),
            "email": find("e-mail", "email", default=5),
        }
        return index, mapping
    return -1, {
        "company": 0, "contact": 1, "mobile": 2, "phone": 4, "email": 5,
    }


def rows_to_customers(rows):
    """Convert sheet rows into customer dicts (skips blanks/headers)."""
    header_index, columns = _find_header(rows)
    customers = []

    for row in rows[header_index + 1:]:
        def cell(name):
            col = columns.get(name)
            if col is None or col >= len(row):
                return ""
            return row[col]

        company = _clean_company(cell("company"))
        if not company or company.lower() in ("particulars", "company name"):
            continue

        contact = _clean_contact(cell("contact"))
        phone = _pick_phone(cell("mobile"), cell("phone"))
        email = _clean_email(cell("email"))

        customers.append({
            "name": contact or company,
            "company": company,
            "contact_person": contact,
            "phone": phone,
            "email": email,
            "address": "",
            "city": "",
            "state": "",
            "pincode": "",
            "country": "India",
            "gstin": "",
        })

    return customers


def import_customers_from_excel(path, upload_cloud=True, progress=None):
    """Read a workbook and import every contact locally, then to the sheet.

    `progress(stage, done, total)` is optional and called from the caller's
    thread, so the UI can marshal it however it likes.
    """
    path = Path(path)
    rows = read_first_sheet(path)
    customers = rows_to_customers(rows)

    if progress:
        progress("parsed", len(customers), len(customers))

    local = customer_service.bulk_import_customers(customers)

    if progress:
        progress("saved", local["total"], local["total"])

    cloud = None
    if upload_cloud and customers:
        try:
            from app.services.cloud_sync import upload_customers_bulk_to_cloud
            cloud = upload_customers_bulk_to_cloud(
                customers,
                progress=lambda done, total: (
                    progress("uploading", done, total) if progress else None
                ),
            )
        except Exception as e:
            cloud = {"supported": False, "error": str(e)}

    return {
        "parsed": len(customers),
        "local": local,
        "cloud": cloud,
    }


if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else r"D:\Ledger Contact Details 20.11.26.xlsx"
    result = import_customers_from_excel(target, upload_cloud=False)
    print(json.dumps(result, indent=2))
