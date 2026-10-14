"""
CRYSTAL / ARMATECH ASSOCIATES
Single-Page Crystal Word Quotation Generator

Replace:
    app/generators/quotation_generator.py

Quotation flow (single page):
    1. Header (logo, offer #, date)
    2. Customer + seller block
    3. Item table
    4. Totals + GST
    5. Amount in words
    6. Terms & conditions
    7. Signature

Primary output:
    Editable Microsoft Word (.docx)

Optional PDF:
    If LibreOffice or docx2pdf is available, a PDF can also be created.

Important:
    - Monetary calculations use Decimal consistently.
    - No product price is invented.
    - Technical specifications come from catalog data when available.
    - Customer and seller information are kept separate.
    - The generator accepts the existing quotation-form interface.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import (
    WD_CELL_VERTICAL_ALIGNMENT,
    WD_TABLE_ALIGNMENT,
)
from docx.enum.text import (
    WD_ALIGN_PARAGRAPH,
    WD_BREAK,
)
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import (
    Mm,
    Pt,
    RGBColor,
)


# ============================================================
# OPTIONAL APPLICATION IMPORTS
# ============================================================

try:
    from app.company import (
        COMPANY,
        QUOTATION_OUTPUT_DIR,
        get_word_dir,
        get_pdf_dir,
    )
except Exception:
    BASE_DIR = Path(__file__).resolve().parents[2]

    QUOTATION_OUTPUT_DIR = (
        BASE_DIR / "output" / "quotations"
    )

    QUOTATION_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    COMPANY = {
        "name": "ARMATECH ASSOCIATES",
        "brand": "CRYSTAL",
        "address": (
            "W-174A, 'S' Block, M.I.D.C., "
            "Bhosari Industrial Estate, PUNE - 411 026. (INDIA)"
        ),
        "phone": "+91 7020991684 / +91 9699820070",
        "email": "armatech@gmail.com",
        "website": "www.armatechassociates.com",
        "tagline": "Precision Measurement Technology",
    }


try:
    from app.services.catalog_service import get_product
except Exception:
    get_product = None


try:
    from app.services.amount_in_words import amount_in_words
except Exception:

    def amount_in_words(value):
        return f"{float(value):,.2f} Rupees Only"


try:
    from app.services.quotation_number_service import (
        get_next_quotation_number,
    )
except Exception:

    _quotation_counter = 0

    def get_next_quotation_number():
        global _quotation_counter

        _quotation_counter += 1

        return f"AA/VMM/26-27/{_quotation_counter:03d}"


try:
    from app.services.quotation_history_service import (
        save_quotation as _save_quotation_history,
    )
except Exception:
    _save_quotation_history = None


# ============================================================
# BRAND / PAGE SETTINGS
# ============================================================

RED = RGBColor(180, 25, 35)
DARK_GREY = RGBColor(55, 55, 55)
MEDIUM_GREY = RGBColor(105, 105, 105)
WHITE = RGBColor(255, 255, 255)
BLACK = RGBColor(0, 0, 0)

DARK_RED = "8F1520"
LIGHT_GREY = "F2F2F2"
VERY_LIGHT_GREY = "F8F8F8"
BORDER = "D9D9D9"

FONT = "Arial"

PAGE_MARGIN_LEFT = Mm(15)
PAGE_MARGIN_RIGHT = Mm(15)
PAGE_MARGIN_TOP = Mm(12)
PAGE_MARGIN_BOTTOM = Mm(10)


# ============================================================
# TABLE ROW HEIGHTS (mm) - TUNE EACH PAGE HERE
# ============================================================
PAGE1_ROW_HEIGHT       = 8.0
PAGE2_SPEC_TOTAL       = 175.0
PAGE2_SPEC_MIN         = 5.75
PAGE3_HW_TOTAL         = 70.0
PAGE3_HW_MIN           = 5.0
PAGE3_SW_TOTAL         = 70.0
PAGE3_SW_MIN           = 5.0
PAGE4_ACC_TOTAL        = 140.0
PAGE4_ACC_MIN          = 10.0
PAGE4_ACC_ROW_H        = 20.0    # Fixed accessory row height (mm)
PAGE6_TERM_TOTAL       = 10.0
PAGE6_TERM_MIN         = 10.0
PAGE6_HEADER_ROW_H     = 8.0

# ============================================================
# TABLE COLUMN WIDTHS (mm) - TUNE EACH PAGE HERE
# ============================================================
# Page 2 — Tech Spec (2 cols)
PAGE2_W1 = 55.0
PAGE2_W2 = 115.0

# Page 3 — Features (2 cols each)
PAGE3_HW_W1 = 15.0
PAGE3_HW_W2 = 155.0
PAGE3_SW_W1 = 15.0
PAGE3_SW_W2 = 155.0

# Page 4 — Accessories (4 cols)
PAGE4_W1 = 20.0
PAGE4_W2 = 80.0
PAGE4_W3 = 20.0
PAGE4_W4 = 50.0

# Page 5 — Commercial (6 cols)
PAGE5_W1 = 12.0
PAGE5_W2 = 40.0
PAGE5_W3 = 30.0
PAGE5_W4 = 15.0
PAGE5_W5 = 35.0
PAGE5_W6 = 35.0

# Page 6 — Terms (3 cols)
PAGE6_W1 = 15.0     # Sr. No. column
PAGE6_W2 = 55.0     # Particulars column
PAGE6_W3 = 100.0    # Terms column

# ============================================================
# PAGE 5 - ROW HEIGHTS (mm)
# ============================================================
PAGE5_MAIN_ROW_H  = 20.0    # Main table rows
PAGE5_TOTAL_ROW_H = 12.0    # Totals table rows
PAGE5_AFTER_WORDS = 30.0    # Space after Amount in Words (mm)






# ============================================================
# LOCAL-FIRST SAVE HELPERS
# ============================================================

def _local_temp_dir() -> Path:
    """Return a local temp folder for staging files."""
    import tempfile
    base = Path(tempfile.gettempdir()) / "CrystalQuotation"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _safe_copy(src: Path, dst: Path, retries: int = 5, delay: float = 0.5) -> bool:
    """
    Copy src to dst, creating parent folders as needed.

    Retries up to `retries` times with `delay` seconds between attempts.
    This handles the common case where Word/LibreOffice still holds
    a file handle on the source for a moment after saving.
    """
    import time

    dst.parent.mkdir(parents=True, exist_ok=True)

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            shutil.copy2(str(src), str(dst))
            if attempt > 1:
                print(f"[copy] Success on retry {attempt}")
            return True
        except Exception as e:
            last_error = e
            if attempt < retries:
                time.sleep(delay)

    print(f"[copy] Failed after {retries} retries: {src} -> {dst}: {last_error}")
    return False



# ============================================================
# BASIC VALUE HELPERS
# ============================================================

def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


def _decimal(
    value: Any,
    default: Decimal = Decimal("0"),
) -> Decimal:
    """
    Convert any numeric-like value to Decimal.

    This is the main protection against:
        float + Decimal
        Decimal + float
    errors.
    """

    if value is None:
        return default

    if isinstance(value, Decimal):
        return value

    if isinstance(value, bool):
        return Decimal("1") if value else Decimal("0")

    try:
        text = str(value).strip()

        if not text:
            return default

        text = text.replace(",", "")
        text = text.replace("₹", "")
        text = text.strip()

        return Decimal(text)

    except (InvalidOperation, ValueError, TypeError):
        return default


def _number(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Compatibility helper for non-money values.
    """

    try:
        return float(_decimal(value))
    except Exception:
        return default


def _money(value: Any) -> str:
    amount = _decimal(value)

    return f"₹ {amount:,.2f}"


def _safe_filename(value: str) -> str:
    value = _text(value, "quotation")

    return re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        value,
    )


def _money_for_words(value: Decimal) -> str:
    """
    Call the existing amount-in-words service safely.
    """

    try:
        return str(amount_in_words(float(value)))
    except Exception:
        return f"{value:,.2f} Rupees Only"


# ============================================================
# PROJECT / LOGO
# ============================================================

def _project_root() -> Path:
    """
    Locate the project root by walking up from this file
    until we find the 'assets' directory.
    """
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / "assets").is_dir():
            return candidate
    # Fallback to old behavior if assets/ can't be found
    return Path(__file__).resolve().parents[2]


def find_logo() -> Path | None:
    root = _project_root()

    candidates = [
        root / "assets" / "logo" / "armatech_logo.png",
        root / "assets" / "logo" / "armatech_logo.jpg",
        root / "assets" / "logo" / "ARMATECH_logo.png",
        root / "assets" / "logo" / "logo.png",
        root / "assets" / "logo" / "LOGO.png",
        root / "assets" / "armatech_logo.png",
        root / "assets" / "logo.png",
        root / "assets" / "LOGO.png",
        root / "LOGO.png",
    ]

    for path in candidates:
        if path.is_file():
            return path

    return None


# ============================================================
def find_product_image(product):
    """
    Resolve the product image path from the catalog.

    Handles:
      - Absolute paths
      - Legacy prefixes like /CRYSTAL_Quotation_Automation/assets/...
      - Relative paths (assets/images/foo.png)
      - Filenames with spaces or underscores
      - Case-insensitive matching
      - Fallback to [model].png / .jpg / .jpeg
    """
    root = _project_root()

    if not isinstance(product, dict):
        return None

    raw = _text(product.get("image_filename"))

    search_dirs = [
        root,
        root / "assets",
        root / "assets" / "images",
    ]

    def _try(candidate_name):
        if not candidate_name:
            return None

        name = str(candidate_name).strip().strip('"').strip("'")

        variants = [name]
        if " " in name:
            variants.append(name.replace(" ", "_"))
        if "_" in name:
            variants.append(name.replace("_", " "))

        for variant in variants:
            p = Path(variant)

            if p.is_absolute() and p.is_file():
                return p

            cleaned = variant.replace("\\", "/")
            for marker in (
                "CRYSTAL_Quotation_Automation/",
                "assets/images/",
                "assets/",
            ):
                if marker in cleaned:
                    cleaned = cleaned.split(marker, 1)[-1]
                    break
            cleaned = cleaned.lstrip("/")

            for base in search_dirs:
                cand = base / cleaned
                if cand.is_file():
                    return cand

                if cand.parent.is_dir():
                    target = cand.name.lower()
                    try:
                        for child in cand.parent.iterdir():
                            if child.is_file() and child.name.lower() == target:
                                return child
                    except Exception:
                        pass

            fname = Path(cleaned).name
            if fname and fname != cleaned:
                for base in search_dirs:
                    cand = base / fname
                    if cand.is_file():
                        return cand

        return None

    if raw:
        found = _try(raw)
        if found:
            return found

    # Fallback: [model].png / .jpg / .jpeg
    model = _text(product.get("model", "")).lower()
    if model:
        for base in search_dirs:
            if not base.is_dir():
                continue
            for ext in (".png", ".jpg", ".jpeg"):
                target = f"{model}{ext}"
                cand = base / target
                if cand.is_file():
                    return cand
                try:
                    for child in base.iterdir():
                        if child.is_file() and child.name.lower() == target:
                            return child
                except Exception:
                    pass

    return None


def _set_table_col_widths(table, widths_mm):
    """
    Apply fixed column widths to a table.
    widths_mm: list of floats (mm) — one per column.
    """
    from docx.shared import Mm as _Mm
    from docx.oxml.ns import qn as _qn
    from docx.oxml import OxmlElement as _OxmlElement

    # Disable autofit
    table.autofit = False

    # Set table layout to fixed
    tblPr = table._tbl.tblPr
    layout = tblPr.find(_qn("w:tblLayout"))
    if layout is None:
        layout = _OxmlElement("w:tblLayout")
        tblPr.append(layout)
    layout.set(_qn("w:type"), "fixed")

    # Set width on every cell in every row
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            if idx < len(widths_mm):
                cell.width = _Mm(widths_mm[idx])

    # Set grid column widths
    tbl = table._tbl
    grid = tbl.find(_qn("w:tblGrid"))
    if grid is not None:
        cols = grid.findall(_qn("w:gridCol"))
        for idx, col in enumerate(cols):
            if idx < len(widths_mm):
                col.set(_qn("w:w"), str(int(_Mm(widths_mm[idx]).twips)))


def _set_row_min_height(row, height_mm):
    """Force a minimum row height so tables stretch correctly.

    Accepts:
        - plain number (interpreted as mm)
        - Length object from docx.shared.Mm()
    """
    from docx.shared import Length as _Length

    # Convert to a Length object safely
    if isinstance(height_mm, _Length):
        length = height_mm
    else:
        try:
            # Plain number — treat as mm
            length = Mm(float(height_mm))
        except Exception:
            length = Mm(8.0)

    tr = row._tr
    trPr = tr.get_or_add_trPr()
    old = trPr.find(qn("w:trHeight"))
    if old is not None:
        trPr.remove(old)
    trHeight = OxmlElement("w:trHeight")
    trHeight.set(qn("w:val"), str(int(length.twips)))
    trHeight.set(qn("w:hRule"), "atLeast")
    trPr.append(trHeight)


# WORD FORMATTING HELPERS
# ============================================================

def _set_cell_shading(cell, fill):
    if fill is None:
        return

    if isinstance(fill, RGBColor):
        fill = str(fill)
    elif hasattr(fill, "rgb"):
        fill = str(fill.rgb)
    else:
        fill = str(fill)

    fill = fill.replace("#", "").strip().upper()

    if len(fill) != 6:
        raise ValueError(
            f"Invalid cell shading color: {fill!r}"
        )

    tc_pr = cell._tc.get_or_add_tcPr()

    old = tc_pr.find(qn("w:shd"))

    if old is not None:
        tc_pr.remove(old)

    shd = OxmlElement("w:shd")

    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)

    tc_pr.append(shd)


def _set_cell_border(
    cell,
    color=BORDER,
    size="6",
):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()

    borders = tc_pr.first_child_found_in(
        "w:tcBorders"
    )

    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)

    for edge in (
        "top",
        "left",
        "bottom",
        "right",
        "insideH",
        "insideV",
    ):
        tag = f"w:{edge}"

        element = borders.find(qn(tag))

        if element is None:
            element = OxmlElement(tag)
            borders.append(element)

        element.set(
            qn("w:val"),
            "single",
        )

        element.set(
            qn("w:sz"),
            size,
        )

        element.set(
            qn("w:space"),
            "0",
        )

        element.set(
            qn("w:color"),
            color,
        )


def _set_cell_text(
    cell,
    text,
    *,
    bold=False,
    size=11,
    color=BLACK,
    align=WD_ALIGN_PARAGRAPH.LEFT,
):
    cell.text = ""

    paragraph = cell.paragraphs[0]

    paragraph.alignment = align
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)

    run = paragraph.add_run(
        _text(text, "-")
    )

    run.bold = bold
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.color.rgb = color

    cell.vertical_alignment = (
        WD_CELL_VERTICAL_ALIGNMENT.CENTER
    )


def _add_page_title(
    doc,
    title: str,
    subtitle: str = "",
    center: bool = True,
):
    paragraph = doc.add_paragraph()

    if center:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(2)

    run = paragraph.add_run(
        title.upper()
    )

    run.bold = True
    run.font.name = FONT
    run.font.size = Pt(17)
    run.font.color.rgb = RED

    if subtitle:
        paragraph2 = doc.add_paragraph()

        if center:
            paragraph2.alignment = WD_ALIGN_PARAGRAPH.CENTER

        paragraph2.paragraph_format.space_after = Pt(9)

        run2 = paragraph2.add_run(
            subtitle
        )

        run2.font.name = FONT
        run2.font.size = Pt(11)
        run2.font.color.rgb = MEDIUM_GREY


def _add_section_bar(
    doc,
    title: str,
):
    table = doc.add_table(
        rows=1,
        cols=1,
    )

    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    cell = table.cell(0, 0)

    _set_cell_shading(
        cell,
        DARK_RED,
    )

    _set_cell_border(
        cell,
        DARK_RED,
        "0",
    )

    _set_cell_text(
        cell,
        title.upper(),
        bold=True,
        size=11,
        color=WHITE,
        align=WD_ALIGN_PARAGRAPH.LEFT,
    )

    cell.paragraphs[0].paragraph_format.left_indent = Mm(2)

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)

    return table


def _add_body(
    doc,
    text: str,
    *,
    size=11,
    bold=False,
    color=BLACK,
    after=5,
    align=WD_ALIGN_PARAGRAPH.LEFT,
):
    paragraph = doc.add_paragraph()

    paragraph.alignment = align

    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = 1.08

    run = paragraph.add_run(
        _text(text)
    )

    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color

    return paragraph


def _add_body_with_bold(doc, text, *, size=11, after=2):
    """
    Add a paragraph, parsing <b>...</b> or **...** as bold.
    Used for the Page 1 description.
    """
    import re as _re

    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.line_spacing = 1.05

    raw = str(text)
    raw = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', raw)

    parts = _re.split(r'(<b>.*?</b>)', raw, flags=_re.DOTALL)

    for part in parts:
        if not part:
            continue
        if part.startswith("<b>") and part.endswith("</b>"):
            inner = part[3:-4]
            run = paragraph.add_run(inner)
            run.bold = True
        else:
            run = paragraph.add_run(part)
            run.bold = False
        run.font.name = FONT
        run.font.size = Pt(size)

    return paragraph


def _add_field(
    doc,
    label: str,
    value: Any,
):
    paragraph = doc.add_paragraph()

    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.line_spacing = 1.05

    run = paragraph.add_run(
        f"{label}: "
    )

    run.bold = True
    run.font.name = FONT
    run.font.size = Pt(11)
    run.font.color.rgb = DARK_GREY

    run = paragraph.add_run(
        _text(value, "-")
    )

    run.font.name = FONT
    run.font.size = Pt(11)
    run.font.color.rgb = BLACK

    return paragraph


def _page_break(doc):
    paragraph = doc.add_paragraph()

    paragraph.paragraph_format.space_after = Pt(0)

    paragraph.add_run().add_break(
        WD_BREAK.PAGE
    )


# ============================================================
# HEADER / FOOTER
# ============================================================

def _add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    run = paragraph.add_run("Page ")

    run.font.name = FONT
    run.font.size = Pt(8)
    run.font.color.rgb = MEDIUM_GREY

    field_begin = OxmlElement("w:fldChar")
    field_begin.set(
        qn("w:fldCharType"),
        "begin",
    )

    instruction = OxmlElement("w:instrText")
    instruction.set(
        qn("xml:space"),
        "preserve",
    )
    instruction.text = " PAGE "

    field_end = OxmlElement("w:fldChar")
    field_end.set(
        qn("w:fldCharType"),
        "end",
    )

    run._r.append(field_begin)
    run._r.append(instruction)
    run._r.append(field_end)


def _configure_sections(doc, include_logo=True):
    logo = find_logo() if include_logo else None

    for section in doc.sections:
        # Explicit A4 page size (python-docx defaults to Letter)
        from docx.shared import Mm as _Mm
        section.page_width  = _Mm(210)
        section.page_height = _Mm(297)

        section.top_margin = PAGE_MARGIN_TOP
        section.bottom_margin = PAGE_MARGIN_BOTTOM
        section.left_margin = PAGE_MARGIN_LEFT
        section.right_margin = PAGE_MARGIN_RIGHT

        section.header_distance = Mm(7)
        section.footer_distance = Mm(8)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------
        if include_logo:
            # HEADER
            # ----------------------------------------------------

            header = section.header

            header.is_linked_to_previous = False

            hp = header.paragraphs[0]
            hp.text = ""

            hp.paragraph_format.space_after = Pt(2)

            header_table = header.add_table(
                rows=1,
                cols=2,
                width=Mm(174),
            )

            header_table.alignment = (
                WD_TABLE_ALIGNMENT.CENTER
            )

            header_table.autofit = False

            left = header_table.cell(0, 0)
            right = header_table.cell(0, 1)

            if logo:
                paragraph = left.paragraphs[0]
                paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                paragraph.paragraph_format.space_before = Pt(4)
                paragraph.paragraph_format.space_after = Pt(4)
                # Add a zero-width space first so Word doesn't collapse
                # the paragraph when only an image is present.
                paragraph.add_run("\u200b")
                run = paragraph.add_run()
                run.add_picture(str(logo), width=Mm(34))


            else:
                _set_cell_text(
                    left,
                    "CRYSTAL",
                    bold=True,
                    size=17,
                    color=RED,
                    align=WD_ALIGN_PARAGRAPH.LEFT,
                )

            right.text = ""

            paragraph = right.paragraphs[0]

            paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.RIGHT
            )

            paragraph.paragraph_format.space_after = Pt(1)

            run = paragraph.add_run(
                "ARMATECH ASSOCIATES"
            )

            run.bold = True
            run.font.name = FONT
            run.font.size = Pt(12)
            run.font.color.rgb = RED

            paragraph2 = right.add_paragraph()

            paragraph2.alignment = (
                WD_ALIGN_PARAGRAPH.RIGHT
            )

            paragraph2.paragraph_format.space_after = Pt(1)

            run = paragraph2.add_run(
                "CRYSTAL • Precision Measurement Technology"
            )

            run.font.name = FONT
            run.font.size = Pt(7.5)
            run.font.color.rgb = DARK_GREY

            paragraph3 = right.add_paragraph()

            paragraph3.alignment = (
                WD_ALIGN_PARAGRAPH.RIGHT
            )

            paragraph3.paragraph_format.space_after = Pt(0)

            run = paragraph3.add_run(
                f"{COMPANY.get('address', '')} | "
                f"{COMPANY.get('phone', '')}"
            )

            run.font.name = FONT
            run.font.size = Pt(6.5)
            run.font.color.rgb = MEDIUM_GREY


        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        footer = section.footer

        footer.is_linked_to_previous = False

        fp = footer.paragraphs[0]

        fp.text = ""

        fp.paragraph_format.space_before = Pt(3)
        fp.paragraph_format.space_after = Pt(0)

        ppr = fp._p.get_or_add_pPr()

        p_bdr = OxmlElement("w:pBdr")

        top = OxmlElement("w:top")

        top.set(
            qn("w:val"),
            "single",
        )

        top.set(
            qn("w:sz"),
            "6",
        )

        top.set(
            qn("w:space"),
            "4",
        )

        top.set(
            qn("w:color"),
            DARK_RED,
        )

        p_bdr.append(top)
        ppr.append(p_bdr)

        run = fp.add_run(
            f"{COMPANY.get('name', 'ARMATECH ASSOCIATES')} | "
            f"{COMPANY.get('email', '')} | "
            f"{COMPANY.get('website', '')}"
        )

        run.font.name = FONT
        run.font.size = Pt(7)
        run.font.color.rgb = MEDIUM_GREY

        _add_page_number(fp)


# ============================================================
# PRODUCT / CATALOG DATA
# ============================================================

def _resolve_product(model: str):
    if not get_product:
        return {}

    try:
        result = get_product(model)

        if isinstance(result, dict):
            return result

        return {}

    except Exception:
        return {}


# ============================================================
# ACCESSORY NORMALIZATION
# ============================================================

def _normalize_accessories(
    accessories,
):
    result = []

    if not accessories:
        return result

    if isinstance(
        accessories,
        dict,
    ):
        accessories = [accessories]

    for item in accessories:
        if not isinstance(
            item,
            dict,
        ):
            continue

        name = (
            item.get("name")
            or item.get("accessory")
            or item.get("product")
        )

        code = (
            item.get("code")
            or item.get("model")
            or item.get("catalog_no")
            or ""
        )

        qty = item.get(
            "qty",
            item.get(
                "quantity",
                1,
            ),
        )

        price = item.get(
            "price",
            item.get(
                "unit_price",
                0,
            ),
        )

        enabled = item.get(
            "enabled",
            item.get(
                "selected",
                True,
            ),
        )

        if not enabled:
            continue

        if not name:
            continue

        result.append(
            {
                "name": str(name),
                "code": str(code),
                "qty": _decimal(
                    qty,
                    Decimal("1"),
                ),
                "price": _decimal(
                    price,
                    Decimal("0"),
                ),
            }
        )

    return result


# ============================================================
# COMMERCIAL CALCULATION
# ============================================================

def calculate_totals(machine_price=0, machine_qty=1, accessories=None,
                     transportation=0, packing_percent=Decimal("3.5"),
                     packing_mode="Percentage (%)",
                     packing_value=None,
                     cgst_percent=Decimal("9"), sgst_percent=Decimal("9"),
                     gst_type="CGST + SGST",
                     gst_rate=None,
                     igst_percent=None,
                     buyback=0):
    machine_price = _decimal(machine_price)
    machine_qty = _decimal(machine_qty, Decimal("1"))
    transportation = _decimal(transportation)
    packing_percent = _decimal(packing_percent)
    cgst_percent = _decimal(cgst_percent)
    sgst_percent = _decimal(sgst_percent)
    accessories = _normalize_accessories(accessories)

    machine_total = machine_price * machine_qty
    accessory_total = Decimal("0")
    normalized_items = []

    for item in accessories:
        qty = _decimal(item["qty"], Decimal("1"))
        price = _decimal(item["price"])
        amount = qty * price
        accessory_total += amount
        normalized_items.append({
            "name": item["name"], "code": item["code"],
            "qty": qty, "price": price, "amount": amount,
        })

    subtotal = machine_total + accessory_total

    # BuyBack — subtracted from machine portion
    buyback_dec = _decimal(buyback)

    # Packing
    mode_str = str(packing_mode or "").strip().lower()
    if mode_str in ("amount (₹)", "amount", "fixed", "fixed amount", "flat"):
        packing = _decimal(
            packing_value if packing_value is not None else packing_percent
        )
    elif mode_str in ("no packing", "none"):
        packing = Decimal("0")
    else:
        packing = subtotal * packing_percent / Decimal("100")

    # Taxable = Machine + Accessories + Packing + Transportation − BuyBack
    taxable = subtotal + packing + transportation - buyback_dec
    if taxable < Decimal("0"):
        taxable = Decimal("0")

    # GST engine
    gst_type = str(gst_type or "CGST + SGST").strip()

    if gst_rate is None or _decimal(gst_rate) == Decimal("0"):
        gst_rate_dec = cgst_percent + sgst_percent
    else:
        gst_rate_dec = _decimal(gst_rate)

    cgst = Decimal("0")
    sgst = Decimal("0")
    igst = Decimal("0")

    if gst_type == "CGST + SGST":
        half = gst_rate_dec / Decimal("2")
        cgst = taxable * half / Decimal("100")
        sgst = taxable * half / Decimal("100")
    elif gst_type == "IGST":
        if igst_percent is not None and _decimal(igst_percent) > 0:
            igst = taxable * _decimal(igst_percent) / Decimal("100")
        else:
            igst = taxable * gst_rate_dec / Decimal("100")
    elif gst_type == "No GST":
        cgst = Decimal("0")
        sgst = Decimal("0")
        igst = Decimal("0")

    gst_total = cgst + sgst + igst
    grand_total = taxable + gst_total

    return {
        "machine_total": machine_total,
        "accessory_total": accessory_total,
        "subtotal": subtotal,
        "packing": packing,
        "transportation": transportation,
        "buyback": buyback_dec,
        "taxable": taxable,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "gst": gst_total,
        "gst_type": gst_type,
        "gst_rate": gst_rate_dec,
        "cgst_percent": (
            gst_rate_dec / Decimal("2")
            if gst_type == "CGST + SGST"
            else Decimal("0")
        ),
        "sgst_percent": (
            gst_rate_dec / Decimal("2")
            if gst_type == "CGST + SGST"
            else Decimal("0")
        ),
        "igst_percent": (
            gst_rate_dec if gst_type == "IGST" else Decimal("0")
        ),
        "grand_total": grand_total,
        "accessories": normalized_items,
    }
    """
    Central commercial calculation.

    Every monetary value remains Decimal.
    """

    machine_price = _decimal(machine_price)
    machine_qty = _decimal(
        machine_qty,
        Decimal("1"),
    )

    transportation = _decimal(
        transportation
    )

    packing_percent = _decimal(
        packing_percent
    )

    packing_mode = str(
        packing_mode or "Percentage (%)"
    ).strip()

    if packing_value is None:
        packing_value = packing_percent
    else:
        packing_value = _decimal(packing_value)

    if packing_mode == "Amount (₹)":
        packing_percent = Decimal("0")
    elif packing_mode == "No Packing":
        packing_percent = Decimal("0")
        packing_value = Decimal("0")
    else:
        packing_mode = "Percentage (%)"
        packing_percent = packing_value

    cgst_percent = _decimal(
        cgst_percent
    )

    sgst_percent = _decimal(
        sgst_percent
    )

    gst_type = str(
        gst_type or "CGST + SGST"
    ).strip()

    if gst_rate is None:
        gst_rate = (
            cgst_percent
            + sgst_percent
        )

    gst_rate = _decimal(
        gst_rate
    )

    igst_percent = _decimal(
        igst_percent
    )

    if gst_type == "CGST + SGST":
        half_rate = (
            gst_rate
            / Decimal("2")
        )
        cgst_percent = half_rate
        sgst_percent = half_rate
        igst_percent = Decimal("0")

    elif gst_type == "IGST":
        cgst_percent = Decimal("0")
        sgst_percent = Decimal("0")
        igst_percent = gst_rate

    elif gst_type == "No GST":
        cgst_percent = Decimal("0")
        sgst_percent = Decimal("0")
        igst_percent = Decimal("0")

    else:
        # Backward compatibility for older callers.
        gst_type = "CGST + SGST"

    accessories = _normalize_accessories(
        accessories
    )

    machine_total = (
        machine_price * machine_qty
    )

    accessory_total = Decimal("0")

    normalized_items = []

    for item in accessories:
        qty = _decimal(
            item["qty"],
            Decimal("1"),
        )

        price = _decimal(
            item["price"]
        )

        amount = qty * price

        accessory_total += amount

        normalized_items.append(
            {
                "name": item["name"],
                "code": item["code"],
                "qty": qty,
                "price": price,
                "amount": amount,
            }
        )

    subtotal = (
        machine_total
        + accessory_total
    )

    if packing_mode == "Amount (₹)":
        packing = packing_value
    elif packing_mode == "No Packing":
        packing = Decimal("0")
    else:
        packing = (
            subtotal
            * packing_percent
            / Decimal("100")
        )

    taxable = (
        subtotal
        + packing
        + transportation
    )

    cgst = (
        taxable
        * cgst_percent
        / Decimal("100")
    )

    sgst = (
        taxable
        * sgst_percent
        / Decimal("100")
    )

    igst = (
        taxable
        * igst_percent
        / Decimal("100")
    )

    gst = (
        cgst
        + sgst
        + igst
    )

    grand_total = (
        taxable
        + gst
    )

    return {
        "machine_total": machine_total,
        "accessory_total": accessory_total,
        "subtotal": subtotal,
        "packing": packing,
        "packing_mode": packing_mode,
        "packing_value": packing_value,
        "packing_percent": packing_percent,
        "transportation": transportation,
        "taxable": taxable,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "gst": gst,
        "gst_type": gst_type,
        "gst_rate": gst_rate,
        "cgst_percent": cgst_percent,
        "sgst_percent": sgst_percent,
        "igst_percent": igst_percent,
        "grand_total": grand_total,
        "accessories": normalized_items,
    }


# ============================================================
# PAGE 1
# CUSTOMER + QUOTATION + PRODUCT
# ============================================================

# ============================================================

# ============================================================
# PAGE 3
# MACHINE FEATURES
# ============================================================

# ============================================================
# PAGE 4
# SOFTWARE + ENVIRONMENT + ELECTRICAL + ACCESSORIES
# ============================================================

# ============================================================
# PAGE 5
# FINAL COMMERCIAL PRICING
# ============================================================

# ============================================================
# PAGE 6
# TERMS & CONDITIONS
# ============================================================

# ============================================================
# PDF CONVERSION
# ============================================================

def _find_libreoffice():
    candidates = [
        shutil.which("libreoffice"),
        shutil.which("soffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate

    return None


def _convert_docx_to_pdf(
    docx_path: Path,
):
    """
    Convert Word -> PDF.

    PDF is saved next to the input .docx (typically a local
    temp folder). Caller is responsible for copying it to the
    final destination.

    Tries, in order:
        1. LibreOffice (if installed)
        2. docx2pdf  (uses Microsoft Word)

    Returns the PDF Path on success, or None.
    """

    # PDF goes next to the input .docx (local staging)
    output_dir = docx_path.parent
    pdf_path = output_dir / f"{docx_path.stem}.pdf"

    # ---------- Attempt 1: LibreOffice ----------
    libreoffice = _find_libreoffice()

    if libreoffice:
        try:
            subprocess.run(
                [
                    libreoffice,
                    "--headless",
                    "--norestore",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(output_dir),
                    str(docx_path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )

            if pdf_path.exists():
                print(f"[PDF] LibreOffice -> {pdf_path}")
                return pdf_path
        except Exception as e:
            print(f"[PDF] LibreOffice failed: {e}")

    # ---------- Attempt 2: docx2pdf (uses Word) ----------
    try:
        from docx2pdf import convert as _docx2pdf_convert
        try:
            _docx2pdf_convert(str(docx_path), str(pdf_path))
        except Exception as e:
            # docx2pdf sometimes raises on Word.Quit even when the PDF
            # was actually created successfully. Check disk first.
            if not pdf_path.exists():
                print(f"[PDF] docx2pdf failed: {e}")
                return None

        if pdf_path.exists():
            print(f"[PDF] docx2pdf -> {pdf_path}")
            return pdf_path
    except ImportError:
        print("[PDF] docx2pdf not installed")

    print("[PDF] No PDF converter available")
    return None


# ============================================================
# MAIN GENERATOR
# ============================================================


# ═══════════════════════════════════════════════════════════════
# CRYSTAL — SINGLE-PAGE QUOTATION
# ═══════════════════════════════════════════════════════════════

def _crystal_divider(doc):
    """Draw a thin horizontal divider line (not a titled section bar)."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run("─" * 90)
    run.font.size = Pt(6)
    run.font.color.rgb = RGBColor(0xDF, 0xE3, 0xE9)


def _crystal_page(
    doc,
    quotation_number,
    quotation_date,
    customer,
    model,
    product,
    machine_price,
    machine_qty,
    totals,
    selected_terms=None,
    **kwargs,
):
    """Build the complete single-page Crystal quotation — Mark-Server format."""

    from docx.shared import Pt, Mm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.oxml.ns import qn

    # ─── Palette ───
    ACCENT = RGBColor(0xC8, 0x10, 0x2E)
    TEXT   = RGBColor(0x0F, 0x17, 0x20)
    MUTED  = RGBColor(0x7B, 0x85, 0x98)
    BLACK  = RGBColor(0x00, 0x00, 0x00)
    BG_HDR = "C2CEC2"        # grey-green header background
    RED    = "C8102E"

    # ─── Helpers ───
    def set_cell(cell, text, *, bold=False, size=9, color=TEXT,
                 align=WD_ALIGN_PARAGRAPH.LEFT, bg=None):
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = align
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        if bg:
            shd = OxmlElement("w:shd")
            shd.set(qn("w:fill"), bg)
            cell._tc.get_or_add_tcPr().append(shd)
        for i, line in enumerate(str(text).split("\n")):
            if i > 0:
                p.add_run().add_break()
            r = p.add_run(line)
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = color
            r.font.name = FONT

    def new_table(rows, cols, widths_mm=None):
        t = doc.add_table(rows=rows, cols=cols)
        t.style = "Table Grid"
        if widths_mm:
            for i, w in enumerate(widths_mm):
                for row in t.rows:
                    row.cells[i].width = Mm(w)
        return t

    def para(text="", *, size=9, bold=False, color=TEXT, align=WD_ALIGN_PARAGRAPH.LEFT,
             space_after=2, space_before=0):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.space_before = Pt(space_before)
        if text:
            r = p.add_run(str(text))
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = color
            r.font.name = FONT
        return p

    # ═══════════════════════════════════════════════════════════
    # 1. HEADER — logo (left) + Armatech block (right)
    # ═══════════════════════════════════════════════════════════
    hdr = new_table(1, 2, widths_mm=[70, 116])

    # Left: CRYSTAL (logo attempt)
    logo_path = None
    try:
        from quotation_generator_crystal import find_logo
        logo_path = find_logo()
    except Exception:
        pass

    left_cell = hdr.cell(0, 0)
    left_cell.text = ""
    lp = left_cell.paragraphs[0]
    if logo_path:
        try:
            from docx.shared import Mm as _Mm
            run = lp.add_run()
            run.add_picture(str(logo_path), width=_Mm(45))
        except Exception:
            r = lp.add_run("CRYSTAL")
            r.font.size = Pt(22); r.font.bold = True; r.font.color.rgb = ACCENT
    else:
        r = lp.add_run("CRYSTAL")
        r.font.size = Pt(22); r.font.bold = True; r.font.color.rgb = ACCENT
    para("", size=1, space_after=0)

    # Right: Armatech block
    right_cell = hdr.cell(0, 1)
    right_cell.text = ""
    rp = right_cell.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rp.paragraph_format.space_after = Pt(2)
    r = rp.add_run("ARMATECH ASSOCIATES")
    r.font.size = Pt(14); r.font.bold = True; r.font.color.rgb = ACCENT

    for line, sz, bd in [
        ("A Name With Magnetic Fame", 9, False),
        ("W-174A, 'S' BLOCK, BHOSARI, PUNE - 411026", 9, False),
        ("Mob No.: 7020991684    Email: armatech@gmail.com", 9, False),
    ]:
        p = right_cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(line)
        r.font.size = Pt(sz); r.font.bold = bd; r.font.color.rgb = TEXT

    # QUOTATION centered bar
    q_bar = new_table(1, 1)
    set_cell(q_bar.cell(0, 0), "QUOTATION", bold=True, size=12,
             align=WD_ALIGN_PARAGRAPH.CENTER, bg=BG_HDR)

    # ═══════════════════════════════════════════════════════════
    # 2. CUSTOMER (left) + META (right) — two columns
    # ═══════════════════════════════════════════════════════════
    block = new_table(1, 2, widths_mm=[100, 86])

    # ── Left: To / Customer ──
    lc = block.cell(0, 0)
    lc.text = ""
    p = lc.paragraphs[0]; p.paragraph_format.space_after = Pt(3)
    r = p.add_run("To")
    r.font.size = Pt(10); r.font.bold = True; r.font.color.rgb = BLACK

    cust = customer or {}
    buyer_lines = []
    if cust.get("company"):
        buyer_lines.append((cust["company"].upper(), True))
    if cust.get("contact_person"):
        buyer_lines.append((f"Attn: {cust['contact_person']}", False))
    if cust.get("address"):
        buyer_lines.append((cust["address"], False))
    city_line = " ".join(filter(None, [cust.get("city")]))
    if city_line:
        buyer_lines.append((city_line, False))
    state_line = " ".join(filter(None, [cust.get("state")]))
    if state_line:
        buyer_lines.append((state_line, False))
    pin = cust.get("pincode")
    if pin:
        buyer_lines.append((f"PIN: {pin}", False))
    if cust.get("phone"):
        buyer_lines.append((f"Phone: {cust['phone']}", False))
    if cust.get("email"):
        buyer_lines.append((f"Email: {cust['email']}", False))
    if cust.get("gstin"):
        buyer_lines.append((f"GSTIN: {cust['gstin']}", False))
    buyer_lines.append(("State Code : 27 Maharashtra", False))

    for line, bold in buyer_lines:
        p = lc.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(line)
        r.font.size = Pt(9); r.font.bold = bold; r.font.color.rgb = TEXT

    # ── Right: Quotation meta ──
    rc = block.cell(0, 1)
    rc.text = ""
    meta = [
        ("Quotation No.", str(quotation_number)),
        ("Quotation Date:", str(quotation_date)),
        ("Ref. No.", "BY MAIL"),
        ("Ref. Date:", str(quotation_date)),
        ("Cr Days", "0"),
    ]

    first = True
    for label, value in meta:
        if first:
            p = rc.paragraphs[0]
            first = False
        else:
            p = rc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r1 = p.add_run(f"{label}  ")
        r1.font.size = Pt(9); r1.font.bold = True; r1.font.color.rgb = TEXT
        r2 = p.add_run(value)
        r2.font.size = Pt(9); r2.font.color.rgb = TEXT

    # Kind Attn fallback chain:
    #   contact_person → customer_name → "Sir/Madam"
    attn_name = (
        cust.get("contact_person")
        or cust.get("name")
        or "Sir/Madam"
    ).strip()
    # Phone fallback: customer phone → "--"
    attn_phone = (cust.get("phone") or "--").strip()

    p = rc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    r = p.add_run(f"Kind Attn : {attn_name}   Mob.No. {attn_phone}")
    r.font.size = Pt(9); r.font.bold = True; r.font.color.rgb = BLACK

    # ═══════════════════════════════════════════════════════════
    # 3. GREETING + ACKNOWLEDGEMENT
    # ═══════════════════════════════════════════════════════════
    para("Dear Sir/Madam", size=9, space_after=4)
    para(
        "We acknowledge with thanks the receipt of your enquiry and have "
        "great pleasure in submitting our lowest quotation (Find Pdf Attachment).",
        size=9, space_after=6,
    )

    # ═══════════════════════════════════════════════════════════
    # 4. PRODUCT DETAILS — 9-column table
    # ═══════════════════════════════════════════════════════════
    pd_bar = new_table(1, 1)
    set_cell(pd_bar.cell(0, 0), "PRODUCT DETAILS", bold=True, size=10,
             align=WD_ALIGN_PARAGRAPH.CENTER, bg=BG_HDR)

    # Product table
    cols = ["Sr.", "Product Description", "HSN/SAC Code", "Tax %",
            "Quantity", "Units", "Rate", "Dis %", "Amount"]
    widths = [8, 60, 20, 12, 14, 12, 16, 10, 24]   # sum ~ 176 mm

    tbl = new_table(2, len(cols), widths_mm=widths)

    # Header row
    for i, (h, w) in enumerate(zip(cols, widths)):
        align = WD_ALIGN_PARAGRAPH.LEFT if i == 1 else (
            WD_ALIGN_PARAGRAPH.RIGHT if i in (2, 3, 4, 6, 7, 8) else WD_ALIGN_PARAGRAPH.LEFT
        )
        set_cell(tbl.cell(0, i), h, bold=True, size=8,
                 align=align, bg=BG_HDR)

    # Product row
    desc = (product or {}).get("description") or ""
    name = (product or {}).get("name") or ""
    model_str = str(model)

    # Prefer the description (it has full multi-line detail).
    # If missing, fall back to name.
    body = (desc or name).strip()

    full_desc = body
    if model_str and model_str not in body:
        full_desc = f"{body}\nModel: {model_str}"

    hsn = str((product or {}).get("hsn") or "85059000")
    tax_pct = (product or {}).get("tax_percent", 18.0)
    try:
        tax_str = f"{float(tax_pct):.2f}"
    except Exception:
        tax_str = "18.00"
    unit = str((product or {}).get("unit") or "NOS")
    qty_str = f"{float(machine_qty):g}"
    rate_str = f"{float(machine_price):,.2f}"
    disc = 0.0
    disc_str = f"{disc:g}" if disc else "0"
    amount = float(machine_price) * float(machine_qty) * (1 - disc / 100.0)
    amount_str = f"{amount:,.2f}"

    row_vals = ["1", full_desc, hsn, tax_str, qty_str, unit, rate_str, disc_str, amount_str]
    for i, v in enumerate(row_vals):
        align = WD_ALIGN_PARAGRAPH.LEFT if i == 1 else (
            WD_ALIGN_PARAGRAPH.RIGHT if i in (2, 3, 4, 6, 7, 8) else WD_ALIGN_PARAGRAPH.LEFT
        )
        set_cell(tbl.cell(1, i), v, size=8, align=align)

    # ═══════════════════════════════════════════════════════════
    # 5. TOTALS BLOCK — right-aligned
    # ═══════════════════════════════════════════════════════════
    t = totals or {}
    total_amt = amount      # single line for now

    gst_pct = 9.0
    cgst = total_amt * gst_pct / 100.0
    sgst = total_amt * gst_pct / 100.0
    pre_round = total_amt + cgst + sgst
    grand = round(pre_round)
    rounding = grand - pre_round

    tot_rows = [
        ("Total", f"{total_amt:,.2f}"),
        (f"C-Gst {gst_pct:g}%", f"{cgst:,.2f}"),
        (f"S-Gst {gst_pct:g}%", f"{sgst:,.2f}"),
        ("Rounding (+/-)", f"({abs(rounding):.2f})" if rounding else "0.00"),
    ]

    # Left side = amount-in-words, right side = totals rows
    tot_tbl = new_table(len(tot_rows) + 1, 2, widths_mm=[110, 66])

    # Amount in words (spans left column, all rows)
    aw_cell = tot_tbl.cell(0, 0)
    for i in range(1, len(tot_rows)):
        aw_cell = aw_cell.merge(tot_tbl.cell(i, 0))
    aw_text = f"Amount In Words :  {_amount_in_words_helper(grand)}"
    set_cell(aw_cell, aw_text, bold=False, size=8, align=WD_ALIGN_PARAGRAPH.LEFT)

    # Totals rows
    for i, (label, value) in enumerate(tot_rows):
        set_cell(tot_tbl.cell(i, 1), f"{label}    {value}", size=8,
                 align=WD_ALIGN_PARAGRAPH.RIGHT)

    # Grand total row (spans both cols)
    grand_row = new_table(1, 2, widths_mm=[110, 66])
    set_cell(grand_row.cell(0, 0), "", size=8, bg=BG_HDR)
    set_cell(grand_row.cell(0, 1), f"Grand Total    {grand:,.2f}",
             bold=True, size=9, align=WD_ALIGN_PARAGRAPH.RIGHT, bg=BG_HDR)

    # ═══════════════════════════════════════════════════════════
    # 6. SUBJECT LINE
    # ═══════════════════════════════════════════════════════════
    para('" Subject to Pune jurisdiction only "',
         size=9, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

    # ═══════════════════════════════════════════════════════════
    # 7. TERMS & CONDITIONS — 2-column table
    # ═══════════════════════════════════════════════════════════
    tc_bar = new_table(1, 1)
    set_cell(tc_bar.cell(0, 0), "Terms & Conditions :", bold=True, size=9,
             align=WD_ALIGN_PARAGRAPH.LEFT, bg=BG_HDR)

    terms = selected_terms or [
        {"title": "Delivery",          "value": "WITHIN 2-3 WEEKS"},
        {"title": "Payment",           "value": "50% ADVANCE AND BALANCE AGAINST PROFORMA INVOICE"},
        {"title": "Transport Charges", "value": "FREIGHT TO PAY BASIS"},
        {"title": "Validity",          "value": "15 DAYS"},
        {"title": "Warranty",          "value": "1 Year warranty from the date of purchase. Warranty applicable on manufacturing defects only."},
    ]

    terms_tbl = new_table(len(terms), 2, widths_mm=[50, 126])
    for i, term in enumerate(terms):
        title = term.get("title") or term.get("key") or ""
        value = term.get("value") or ""
        set_cell(terms_tbl.cell(i, 0), title, bold=True, size=8, bg=BG_HDR)
        set_cell(terms_tbl.cell(i, 1), value, size=8)

    # ═══════════════════════════════════════════════════════════
    # 8. FOOTER — GST TIN (left) + Signatory (right)
    # ═══════════════════════════════════════════════════════════
    foot = new_table(1, 2, widths_mm=[100, 86])

    set_cell(foot.cell(0, 0),
             "GST. TIN NO. : 27AACFA6934B1ZT W.E.F. : 01-07-2017\nState Code : 27 Maharashtra",
             bold=True, size=8)

    sig_cell = foot.cell(0, 1)
    sig_cell.text = ""
    for line, bd, sz in [
        ("For ARMATECH ASSOCIATES", True, 9),
        ("", False, 8),
        ("", False, 8),
        ("Authorised Signatory", True, 8),
        ("(Computer generated document no signature required)", False, 7),
    ]:
        p = sig_cell.add_paragraph() if sig_cell.paragraphs[0].text else sig_cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_after = Pt(1)
        if line:
            r = p.add_run(line)
            r.font.size = Pt(sz); r.font.bold = bd; r.font.color.rgb = TEXT

    # ═══════════════════════════════════════════════════════════
    # 9. BANK DETAILS + PLEASE FIND ATTACHED
    # ═══════════════════════════════════════════════════════════
    bank_bar = new_table(1, 1)
    set_cell(bank_bar.cell(0, 0), "Bank Account Details", bold=True, size=9,
             align=WD_ALIGN_PARAGRAPH.LEFT, bg=BG_HDR)

    bank_tbl = new_table(1, 1)
    set_cell(bank_tbl.cell(0, 0),
             "Bank Details:\n"
             "Name:HDFC BANK\n"
             "A/c.Name: ARMATECH ASSOCIATES\n"
             "A/c.No.: 01852320002300\n"
             "Branch: Nigdi\n"
             "IFSC: HDFC0000185",
             size=8)

    attach = new_table(1, 1)
    set_cell(attach.cell(0, 0),
             "Please Find Attached :\n1. Pdf Copy",
             size=8, align=WD_ALIGN_PARAGRAPH.CENTER, bg=BG_HDR)


# ─── helper used above ───
def _amount_in_words_helper(value):
    try:
        return amount_in_words(value)
    except Exception:
        return f"{float(value):,.2f} Rupees Only"


def generate_quotation(
    customer_name="",
    customer_company="",
    customer_address="",
    customer_phone="",
    customer_email="",

    # Compatibility with older UI
    company="",
    address="",
    phone="",
    email="",

    model="AA-9011M",

    machine_price=0,
    quantity=1,
    machine_qty=None,

    accessories=None,

    transportation=0,
    packing_percent=3.5,
    packing_mode="Percentage (%)",
    packing_value=None,
    cgst_percent=9,
    sgst_percent=9,

    quotation_date=None,

    generate_pdf=True,

    **kwargs,
):
    """
    Generate the complete six-page Word quotation.

    The function deliberately accepts both:

        customer_company
        customer_address
        customer_phone
        customer_email
        quantity

    and the older:

        company
        address
        phone
        email
        machine_qty

    interface.

    Returns a dictionary containing:
        path
        pdf_path
        quotation_number
        quotation_date
        model
        customer_name
        totals
    """

    # ========================================================
    # 1. NORMALIZE CUSTOMER DATA
    # ========================================================

    if not customer_company:
        customer_company = (
            company
            or kwargs.get(
                "customer_company",
                "",
            )
        )

    if not customer_address:
        customer_address = (
            address
            or kwargs.get(
                "customer_address",
                "",
            )
        )

    if not customer_phone:
        customer_phone = (
            phone
            or kwargs.get(
                "customer_phone",
                "",
            )
        )

    if not customer_email:
        customer_email = (
            email
            or kwargs.get(
                "customer_email",
                "",
            )
        )

    contact_person = str(
        kwargs.get("contact_person", "") or ""
    ).strip()
    city = str(kwargs.get("city", "") or "").strip()
    state = str(kwargs.get("state", "") or "").strip()
    pincode = str(kwargs.get("pincode", "") or "").strip()
    country = str(kwargs.get("country", "India") or "India").strip()
    gstin = str(kwargs.get("gstin", "") or "").strip().upper()

    if not customer_name:
        customer_name = kwargs.get(
            "customer_name",
            "",
        )

    # ========================================================
    # 2. NORMALIZE QUANTITY
    # ========================================================

    if machine_qty is None:
        machine_qty = kwargs.get(
            "machine_qty",
            kwargs.get(
                "quantity",
                quantity,
            ),
        )

    machine_qty = _decimal(
        machine_qty,
        Decimal("1"),
    )

    # ========================================================
    # 3. NORMALIZE PRICE
    # ========================================================

    if machine_price in (
        None,
        "",
    ):
        machine_price = kwargs.get(
            "unit_price",
            kwargs.get(
                "price",
                0,
            ),
        )

    machine_price = _decimal(
        machine_price
    )

    # ========================================================
    # 4. NORMALIZE COMMERCIAL VALUES
    # ========================================================

    transportation = _decimal(
        transportation
    )

    packing_percent = _decimal(
        packing_percent
    )

    packing_mode = str(
        kwargs.get("packing_mode", packing_mode)
        or "Percentage (%)"
    ).strip()

    packing_value = kwargs.get(
        "packing_value",
        packing_value,
    )

    if packing_value is None:
        packing_value = packing_percent
    else:
        packing_value = _decimal(packing_value)

    if packing_mode == "Amount (₹)":
        packing_percent = Decimal("0")
    elif packing_mode == "No Packing":
        packing_percent = Decimal("0")
        packing_value = Decimal("0")
    else:
        packing_mode = "Percentage (%)"
        packing_percent = packing_value

    cgst_percent = _decimal(
        cgst_percent
    )

    sgst_percent = _decimal(
        sgst_percent
    )

    gst_type = str(
        kwargs.get(
            "gst_type",
            "CGST + SGST",
        )
        or "CGST + SGST"
    ).strip()

    gst_rate = kwargs.get(
        "gst_rate",
        None,
    )

    igst_percent = kwargs.get(
        "igst_percent",
        0,
    )

    # ========================================================
    # 5. QUOTATION NUMBER
    # ========================================================

    quotation_number = (
        get_next_quotation_number()
    )

    # ========================================================
    # 6. DATE
    # ========================================================

    if quotation_date is None:
        quotation_date = datetime.now().strftime(
            "%d-%m-%Y"
        )

    elif isinstance(
        quotation_date,
        (
            date,
            datetime,
        ),
    ):
        quotation_date = quotation_date.strftime(
            "%d-%m-%Y"
        )

    else:
        quotation_date = str(
            quotation_date
        )

    # ========================================================
    # 7. CUSTOMER OBJECT
    # ========================================================

    customer = {
        "name": customer_name,
        "company": customer_company,
        "contact_person": contact_person,
        "address": customer_address,
        "city": city,
        "state": state,
        "pincode": pincode,
        "country": country,
        "gstin": gstin,
        "phone": customer_phone,
        "email": customer_email,
    }

    # ========================================================
    # 8. PRODUCT
    # ========================================================

    product = _resolve_product(
        model
    )

    # ========================================================
    # 9. CALCULATE TOTALS FIRST
    # ========================================================

    totals = calculate_totals(
        machine_price=machine_price,
        machine_qty=machine_qty,
        accessories=accessories,
        transportation=transportation,
        packing_percent=packing_percent,
        packing_mode=packing_mode,
        packing_value=packing_value,
        cgst_percent=cgst_percent,
        sgst_percent=sgst_percent,
        gst_type=gst_type,
        gst_rate=gst_rate,
        igst_percent=igst_percent,
    )

    # ========================================================
    # 10. CREATE WORD DOCUMENT
    # ========================================================

    doc = Document()

    section = doc.sections[0]

    section.top_margin = PAGE_MARGIN_TOP
    section.bottom_margin = PAGE_MARGIN_BOTTOM
    section.left_margin = PAGE_MARGIN_LEFT
    section.right_margin = PAGE_MARGIN_RIGHT

    # Default font
    normal = doc.styles["Normal"]

    normal.font.name = FONT
    normal.font.size = Pt(9)
    normal.font.color.rgb = BLACK

    # ========================================================
    # CRYSTAL — SINGLE-PAGE LAYOUT
    # ========================================================

    selected_terms = kwargs.get("selected_terms") or []

    # Remove keys we pass explicitly from kwargs to avoid duplicate
    # keyword-argument errors (e.g. selected_terms arriving twice).
    call_kwargs = dict(kwargs)
    for k in ("selected_terms", "customer", "product", "model",
              "quotation_number", "quotation_date"):
        call_kwargs.pop(k, None)

    _crystal_page(
        doc,
        quotation_number,
        quotation_date,
        customer,
        model,
        product,
        machine_price,
        machine_qty,
        totals,
        selected_terms=selected_terms,
        **call_kwargs,
    )

    # ========================================================
    # HEADER / FOOTER
    # ========================================================

    # Crystal draws its own logo in _crystal_page; skip the doc-level one
    _configure_sections(doc, include_logo=False)

    # ========================================================
    # OUTPUT DIRECTORY
    # ========================================================

    # Final destination folders (may be on network share)
    try:
        final_word_dir = get_word_dir()
    except Exception:
        final_word_dir = Path(QUOTATION_OUTPUT_DIR)
        final_word_dir.mkdir(parents=True, exist_ok=True)

    try:
        final_pdf_dir = get_pdf_dir()
    except Exception:
        final_pdf_dir = Path(QUOTATION_OUTPUT_DIR)
        final_pdf_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================
    # LOCAL STAGING FOLDER
    # ========================================================
    # We generate .docx and .pdf locally first (fast + reliable),
    # then copy to the final destination. This is critical when
    # the destination is a network share.

    local_dir = _local_temp_dir()

    # ========================================================
    # FILE NAME
    # ========================================================

    filename = (
        f"Quotation_"
        f"{_safe_filename(quotation_number)}_"
        f"{_safe_filename(model)}.docx"
    )

    local_docx = local_dir / filename

    # ========================================================
    # SAVE WORD FILE (locally)
    # ========================================================

    doc.save(str(local_docx))

    # ========================================================
    # COPY WORD FILE to final destination
    # ========================================================

    final_docx = final_word_dir / filename

    if not _safe_copy(local_docx, final_docx):
        # If copy fails, try to at least keep the local file
        print(f"[warn] Could not copy to {final_docx}")
        final_docx = local_docx
    else:
        print(f"[ok] Word saved -> {final_docx}")

    # ========================================================
    # OPTIONAL PDF (convert locally, then copy)
    # ========================================================

    pdf_path = None

    if generate_pdf:
        # Convert locally
        local_pdf = _convert_docx_to_pdf(local_docx)

        if local_pdf and local_pdf.is_file():
            final_pdf = final_pdf_dir / local_pdf.name

            if _safe_copy(local_pdf, final_pdf):
                pdf_path = final_pdf
                print(f"[ok] PDF saved -> {final_pdf}")
            else:
                print(f"[warn] Could not copy PDF to {final_pdf}")
                pdf_path = local_pdf
        else:
            print(f"[warn] PDF conversion failed for {local_docx}")

    output_path = final_docx

    # ========================================================
    # RETURN RESULT
    # ========================================================

    result = {
        "path": str(output_path),
        "docx_path": str(output_path),
        "pdf_path": (str(pdf_path) if pdf_path else None),
        "quotation_number": quotation_number,
        "quotation_date": quotation_date,
        "model": model,

        # ---- customer summary ----
        "customer_name":    customer_name,
        "customer_company": customer_company,

        # ---- full customer block ----
        "customer_phone":   (customer_phone or phone or ""),
        "customer_email":   (customer_email or email or ""),
        "customer_address": (customer_address or address or ""),
        "customer_city":    (kwargs.get("city") or ""),
        "customer_state":   (kwargs.get("state") or ""),
        "customer_pincode": (kwargs.get("pincode") or ""),
        "customer_gstin":   (kwargs.get("gstin") or ""),
        "contact_person":   (kwargs.get("contact_person") or ""),

        "totals": totals,
    }

    if _save_quotation_history is not None:
        try:
            _save_quotation_history(result)
        except Exception:
            pass

    return result


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    result = generate_quotation(
        customer_name="Test Customer",
        customer_company="Test Company",
        customer_address="Pune, Maharashtra",
        customer_phone="0000000000",
        customer_email="test@example.com",

        model="AA-9011M",

        machine_price=Decimal("100000"),
        quantity=1,

        accessories=[
            {
                "name": "Computer System",
                "code": "ACC-COMPUTER",
                "qty": 1,
                "price": Decimal("10000"),
                "enabled": True,
            }
        ],

        transportation=Decimal("5000"),
        packing_percent=Decimal("3.5"),
        cgst_percent=Decimal("9"),
        sgst_percent=Decimal("9"),

        generate_pdf=True,
    )

    print()
    print("=" * 70)
    print("CRYSTAL QUOTATION GENERATED SUCCESSFULLY")
    print("=" * 70)

    print(
        f"Offer No.: {result['quotation_number']}"
    )

    print(
        f"Model:     {result['model']}"
    )

    print(
        f"Word:      {result['docx_path']}"
    )

    print(
        f"PDF:       {result['pdf_path'] or 'PDF converter not available'}"
    )

    print(
        f"Grand:     {_money(result['totals']['grand_total'])}"
    )

    print("=" * 70)