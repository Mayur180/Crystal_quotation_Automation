# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# QUOTATION MANAGEMENT SYSTEM
#
# Modern quotation builder
#
# WORKFLOW:
#   1. Customer
#   2. Product
#   3. Pricing
#   4. Terms & Conditions
#   6. Generate
#
# File:
#   ui/quotation_form.py
# ============================================================

import os
import sys
import json
import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from decimal import Decimal, InvalidOperation

# Pillow is optional: it is only used to scale the preview image.
# Importing it lazily keeps the form usable on machines where it
# is not installed.
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.crystal import theme as T
from ui.crystal import widgets as W
from ui.crystal.terms_editor import TermsEditor


# ============================================================
# PROJECT IMPORTS
# ============================================================

try:
    from app.services.catalog_service import (
        get_product_categories,
        get_products_by_category,
        get_product,
    )
except Exception:
    get_product_categories = None
    get_products_by_category = None
    get_product = None
try:
    from quotation_generator_crystal import generate_quotation
except Exception:
    generate_quotation = None


try:
    from app.services.states_service import (
        get_state_by_city,
        resolve_state,
    )
except Exception:
    get_state_by_city = None
    resolve_state = None


# ============================================================
# CUSTOMER LOCATION / GST HELPERS
# ============================================================

INDIAN_STATES = sorted(
    [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
        "Chhattisgarh", "Goa", "Gujarat", "Haryana",
        "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
        "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
        "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
        "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
        "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Andaman and Nicobar Islands", "Chandigarh",
        "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
        "Jammu and Kashmir", "Ladakh", "Lakshadweep",
        "Puducherry",
    ],
    key=str.casefold,
)

STATE_GST_CODES = {
    "Andhra Pradesh": "37", "Arunachal Pradesh": "12", "Assam": "18",
    "Bihar": "10", "Chhattisgarh": "22", "Goa": "30",
    "Gujarat": "24", "Haryana": "06", "Himachal Pradesh": "02",
    "Jharkhand": "20", "Karnataka": "29", "Kerala": "32",
    "Madhya Pradesh": "23", "Maharashtra": "27", "Manipur": "14",
    "Meghalaya": "17", "Mizoram": "15", "Nagaland": "13",
    "Odisha": "21", "Punjab": "03", "Rajasthan": "08",
    "Sikkim": "11", "Tamil Nadu": "33", "Telangana": "36",
    "Tripura": "16", "Uttar Pradesh": "09", "Uttarakhand": "05",
    "West Bengal": "19", "Andaman and Nicobar Islands": "35",
    "Chandigarh": "04",
    "Dadra and Nagar Haveli and Daman and Diu": "26",
    "Delhi": "07", "Jammu and Kashmir": "01", "Ladakh": "38",
    "Lakshadweep": "31", "Puducherry": "34",
}


# ============================================================
# FALLBACK CATALOG
# ============================================================

def _get_fallback_categories():
    """Return VMM fallback categories ONLY when VMM module is active.
    Crystal module gets NO fallback (user must add real products)."""
    try:
        from app.services import paths as _paths
        if _paths.get_active_module() == "VMM":
            return [
                "Manual VMM",
                "Semi Automatic VMM",
                "Fully Automatic VMM",
                "Automatic VMM with Cabinet",
                "VMS",
            ]
    except Exception:
        pass
    return []


FALLBACK_CATEGORIES = _get_fallback_categories()


# Canonical Crystal categories — always offered in the dropdown,
# merged with whatever the catalog actually contains.
CANONICAL_CRYSTAL_CATEGORIES = [
    "MAGNETIC",
    "NON-MAGNETIC",
    "REPAIRING AND RECONDITIONING",
]


FALLBACK_MODELS = {

    "Manual VMM": [
        "AA-9011M",
        "AA-9012M",
        "AA-9013M",
    ],

    "Semi Automatic VMM": [
        "AA-9021SA",
        "AA-9022SA",
        "AA-9023SA",
    ],

    "Fully Automatic VMM": [
        "AA-9031A",
        "AA-9032A",
        "AA-9033A",
    ],

    "Automatic VMM with Cabinet": [
        "AA-9041AC",
        "AA-9042AC",
        "AA-9043AC",
        "AA-9044AC",
    ],

    "VMS": [
        "AA-9051V",
        "AA-9052V",
        "AA-9053V",
    ],
}


# ============================================================
# MODEL SIZE
# ============================================================

MODEL_SIZE = {

    "AA-9011M": "200 × 100 × 150 mm",
    "AA-9012M": "300 × 200 × 200 mm",
    "AA-9013M": "400 × 300 × 200 mm",

    "AA-9021SA": "200 × 100 × 150 mm",
    "AA-9022SA": "300 × 200 × 200 mm",
    "AA-9023SA": "400 × 300 × 200 mm",

    "AA-9031A": "200 × 200 × 200 mm",
    "AA-9032A": "300 × 200 × 200 mm",
    "AA-9033A": "400 × 300 × 200 mm",

    "AA-9041AC": "300 × 200 × 200 mm",
    "AA-9042AC": "400 × 300 × 200 mm",
    "AA-9043AC": "500 × 400 × 200 mm",
    "AA-9044AC": "600 × 500 × 200 mm",

    "AA-9051V": "200 × 100 × 150 mm",
    "AA-9052V": "300 × 200 × 200 mm",
    "AA-9053V": "400 × 300 × 200 mm",
}




# ============================================================
# STANDARD TERMS
# ============================================================

STANDARD_TERMS = [
    ("Delivery",
     "WITHIN 2-3 WEEKS"),
    ("Payment",
     "50% ADVANCE AND BALANCE AGAINST PROFORMA INVOICE"),
    ("Transport Charges",
     "FREIGHT TO PAY BASIS"),
    ("Validity",
     "15 DAYS"),
    ("Warranty",
     "1 Year warranty from the date of purchase. Warranty applicable on manufacturing defects only."),
]


# ============================================================
# TERMS PERSISTENCE FILE
# ============================================================

# Module-aware terms file:
#   Crystal → data/Crystal/custom_terms.json
#   VMM     → data/VMM/custom_terms.json
try:
    from app.services.paths import get_data_dir
    TERMS_FILE = str(get_data_dir() / "custom_terms.json")
except Exception:
    TERMS_FILE = os.path.join(
        PROJECT_ROOT,
        "data",
        "custom_terms.json",
    )


# ============================================================
# MAIN WINDOW
# ============================================================

class QuotationForm(tk.Toplevel):

    # ========================================================
    # COLORS
    # ========================================================

    BG = T.BG
    CARD = T.SURFACE

    TEXT = T.TEXT
    MUTED = T.TEXT_MUTED
    LIGHT_MUTED = T.TEXT_FAINT

    BORDER = T.BORDER

    RED = T.ACCENT
    RED_DARK = T.ACCENT_DARK
    RED_LIGHT = T.ACCENT_SOFT

    GREEN = T.SUCCESS
    GREEN_LIGHT = T.SUCCESS_BG

    SOFT = T.SURFACE_ALT


    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, app=None, parent=None, prefill=None, revision_number=None,
                 doc_type="quotation"):

        super().__init__(parent or app)

        self.app = app

        self._revision_number = (
            str(revision_number).strip() if revision_number else None
        )

        self._initial_doc_type = (
            "proforma"
            if str(doc_type or "").strip().lower().startswith("prof")
            else "quotation"
        )

        if self._revision_number:
            try:
                from app.services.quotation_number_service import split_revision
                _base, _rev = split_revision(self._revision_number)
            except Exception:
                _base, _rev = self._revision_number, 1
            self.title(
                f"CRYSTAL | ARMATECH ASSOCIATES — Revise {_base} (R{_rev})"
            )
        else:
            self.title(
                "CRYSTAL | ARMATECH ASSOCIATES — New "
                + ("Proforma Invoice" if self._initial_doc_type == "proforma"
                   else "Quotation")
            )

        # ---- Adaptive window size ----
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
        except Exception:
            screen_w, screen_h = 1366, 768

        usable_w = min(1500, max(1000, screen_w - 80))
        usable_h = min(900, max(650, screen_h - 100))

        x = max(0, (screen_w - usable_w) // 2)
        y = max(0, (screen_h - usable_h) // 2 - 20)

        self.geometry(f"{usable_w}x{usable_h}+{x}+{y}")
        self.minsize(1180, 720)

        self.configure(
            bg=self.BG
        )

        try:
            W.set_window_icon(self)
        except Exception:
            pass

        self.current_step = 1
        self._prefill = prefill or {}

        self.completed_steps = set()
        self.items = []
        self.term_rows = []

        # Custom terms loaded from disk
        self.custom_terms = self._load_terms()

        self._create_variables()

        self._configure_style()

        self._build_interface()

        # initial render on Customer page
        self._load_step(1)

        # apply duplicate/customer prefill AFTER initial render
        # (this may jump to Step 2)
        try:
            self._apply_prefill(getattr(self, "_prefill", {}))
        except Exception:
            pass

        if self._initial_doc_type == "proforma":
            try:
                self._set_doc_type("proforma")
            except Exception:
                pass


    # ========================================================
    # TERMS PERSISTENCE
    # ========================================================

    def _load_terms(self):
        """Load custom terms from disk, fall back to STANDARD_TERMS."""

        try:

            if os.path.isfile(TERMS_FILE):

                with open(
                    TERMS_FILE,
                    "r",
                    encoding="utf-8"
                ) as handle:

                    data = json.load(handle)

                # Shape A — list of {"title": ..., "value": ...}
                if isinstance(data, list) and data:

                    result = []

                    for item in data:

                        if isinstance(item, dict):

                            title = str(
                                item.get("title", "")
                            ).strip()

                            value = str(
                                item.get("value", "")
                            ).strip()

                            if title and value:

                                result.append(
                                    (title, value)
                                )

                    if result:
                        return result

                # Shape B — {"terms": {"Delivery": "...", ...}}
                if isinstance(data, dict) and "terms" in data:

                    terms_dict = data.get("terms") or {}

                    if isinstance(terms_dict, dict):

                        result = []

                        for title, value in terms_dict.items():

                            t = str(title).strip()
                            v = str(value).strip()

                            if t and v:

                                result.append((t, v))

                        if result:
                            return result

        except Exception:
            pass

        return [
            (title, value)
            for title, value in STANDARD_TERMS
        ]


    def _save_terms(self):
        """Persist custom terms to disk."""

        try:

            os.makedirs(
                os.path.dirname(TERMS_FILE),
                exist_ok=True
            )

            payload = [

                {
                    "title": title,
                    "value": value,
                }

                for title, value in self.custom_terms
            ]

            with open(
                TERMS_FILE,
                "w",
                encoding="utf-8"
            ) as handle:

                json.dump(
                    payload,
                    handle,
                    indent=2,
                    ensure_ascii=False
                )

            return True

        except Exception as exc:

            messagebox.showerror(
                "Could not save terms",
                (
                    "The terms could not be saved.\n\n"
                    f"{type(exc).__name__}: {exc}"
                ),
                parent=self
            )

            return False


    # ========================================================
    # VARIABLES
    # ========================================================

    def _create_variables(self):

        # Document type: quotation or proforma invoice (own PI/26-27/NNN series)
        self.doc_type = tk.StringVar(value="quotation")

        # Customer
        self.customer_name = tk.StringVar()
        self.company = tk.StringVar()
        self.contact_person = tk.StringVar()
        self.address = tk.StringVar()
        self.city = tk.StringVar()
        self.state = tk.StringVar()
        self.pincode = tk.StringVar()
        self.country = tk.StringVar(value="India")
        self.phone = tk.StringVar()
        self.email = tk.StringVar()
        self.gstin = tk.StringVar()

        # Product
        self.category = tk.StringVar()
        self.model = tk.StringVar()
        self.machine_price = tk.StringVar()
        self.update_catalog = tk.BooleanVar(value=False)
        self.machine_qty = tk.StringVar(value="1")

        # Commercial
        self.transportation = tk.StringVar(value="0")
        self.buyback = tk.StringVar(value="0")

        # Packing can be entered either as a percentage of the
        # Machine subtotal or as a fixed amount.
        self.packing_mode = tk.StringVar(value="Percentage (%)")
        self.packing_value = tk.StringVar(value="3.5")

        # Compatibility variable retained for older generator calls.
        self.packing_percent = tk.StringVar(value="3.5")

        # Manual GST selection.
        # The user explicitly chooses the tax treatment for each quotation.
        if not hasattr(self, "gst_type"):
            self.gst_type = tk.StringVar(value="CGST + SGST")
        self.gst_rate = tk.StringVar(value="18")

        # Compatibility variables retained for the existing generator.
        # They are kept synchronized from gst_type + gst_rate before
        # preview/generation.
        self.cgst_percent = tk.StringVar(value="9")
        self.sgst_percent = tk.StringVar(value="9")

        # Terms
        self.include_terms = tk.BooleanVar(value=False)

        # Product display
        self.product_title = tk.StringVar(
            value="Select a machine"
        )

        self.product_subtitle = tk.StringVar(
            value=""
        )

        # Summary
        self.summary_values = {}

        for key in [
            "subtotal",
            "packing",
            "transportation",
            "buyback",
            "taxable",
            "cgst",
            "sgst",
            "igst",
            "gst",
            "grand",
        ]:
            self.summary_values[key] = tk.StringVar(
                value="₹ 0.00"
            )

        # Status
        self.status_text = tk.StringVar(
            value="Complete customer details to continue."
        )


    # ========================================================
    # STYLE
    # ========================================================

    def _configure_style(self):

        W.apply_ttk_theme(self)

        style = ttk.Style(self)

        style.configure(
            "Crystal.TCombobox",
            fieldbackground=T.SURFACE,
            background=T.SURFACE,
            foreground=self.TEXT,
            bordercolor=T.BORDER,
            lightcolor=T.BORDER,
            darkcolor=T.BORDER,
            arrowcolor=T.TEXT_MUTED,
            padding=(10, 6),
            font=T.FONT_BODY,
        )

        style.map(
            "Crystal.TCombobox",
            fieldbackground=[
                ("readonly", T.SURFACE)
            ],
            foreground=[
                ("readonly", self.TEXT)
            ],
            bordercolor=[
                ("focus", T.FOCUS),
                ("active", T.BORDER_HARD),
            ],
            lightcolor=[
                ("focus", T.FOCUS),
            ],
            darkcolor=[
                ("focus", T.FOCUS),
            ],
        )


    # ========================================================
    # MAIN INTERFACE
    # ========================================================

    def _build_interface(self):

        self._build_header()

        self._build_stepper()

        self._build_navigation_bar()

        body = tk.Frame(
            self,
            bg=self.BG
        )

        body.pack(
            fill="both",
            expand=True
        )

        self.left_area = tk.Frame(
            body,
            bg=self.BG
        )

        self.left_area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(26, 12),
            pady=16
        )

        self.right_area = tk.Frame(
            body,
            bg=self.BG,
            width=350
        )

        self.right_area.pack_forget()

        self.right_area.pack_propagate(False)

        self.content_container = tk.Frame(
            self.left_area,
            bg=self.BG
        )

        self.content_container.pack(
            fill="both",
            expand=True
        )

        self.canvas = tk.Canvas(
            self.content_container,
            bg=self.BG,
            highlightthickness=0,
            bd=0
        )

        self.scrollbar = ttk.Scrollbar(
            self.content_container,
            orient="vertical",
            command=self.canvas.yview
        )

        self.content_area = tk.Frame(
            self.canvas,
            bg=self.BG
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content_area,
            anchor="nw"
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.scrollbar.pack(
            side="right",
            fill="y"
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.content_area.bind(
            "<Configure>",
            self._update_scroll_region
        )

        self.canvas.bind(
            "<Configure>",
            self._resize_canvas_content
        )

        # Wheel is routed through the shared ScrollManager so the
        # preview / customer DB windows don't steal wheel events.
        try:
            from ui.common.scroll_manager import ScrollManager
            ScrollManager.register(self.canvas, "vertical")
        except Exception:
            # Fallback: bind locally if the manager can't load
            self.canvas.bind("<MouseWheel>", self._mousewheel)

        # Keep PgUp / PgDn as window-scoped bindings
        self.bind("<Prior>",
                  lambda e: self.canvas.yview_scroll(-8, "units"))
        self.bind("<Next>",
                  lambda e: self.canvas.yview_scroll(8, "units"))

        self._build_summary_panel()


    # ========================================================
    # SCROLL SUPPORT
    # ========================================================

    def _update_scroll_region(self, event=None):

        try:
            self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        except Exception:
            pass


    def _resize_canvas_content(self, event=None):

        try:

            self.canvas.itemconfigure(
                self.canvas_window,
                width=event.width
            )

        except Exception:
            pass


    def _mousewheel(self, event):
        """Scroll the main quotation canvas for mouse and laptop touchpad input."""
        try:
            if not self.winfo_exists() or not self.canvas.winfo_exists():
                return

            # Ignore events belonging to a child Toplevel such as TermsEditor.
            if event.widget.winfo_toplevel() is not self:
                return

            delta = getattr(event, "delta", 0)
            if delta:
                # Windows mouse wheel and Windows precision touchpads both
                # normally arrive here as <MouseWheel>. Use sign rather than
                # assuming a fixed 120-step delta so touchpad scrolling works.
                amount = -1 if delta > 0 else 1
                magnitude = max(1, min(6, int(abs(delta) / 120)))
                self.canvas.yview_scroll(amount * magnitude, "units")
        except Exception:
            pass

    def _mousewheel_up(self, event):
        try:
            if event.widget.winfo_toplevel() is self:
                self.canvas.yview_scroll(-3, "units")
        except Exception:
            pass

    def _mousewheel_down(self, event):
        try:
            if event.widget.winfo_toplevel() is self:
                self.canvas.yview_scroll(3, "units")
        except Exception:
            pass


    # ========================================================
    # HEADER
    # ========================================================

    def _build_header(self):

        header = tk.Frame(
            self,
            bg=self.CARD,
            height=78
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        tk.Frame(
            header,
            bg=self.RED,
            height=3
        ).pack(
            side="bottom",
            fill="x"
        )

        brand = tk.Frame(
            header,
            bg=self.CARD
        )

        brand.pack(
            side="left",
            padx=28
        )

        tk.Label(
            brand,
            text="CRYSTAL",
            bg=self.CARD,
            fg=self.RED,
            font=T.FONT_H1
        ).pack(
            side="left",
            pady=15
        )

        self.header_sub_label = tk.Label(
            brand,
            text=self._header_subtitle(),
            bg=self.CARD,
            fg=self.MUTED,
            font=T.FONT_BODY
        )

        self.header_sub_label.pack(
            side="left",
            pady=19
        )

        company = tk.Frame(
            header,
            bg=self.CARD
        )

        company.pack(
            side="right",
            padx=28
        )

        tk.Label(
            company,
            text="ARMATECH ASSOCIATES",
            bg=self.CARD,
            fg=self.TEXT,
            font=T.FONT_H3
        ).pack(
            anchor="e",
            pady=(13, 1)
        )

        try:
            from ui.themes import get_tagline
            from app.services import paths as _paths
            _form_tagline = get_tagline(_paths.get_active_module())
        except Exception:
            _form_tagline = "Precision Measurement Technology"

        tk.Label(
            company,
            text=_form_tagline,
            bg=self.CARD,
            fg=self.MUTED,
            font=T.FONT_SMALL
        ).pack(
            anchor="e"
        )


    def _header_subtitle(self):
        """Header strip text — shows the revision link when revising."""
        if not self._revision_number:
            return f"  /  New {self._doc_label()}"
        try:
            from app.services.quotation_number_service import split_revision
            base, rev = split_revision(self._revision_number)
        except Exception:
            base, rev = self._revision_number, 1
        return f"  /  Revising {base} → R{rev}"

    def _doc_label(self):
        """Human label for the current document type."""
        try:
            is_pi = self.doc_type.get() == "proforma"
        except Exception:
            is_pi = False
        return "Proforma Invoice" if is_pi else "Quotation"

    def _set_doc_type(self, value):
        """Switch between Quotation and Proforma Invoice on step 1."""
        if self._revision_number:
            # Revisions always remain quotations.
            value = "quotation"
        self.doc_type.set("proforma" if value == "proforma" else "quotation")
        self._refresh_doc_type_buttons()
        try:
            self.title(
                f"CRYSTAL | ARMATECH ASSOCIATES — New {self._doc_label()}"
            )
        except Exception:
            pass
        try:
            self.header_sub_label.configure(text=self._header_subtitle())
        except Exception:
            pass

    def _refresh_doc_type_buttons(self):
        current = self.doc_type.get() if hasattr(self, "doc_type") else "quotation"
        for value, btn in getattr(self, "_doc_type_buttons", {}).items():
            try:
                if value == current:
                    btn.configure(bg=self.RED, fg="white",
                                  activebackground=self.RED_DARK,
                                  activeforeground="white",
                                  highlightbackground=self.RED)
                else:
                    btn.configure(bg=T.SURFACE_ALT, fg=T.TEXT_BODY,
                                  activebackground=T.SURFACE_HOVER,
                                  activeforeground=self.TEXT,
                                  highlightbackground=self.BORDER)
            except Exception:
                pass


    # ========================================================
    # STEPPER
    # ========================================================

    def _build_stepper(self):

        self.stepper = tk.Frame(
            self,
            bg=self.CARD,
            height=76,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        self.stepper.pack(
            fill="x"
        )

        self.stepper.pack_propagate(False)

        inner = tk.Frame(
            self.stepper,
            bg=self.CARD
        )

        inner.pack(
            fill="x",
            padx=28,
            pady=14
        )

        steps = [
            (1, "Customer", "Buyer details"),
            (2, "Product", "Select machine"),
            (3, "Pricing", "Final amount"),
            (4, "Terms", "Conditions"),
        ]

        self.step_widgets = []

        for index, (
            number,
            title,
            subtitle
        ) in enumerate(steps):

            holder = tk.Frame(
                inner,
                bg=self.CARD
            )

            holder.pack(
                side="left",
                fill="x",
                expand=True
            )

            circle = tk.Label(
                holder,
                text=str(number),
                bg=T.NEUTRAL_BG,
                fg=T.TEXT_MUTED,
                width=2,
                height=1,
                padx=4,
                pady=4,
                font=T.FONT_BODY_B
            )

            circle.pack(
                side="left"
            )

            text_box = tk.Frame(
                holder,
                bg=self.CARD
            )

            text_box.pack(
                side="left",
                padx=10
            )

            title_label = tk.Label(
                text_box,
                text=title,
                bg=self.CARD,
                fg=self.MUTED,
                font=T.FONT_BODY_B
            )

            title_label.pack(
                anchor="w"
            )

            subtitle_label = tk.Label(
                text_box,
                text=subtitle,
                bg=self.CARD,
                fg=self.LIGHT_MUTED,
                font=T.FONT_TINY
            )

            subtitle_label.pack(
                anchor="w"
            )

            self.step_widgets.append(
                (
                    circle,
                    title_label,
                    subtitle_label
                )
            )

            if index < len(steps) - 1:

                tk.Frame(
                    inner,
                    bg=T.BORDER,
                    height=1
                ).pack(
                    side="left",
                    fill="x",
                    expand=True,
                    padx=14
                )


    # ========================================================
    # CARD
    # ========================================================

    def _create_card(
        self,
        parent,
        padding=22
    ):

        outer = tk.Frame(
            parent,
            bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        outer.pack(
            fill="x",
            pady=(0, 14)
        )

        inner = tk.Frame(
            outer,
            bg=self.CARD
        )

        inner.pack(
            fill="both",
            expand=True,
            padx=padding,
            pady=padding
        )

        return inner


    # ========================================================
    # SECTION HEADER
    # ========================================================

    def _section_header(
        self,
        parent,
        number,
        title,
        subtitle
    ):

        row = tk.Frame(
            parent,
            bg=self.CARD
        )

        row.pack(
            fill="x",
            pady=(0, 20)
        )

        tk.Label(
            row,
            text=str(number),
            bg=self.RED,
            fg="white",
            width=2,
            height=1,
            padx=4,
            pady=4,
            font=T.FONT_LABEL
        ).pack(
            side="left",
            padx=(0, 12)
        )

        text_box = tk.Frame(
            row,
            bg=self.CARD
        )

        text_box.pack(
            side="left"
        )

        tk.Label(
            text_box,
            text=title,
            bg=self.CARD,
            fg=self.TEXT,
            font=T.FONT_H2
        ).pack(
            anchor="w"
        )

        tk.Label(
            text_box,
            text=subtitle,
            bg=self.CARD,
            fg=self.MUTED,
            font=T.FONT_SMALL
        ).pack(
            anchor="w",
            pady=(2, 0)
        )


    # ========================================================
    # ENTRY
    # ========================================================

    def _make_entry(
        self,
        parent,
        label,
        variable,
        required=False
    ):

        box = tk.Frame(
            parent,
            bg=self.CARD
        )

        label_text = label.upper()

        if required:
            label_text += "  *"

        tk.Label(
            box,
            text=label_text,
            bg=self.CARD,
            fg=T.TEXT_MUTED,
            font=T.FONT_LABEL
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        entry = tk.Entry(
            box,
            textvariable=variable,
            bg=T.SURFACE,
            fg=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.BORDER,
            highlightcolor=T.FOCUS,
            font=T.FONT_BODY,
            insertbackground=self.RED
        )

        entry.pack(
            fill="x",
            ipady=6
        )

        box.entry = entry

        return box


    # ========================================================
    # STEP 1 — CUSTOMER
    # ========================================================

    def _render_customer(self):

        self._clear_content()

        card = self._create_card(
            self.content_area
        )

        # ---- Document type: Quotation or Proforma Invoice ----
        type_bar = tk.Frame(card, bg=self.CARD)
        type_bar.pack(fill="x", pady=(0, 16))

        tk.Label(
            type_bar, text="DOCUMENT TYPE",
            bg=self.CARD, fg=T.TEXT_MUTED, font=T.FONT_LABEL
        ).pack(side="left", padx=(0, 12))

        self._doc_type_buttons = {}
        for value, label in (("quotation", "Quotation"),
                             ("proforma", "Proforma Invoice")):
            btn = tk.Button(
                type_bar, text=label,
                font=T.FONT_LABEL, relief="flat", bd=0,
                highlightthickness=1,
                highlightbackground=self.BORDER,
                highlightcolor=self.BORDER,
                cursor="hand2", padx=16, pady=5,
                command=lambda v=value: self._set_doc_type(v),
            )
            if self._revision_number and value == "proforma":
                btn.configure(state="disabled")
            btn.pack(side="left", padx=(0, 8))
            self._doc_type_buttons[value] = btn
        self._refresh_doc_type_buttons()

        self._section_header(
            card,
            1,
            "Customer details",
            "Enter the complete buyer information for the quotation."
        )

        grid = tk.Frame(
            card,
            bg=self.CARD
        )

        grid.pack(
            fill="x"
        )

        for column in (0, 1):
            grid.grid_columnconfigure(column, weight=1)

        # Customer name + saved customer lookup
        name_box = tk.Frame(grid, bg=self.CARD)
        name_box.grid(
            row=0, column=0, sticky="ew",
            padx=(0, 10), pady=7
        )

        label_row = tk.Frame(name_box, bg=self.CARD)
        label_row.pack(fill="x", pady=(0, 6))

        tk.Label(
            label_row, text="CUSTOMER NAME",
            bg=self.CARD, fg=T.TEXT_MUTED,
            font=T.FONT_LABEL
        ).pack(side="left")

        tk.Button(
            label_row,
            text="Lookup saved",
            command=self._open_customer_lookup,
            bg=T.SURFACE_ALT, fg=T.TEXT_BODY,
            activebackground=T.SURFACE_HOVER, activeforeground=self.TEXT,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=self.BORDER, highlightcolor=T.FOCUS,
            font=T.FONT_LABEL, cursor="hand2",
            padx=10, pady=1,
        ).pack(side="right")

        self.customer_name_entry = tk.Entry(
            name_box, textvariable=self.customer_name,
            bg=T.SURFACE, fg=self.TEXT, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=self.BORDER,
            highlightcolor=T.FOCUS,
            font=T.FONT_BODY, insertbackground=self.RED,
        )
        self.customer_name_entry.pack(fill="x", ipady=6)

        self._make_entry(
            grid, "Company", self.company, True
        ).grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=7)

        self._make_entry(
            grid, "Contact person", self.contact_person, False
        ).grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=7)

        self._make_entry(
            grid, "Phone", self.phone, False
        ).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=7)

        self._make_entry(
            grid, "Email", self.email, False
        ).grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=7)

        self._make_entry(
            grid, "GSTIN", self.gstin, False
        ).grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=7)

        self._make_entry(
            grid, "Address / Location", self.address, False
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=7)

        city_entry = self._make_entry(
            grid, "City", self.city, False
        )

        city_entry.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=(0, 10),
            pady=7
        )

        # Automatically detect state from a known city.
        city_entry.entry.bind(
            "<KeyRelease>",
            self._auto_fill_state_from_city,
            add="+"
        )

        state_box = tk.Frame(grid, bg=self.CARD)
        state_box.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=7)

        tk.Label(
            state_box, text="STATE",
            bg=self.CARD, fg=T.TEXT_MUTED,
            font=T.FONT_LABEL
        ).pack(anchor="w", pady=(0, 6))

        state_combo = ttk.Combobox(
            state_box,
            textvariable=self.state,
            values=INDIAN_STATES,
            state="normal",
            style="Crystal.TCombobox"
        )
        state_combo.pack(fill="x", ipady=2)

        self.state_combo = state_combo

        # Allow state abbreviations such as MH, KA, GJ, TN, etc.
        state_combo.bind(
            "<KeyRelease>",
            self._auto_fill_state_from_text,
            add="+"
        )

        state_combo.bind(
            "<<ComboboxSelected>>",
            self._normalize_selected_state,
            add="+"
        )

        self._make_entry(
            grid, "Pincode", self.pincode, False
        ).grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=7)

        self._make_entry(
            grid, "Country", self.country, False
        ).grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=7)

        note = tk.Frame(
            card, bg=T.ACCENT_SOFT
        )
        note.pack(fill="x", pady=(15, 0))

        tk.Frame(
            note, bg=self.RED, width=3
        ).pack(side="left", fill="y")

        tk.Label(
            note,
            text="* Required field  •  GSTIN is optional for non-GST customers, but must be valid when entered.",
            bg=T.ACCENT_SOFT, fg=T.ACCENT_DARK,
            font=T.FONT_SMALL
        ).pack(anchor="w", padx=14, pady=10)

        self.status_text.set(
            "Complete customer details to continue."
        )


    # ========================================================
    # CUSTOMER LOCATION AUTO-FILL
    # ========================================================

    def _auto_fill_state_from_city(self, event=None):
        """Automatically select a state when a known city is entered."""
        if get_state_by_city is None:
            return
        city = self.city.get().strip()
        if not city:
            return
        state = get_state_by_city(city)
        if state:
            self.state.set(state)

    def _auto_fill_state_from_text(self, event=None):
        """Resolve a typed state abbreviation or full state name."""
        if resolve_state is None:
            return
        value = self.state.get().strip()
        if not value:
            return
        state = resolve_state(value)
        if state and self.state.get() != state:
            self.state.set(state)

    def _normalize_selected_state(self, event=None):
        """Normalize a state selected from the combobox."""
        if resolve_state is None:
            return
        value = self.state.get().strip()
        if not value:
            return
        state = resolve_state(value)
        if state:
            self.state.set(state)


    # ========================================================
    # CUSTOMER VALIDATION
    # ========================================================

    def _validate_customer(self):
        """Only COMPANY is required."""
        company = (self.company.get() or "").strip()
        if not company:
            messagebox.showerror(
                "Company required",
                "Please enter the company name.",
                parent=self,
            )
            return False
        return True


    def _render_product(self):
        self._clear_content()
        card = self._create_card(self.content_area)
        self._section_header(card, 2, "Choose your machine", "Add machines to the quotation.")

        # --- 2-Column Layout (Left: Inputs, Right: Info) ---
        main_layout = tk.Frame(card, bg=self.CARD)
        main_layout.pack(fill="both", expand=True, pady=10)
        
        # Left Column (Inputs)
        top = tk.Frame(main_layout, bg=self.CARD)
        top.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # Right Column (Product Info Panel)
        self.info_panel = tk.Frame(main_layout, bg=T.SURFACE_ALT, highlightbackground=self.BORDER, highlightthickness=1, width=330)
        self.info_panel.pack(side="right", fill="y", expand=False)
        self.info_panel.pack_propagate(False)
        
        # Info Panel Header
        tk.Label(
            self.info_panel, text="PRODUCT INFORMATION",
            bg=T.SURFACE_ALT, fg=T.TEXT_MUTED, font=T.FONT_LABEL,
            anchor="w", padx=14, pady=12
        ).pack(fill="x")
        tk.Frame(self.info_panel, bg=self.BORDER, height=1).pack(fill="x")
        
        # Scrollable Text Area
        text_frame = tk.Frame(self.info_panel, bg=T.SURFACE_ALT)
        text_frame.pack(fill="both", expand=True, padx=14, pady=12)
        
        self.info_text = tk.Text(text_frame, bg=T.SURFACE_ALT, fg=T.TEXT_BODY, font=T.FONT_SMALL, wrap="word", relief="flat", highlightthickness=0, bd=0, height=15)
        self.info_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.info_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.info_text.configure(yscrollcommand=scrollbar.set)
        self.info_text.insert("1.0", "Select a model to see its details here.")
        self.info_text.config(state="disabled")
        
        # --- Left Column Inputs ---
        tk.Label(top, text="PRODUCT CATEGORY", bg=self.CARD, fg=self.MUTED, font=T.FONT_LABEL).pack(anchor="w")
        self.category_combo = ttk.Combobox(top, textvariable=self.category, values=self._get_categories(), state="readonly", style="Crystal.TCombobox", width=50)
        self.category_combo.pack(fill="x", pady=(6, 16))
        self.category_combo.bind("<<ComboboxSelected>>", self._category_changed)

        model_head = tk.Frame(top, bg=self.CARD)
        model_head.pack(fill="x")
        tk.Label(model_head, text="SELECT MODEL", bg=self.CARD, fg=self.MUTED,
                 font=T.FONT_LABEL).pack(side="left")
        W.GhostButton(
            model_head, "Edit product", self._quick_edit_product,
            padx=10, pady=3,
        ).pack(side="right")
        W.GhostButton(
            model_head, "New product", self._quick_add_product,
            padx=10, pady=3,
        ).pack(side="right", padx=(0, 6))
        self.model_combo = ttk.Combobox(top, textvariable=self.model, values=self._get_models(self.category.get()), state="normal", style="Crystal.TCombobox", width=50)
        self.model_combo.pack(fill="x", pady=(6, 16))
        self.model_combo.bind("<<ComboboxSelected>>", self._model_changed)
        self.model_combo.bind("<KeyRelease>", self._on_model_keyrelease)

        row = tk.Frame(top, bg=self.CARD)
        row.pack(fill="x", pady=10)
        
        def _num_entry(variable, width):
            e = tk.Entry(
                row, textvariable=variable, width=width,
                bg=T.SURFACE, fg=self.TEXT, relief="flat", bd=0,
                highlightthickness=1, highlightbackground=self.BORDER,
                highlightcolor=T.FOCUS, font=T.FONT_BODY,
                insertbackground=self.RED,
            )
            e.pack(side="left", ipady=5, padx=(0, 20))
            return e

        # HSN Code
        tk.Label(row, text="HSN/SAC", bg=self.CARD, fg=self.MUTED, font=T.FONT_LABEL).pack(side="left", padx=(0, 6))
        self.hsn_var = tk.StringVar()
        _num_entry(self.hsn_var, 12)

        # Price
        tk.Label(row, text="PRICE (₹)", bg=self.CARD, fg=self.MUTED, font=T.FONT_LABEL).pack(side="left", padx=(0, 6))
        _num_entry(self.machine_price, 10)

        # Qty
        tk.Label(row, text="QTY", bg=self.CARD, fg=self.MUTED, font=T.FONT_LABEL).pack(side="left", padx=(0, 6))
        _num_entry(self.machine_qty, 5)

        # Discount
        tk.Label(row, text="DISCOUNT", bg=self.CARD, fg=self.MUTED, font=T.FONT_LABEL).pack(side="left", padx=(0, 6))
        self.disc_mode = tk.StringVar(value="Amount (₹)")
        disc_mode_box = ttk.Combobox(row, textvariable=self.disc_mode, values=["Amount (₹)", "Percentage (%)"], state="readonly", width=12, style="Crystal.TCombobox", font=T.FONT_SMALL)
        disc_mode_box.pack(side="left", padx=(0, 6))
        self.disc_var = tk.StringVar(value="0")
        _num_entry(self.disc_var, 8)
        
        # Update Catalog Checkbox
        catalog_frame = tk.Frame(top, bg=self.CARD)
        catalog_frame.pack(fill="x", pady=(0, 5))
        self._update_catalog_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            catalog_frame,
            text="Also update catalog price for this model",
            variable=self._update_catalog_var,
            bg=self.CARD, fg=self.MUTED, activebackground=self.CARD,
            activeforeground=self.TEXT, selectcolor=T.SURFACE,
            font=T.FONT_SMALL, anchor="w"
        ).pack(side="left")
        
        # Add to Quotation Button
        tk.Button(
            top, text="Add to quotation  +",
            bg=self.RED, fg="white",
            activebackground=self.RED_DARK, activeforeground="white",
            font=T.FONT_BODY_B, relief="flat", bd=0,
            highlightthickness=0, padx=20, pady=8,
            cursor="hand2", command=self._add_item_to_cart,
        ).pack(anchor="e", pady=10)

        # --- Cart Table ---
        self.cart_frame = tk.Frame(card, bg=self.CARD)
        self.cart_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        cols = ("model", "hsn", "qty", "price", "discount", "total")
        self.cart_tree = ttk.Treeview(self.cart_frame, columns=cols, show="headings", height=6)
        anchors = {"qty": "e", "price": "e", "discount": "e", "total": "e"}
        for c, w, t in [("model", 200, "Model"), ("hsn", 80, "HSN"), ("qty", 60, "Qty"), ("price", 100, "Price"), ("discount", 100, "Discount"), ("total", 100, "Total")]:
            self.cart_tree.heading(c, text=t, anchor=anchors.get(c, "w"))
            self.cart_tree.column(c, width=w, anchor=anchors.get(c, "w"))
        self.cart_tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        self.cart_tree.tag_configure("oddrow", background=T.SURFACE)
        
        vsb = ttk.Scrollbar(self.cart_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=vsb.set)
        self.cart_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tk.Button(
            card, text="Remove selected",
            bg=T.SURFACE, fg=T.TEXT_BODY,
            activebackground=T.SURFACE_HOVER, activeforeground=self.TEXT,
            font=T.FONT_SMALL, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=self.BORDER,
            padx=14, pady=5, cursor="hand2",
            command=self._remove_cart_item,
        ).pack(anchor="w", pady=10)

        self._refresh_cart_table()


    def _add_item_to_cart(self, silent=False):
        model = self.model.get().strip()
        if not model:
            if not silent: messagebox.showwarning("Empty", "Select a model first.", parent=self)
            return
        try: price = float(str(self.machine_price.get() or "0").strip() or "0")
        except: price = 0.0
        
        # Update catalog if checkbox is checked
        if getattr(self, '_update_catalog_var', None) and self._update_catalog_var.get():
            if price > 0:
                try:
                    from app.services.catalog_admin_service import update_product
                    update_product(model, {"price": price})
                    print(f"[catalog] Updated price for {model} to {price}")
                except Exception as e:
                    print(f"[catalog] Could not update price: {e}")
        try: qty = int(float(str(self.machine_qty.get() or "1").strip() or "1"))
        except: qty = 1
        try: disc_val = float(str(self.disc_var.get() or "0").strip() or "0")
        except: disc_val = 0.0
            
        if price <= 0 or qty <= 0:
            if not silent: messagebox.showerror("Invalid", "Price and Qty must be > 0.", parent=self)
            return
            
        subtotal = price * qty
        disc = 0.0
        
        # Check if discount is Percentage or Amount
        mode = getattr(self, 'disc_mode', None)
        mode_val = mode.get() if mode else "Amount (₹)"
        
        # Save raw disc value and mode for display
        raw_disc = disc_val
        
        if mode_val == "Percentage (%)":
            disc = subtotal * (disc_val / 100.0)
        else:
            disc = disc_val
            
        # Ensure discount doesn't exceed subtotal
        if disc > subtotal:
            disc = subtotal
            
        total = subtotal - disc
        self.items.append({
            "model": model, 
            "hsn": (getattr(self, "hsn_var", tk.StringVar()).get().strip() or "85059000"), 
            "price": price, 
            "qty": qty, 
            "discount": disc, 
            "raw_discount": raw_disc,
            "disc_mode": mode_val,
            "total": total
        })
        self._refresh_cart_table()
        self.model.set("")
        self.machine_price.set("")
        self.machine_qty.set("1")
        self.disc_var.set("0")
        if hasattr(self, '_update_catalog_var'):
            self._update_catalog_var.set(False)

    def _remove_cart_item(self):
        sel = self.cart_tree.selection()
        if not sel: return
        idx = int(sel[0].replace("row_", ""))
        del self.items[idx]
        self._refresh_cart_table()

    def _refresh_cart_table(self):
        if not hasattr(self, "cart_tree"): return
        self.cart_tree.delete(*self.cart_tree.get_children())
        for i, item in enumerate(self.items):
            self.cart_tree.insert("", "end", iid=f"row_{i}", values=(
                item["model"], 
            item.get("hsn", "85059000"), 
            item["qty"], 
            f"₹{item['price']:,.0f}", 
            f"{item.get('raw_discount', 0)}%" if item.get('disc_mode') == "Percentage (%)" else f"₹{item['discount']:,.0f}",
            f"₹{item['total']:,.0f}"
            ), tags=("evenrow" if i % 2 == 0 else "oddrow",))

    # ────────────────────────────────────────────────────────
    # QUICK PRODUCT ACTIONS (Step 2)
    # ────────────────────────────────────────────────────────

    def _quick_add_product(self):
        self._open_quick_product(None)

    def _quick_edit_product(self):
        model = self.model.get().strip()
        if not model:
            messagebox.showinfo("Edit product", "Select a model first.",
                                parent=self)
            return
        product = None
        try:
            from app.services.catalog_service import get_products
            wanted = model.lower()
            for p in get_products():
                if str(p.get("model", "")).strip().lower() == wanted:
                    product = p
                    break
        except Exception:
            pass
        if not product:
            messagebox.showerror(
                "Edit product",
                f"Could not find {model} in the catalog.", parent=self,
            )
            return
        self._open_quick_product(product)

    def _open_quick_product(self, product):
        from app.services.catalog_admin_service import add_product, update_product

        editing = product is not None
        initial = product or {}

        dialog = tk.Toplevel(self)
        dialog.title("Edit product" if editing else "New product")
        dialog.configure(bg=T.SURFACE)
        dialog.transient(self)
        dialog.withdraw()
        W.set_window_icon(dialog)
        W.apply_ttk_theme(dialog)

        head = tk.Frame(dialog, bg=T.SURFACE)
        head.pack(fill="x", padx=22, pady=(18, 0))
        tk.Label(
            head, text="Edit product" if editing else "New product",
            bg=T.SURFACE, fg=T.TEXT, font=T.FONT_H2,
        ).pack(anchor="w")
        tk.Label(
            head,
            text=(f"Catalog details · {initial.get('model', '')}" if editing
                  else "Saved to the catalog and ready for this quotation."),
            bg=T.SURFACE, fg=T.TEXT_MUTED, font=T.FONT_SMALL,
            wraplength=500, justify="left",
        ).pack(anchor="w", pady=(2, 0))
        tk.Frame(dialog, bg=T.ACCENT, height=2).pack(fill="x", padx=22, pady=(12, 0))

        footer = tk.Frame(dialog, bg=T.SURFACE)
        footer.pack(side="bottom", fill="x", padx=22, pady=(10, 14))
        tk.Frame(dialog, bg=T.BORDER, height=1).pack(side="bottom", fill="x")

        body = tk.Frame(dialog, bg=T.SURFACE)
        body.pack(fill="both", expand=True, padx=22, pady=(12, 6))
        body.grid_columnconfigure(1, weight=1)

        fields, widgets = {}, {}

        def add_row(row, label, key, values=None):
            tk.Label(
                body, text=label, bg=T.SURFACE, fg=T.TEXT_BODY,
                font=T.FONT_LABEL, anchor="w",
            ).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
            var = tk.StringVar()
            fields[key] = var
            if values is not None:
                widget = ttk.Combobox(
                    body, textvariable=var, values=values, state="normal",
                    style="Crystal.TCombobox", font=T.FONT_BODY,
                )
            else:
                widget = W.SearchEntry(
                    body, textvariable=var, placeholder="", show_icon=False,
                )
            widget.grid(row=row, column=1, sticky="ew", pady=6)
            widgets[key] = widget

        add_row(0, "Model", "model")
        add_row(1, "Category", "category", values=self._get_categories())
        add_row(2, "Product name", "name")
        add_row(3, "Price (₹)", "price")
        add_row(4, "HSN/SAC", "hsn")
        add_row(5, "Unit", "unit")
        add_row(6, "Tax %", "tax_percent")

        fields["model"].set(str(initial.get("model", "")))
        fields["category"].set(
            str(initial.get("category") or self.category.get() or ""))
        fields["name"].set(
            str(initial.get("product_name") or initial.get("name") or ""))
        fields["price"].set(str(
            initial.get("price") if initial.get("price") is not None
            else initial.get("rate", "")))
        fields["hsn"].set(str(initial.get("hsn", "")))
        fields["unit"].set(str(initial.get("unit") or "NOS"))
        fields["tax_percent"].set(str(initial.get("tax_percent") or "18"))

        tk.Label(
            body, text="Description", bg=T.SURFACE, fg=T.TEXT_BODY,
            font=T.FONT_LABEL, anchor="nw",
        ).grid(row=7, column=0, sticky="nw", padx=(0, 12), pady=6)
        desc = tk.Text(
            body, height=3, font=T.FONT_BODY, bg=T.SURFACE, fg=T.TEXT,
            bd=0, highlightthickness=1, highlightbackground=T.BORDER,
            highlightcolor=T.FOCUS, wrap="word", insertbackground=T.TEXT,
        )
        desc.grid(row=7, column=1, sticky="ew", pady=6)
        desc.insert("1.0", str(initial.get("description") or ""))

        if editing:
            # Model is the catalog key and cannot be renamed here.
            try:
                widgets["model"].entry.configure(state="readonly")
            except Exception:
                pass

        def save():
            model = fields["model"].get().strip()
            if not model:
                messagebox.showerror("Product", "Model is required.",
                                     parent=dialog)
                return
            try:
                price = float(fields["price"].get().strip() or "0")
            except ValueError:
                messagebox.showerror("Product", "Price must be a number.",
                                     parent=dialog)
                return
            data = {
                "model": model,
                "category": fields["category"].get().strip() or "Uncategorized",
                "name": fields["name"].get().strip(),
                "product_name": fields["name"].get().strip(),
                "description": desc.get("1.0", "end").strip(),
                "price": price,
                "hsn": fields["hsn"].get().strip() or "85059000",
                "unit": fields["unit"].get().strip() or "NOS",
                "tax_percent": fields["tax_percent"].get().strip() or "18",
                "status": "Active",
            }
            try:
                if editing:
                    ok, err = update_product(str(initial.get("model", "")), data)
                else:
                    ok, err = add_product(data)
            except Exception as exc:
                ok, err = False, str(exc)
            if not ok:
                messagebox.showerror("Product", str(err), parent=dialog)
                return
            dialog.destroy()
            self._after_quick_product(data["model"], data["category"])

        W.GhostButton(
            footer, "Cancel", dialog.destroy, padx=18, pady=7,
        ).pack(side="right")
        W.PrimaryButton(
            footer, "Save product", save, padx=18, pady=7,
        ).pack(side="right", padx=(0, 8))

        W.fit_toplevel(dialog, 560)
        dialog.deiconify()
        dialog.grab_set()

    def _after_quick_product(self, model, category):
        categories = self._get_categories()
        if category and category not in categories:
            categories.append(category)
        self.category_combo["values"] = categories
        self.category.set(category)
        self.model_combo["values"] = self._get_models(category)
        self.model.set(model)
        self._model_changed()

    def _get_categories(self):

        merged = []

        if get_product_categories:

            try:

                categories = get_product_categories()

                if categories:
                    merged = [str(x) for x in categories]

            except Exception:
                pass

        # Always include the canonical Crystal categories first,
        # then append any extras that came from the catalog.
        try:
            from app.services import paths as _paths
            if _paths.get_active_module() == "Crystal":
                for cat in CANONICAL_CRYSTAL_CATEGORIES:
                    if cat not in merged:
                        merged.append(cat)
        except Exception:
            pass

        if merged:
            return merged

        return FALLBACK_CATEGORIES


    # ========================================================
    # MODELS
    # ========================================================

    def _get_models(self, category):

        if get_products_by_category:

            try:

                products = get_products_by_category(
                    category
                )

                if products:

                    result = []

                    for product in products:

                        if isinstance(
                            product,
                            dict
                        ):

                            model = (
                                product.get("model")
                                or product.get("catalog_no")
                                or product.get("code")
                            )

                            if model:
                                result.append(
                                    str(model)
                                )

                        else:

                            result.append(
                                str(product)
                            )

                    if result:
                        return result

            except Exception:
                pass

        return FALLBACK_MODELS.get(
            category,
            []
        )


    # ────────────────────────────────────────────────────────
    # TYPE-TO-SEARCH HELPERS (Feature B)
    # ────────────────────────────────────────────────────────

    def _get_products_for_category(self, category):
        """Return list of {model, name} dicts for a category (best-effort)."""
        out = []
        try:
            if get_products_by_category:
                products = get_products_by_category(category) or []
                for prod in products:
                    if isinstance(prod, dict):
                        m = prod.get("model") or prod.get("catalog_no") or prod.get("code")
                        n = prod.get("product_name") or prod.get("name") or ""
                        if m:
                            out.append({"model": str(m), "name": str(n)})
                    else:
                        out.append({"model": str(prod), "name": ""})
        except Exception:
            pass
        return out

    def _filter_models(self, query, category):
        """Return model list matching query on model OR name (case-insensitive)."""
        all_products = self._get_products_for_category(category)
        if not all_products:
            # fall back to the plain model list
            all_products = [{"model": m, "name": ""} for m in self._get_models(category)]

        q = (query or "").strip().lower()
        if not q:
            return [p["model"] for p in all_products]

        hits = [
            p["model"] for p in all_products
            if q in p["model"].lower() or q in p["name"].lower()
        ]
        return hits

    def _on_model_keyrelease(self, event=None):
        """Called on each keystroke in the model combobox.

        Filter the dropdown options to matching models (by model OR name),
        scoped to the currently selected category.
        """
        # Ignore navigation / commit keys
        if event is not None and event.keysym in (
            "Up", "Down", "Left", "Right", "Return", "Escape", "Tab"
        ):
            return

        query = self.model.get()
        category = self.category.get()

        matches = self._filter_models(query, category)
        self.model_combo["values"] = matches

        # If the typed text exactly matches a model, commit it as a selection
        if query and query in matches:
            # Defer so the dropdown value is actually set first
            try:
                self.after(1, self._model_changed)
            except Exception:
                self._model_changed()


    # ========================================================
    # CATEGORY CHANGED
    # ========================================================

    def _category_changed(self, event=None):

        models = self._get_models(
            self.category.get()
        )

        self.model_combo["values"] = models

        if models:

            self.model.set(
                models[0]
            )

        else:

            self.model.set("")

        self._model_changed()


    # ========================================================
    # MODEL CHANGED
    # ========================================================

    def _model_changed(self, event=None):
        model = self.model.get().strip()
        if not model:
            return
        
        # Import get_product HERE to avoid UnboundLocalError
        try:
            from app.services.catalog_service import get_product
            product = get_product(model)
        except Exception as e:
            print(f"Error fetching product: {e}")
            product = None
        
        # Auto-fill HSN and Price
        if product:
            hsn = product.get('hsn') or product.get('hsn_code') or ""
            self.hsn_var.set(str(hsn))
            
            price = product.get('price')
            if price is not None:
                try:
                    self.machine_price.set(str(float(price)))
                except Exception:
                    pass
            
            # Update Info Panel
            if hasattr(self, 'info_text'):
                try:
                    self.info_text.config(state="normal")
                    self.info_text.delete("1.0", "end")
                    
                    info = f"MODEL: {product.get('model', 'N/A')}\n"
                    info += f"CATEGORY: {product.get('category', 'N/A')}\n"
                    info += "=" * 40 + "\n\n"
                    
                    desc = product.get('description') or product.get('product_name') or ''
                    if desc:
                        info += f"DESCRIPTION:\n{desc}\n\n"
                    
                    size = product.get('dimension') or product.get('measuring_range') or product.get('size') or ''
                    if size:
                        info += f"SIZE / DIMENSIONS:\n{size}\n\n"
                    
                    price = product.get('price', 0)
                    info += f"LIST PRICE: ₹{float(price):,.2f}"
                    
                    self.info_text.insert("1.0", info)
                    self.info_text.config(state="disabled")
                except Exception as e:
                    print(f"Info panel error: {e}")
        else:
            self.hsn_var.set("")
            self.machine_price.set("")
            if hasattr(self, 'info_text'):
                self.info_text.config(state="normal")
                self.info_text.delete("1.0", "end")
                self.info_text.insert("1.0", f"Model '{model}' not found in catalog.")
                self.info_text.config(state="disabled")
        
        # Update summary
        try:
            self._recalculate()
        except Exception:
            pass
        try:
            self._update_summary()
        except Exception:
            pass


    def _validate_product(self):
        """Validation bypassed. The cart check in _next handles everything."""
        return True


    # ========================================================
    # GET ACCESSORIES  (from catalog — active only)
    # ========================================================

    # ========================================================
    # STEP 4 — PRICING
    # ========================================================


    def _do_refresh_pricing(self):
        try:
            self._clear_content()
            self._render_pricing()
        except Exception as e:
            print(f"Rebuild error: {e}")


    def _reload_pricing_screen(self):
        """Safely reload the pricing screen while preserving transport input."""
        try:
            # 1. Save the current transport value
            if hasattr(self, "transport_var"):
                saved_transport = self.transport_var.get()
            else:
                saved_transport = "0"
                
            # 2. Clear the screen
            self._clear_content()
            
            # 3. Restore the saved value BEFORE redrawing
            if hasattr(self, "transport_var"):
                self.transport_var.set(saved_transport)
                
            # 4. Redraw
            self._render_pricing()
        except Exception as e:
            print(f"Reload error: {e}")

    def _render_pricing(self):
        self._clear_content()
        card = self._create_card(self.content_area)
        self._section_header(card, 3, "Final pricing", "Review the commercial calculation before continuing.")

        # 1. Calculate Cart Total
        items_total = sum(float(item.get("total", 0)) for item in getattr(self, "items", []))

        # --- Packing UI ---
        packing_ctrl_frame = tk.Frame(card, bg=self.CARD)
        packing_ctrl_frame.pack(fill="x", pady=(10, 10))
        
        def _pricing_entry(parent, variable, width):
            e = tk.Entry(
                parent, textvariable=variable, width=width,
                bg=T.SURFACE, fg=self.TEXT, relief="flat", bd=0,
                highlightthickness=1, highlightbackground=self.BORDER,
                highlightcolor=T.FOCUS, font=T.FONT_BODY,
                insertbackground=self.RED,
            )
            e.pack(side="left", ipady=5)
            return e

        tk.Label(packing_ctrl_frame, text="PACKING TYPE", bg=self.CARD, fg=T.TEXT_MUTED, font=T.FONT_LABEL).pack(side="left", padx=(0, 6))
        
        packing_mode_box = ttk.Combobox(
            packing_ctrl_frame,
            textvariable=self.packing_mode,
            values=["Percentage (%)", "Amount (₹)", "No Packing"],
            state="readonly",
            width=15,
            style="Crystal.TCombobox"
        )
        packing_mode_box.pack(side="left", padx=(0, 18))
        
        tk.Label(packing_ctrl_frame, text="VALUE", bg=self.CARD, fg=T.TEXT_MUTED, font=T.FONT_LABEL).pack(side="left", padx=(0, 6))
        
        packing_val_entry = _pricing_entry(packing_ctrl_frame, self.packing_value, 10)

        # --- Transport & GST Controls ---
        extra_ctrl_frame = tk.Frame(card, bg=self.CARD)
        extra_ctrl_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(extra_ctrl_frame, text="TRANSPORT (₹)", bg=self.CARD, fg=T.TEXT_MUTED, font=T.FONT_LABEL).pack(side="left", padx=(0, 6))
        if not hasattr(self, "transport_var"):
            self.transport_var = tk.StringVar(value="0")
            
        transport_entry = _pricing_entry(extra_ctrl_frame, self.transport_var, 10)
        transport_entry.pack_configure(padx=(0, 20))
        
        # Bind the Transport entry to trigger a reload when the user presses Enter or clicks away
        transport_entry.bind("<Return>", lambda e: self._reload_pricing_screen())
        transport_entry.bind("<FocusOut>", lambda e: self._reload_pricing_screen())
        
        tk.Label(extra_ctrl_frame, text="GST TYPE", bg=self.CARD, fg=T.TEXT_MUTED, font=T.FONT_LABEL).pack(side="left", padx=(0, 6))
        if not hasattr(self, "gst_type"):
            self.gst_type = tk.StringVar(value="CGST + SGST")
        gst_type_box = ttk.Combobox(extra_ctrl_frame, textvariable=self.gst_type, values=["CGST + SGST", "IGST"], state="readonly", width=12, style="Crystal.TCombobox")
        gst_type_box.pack(side="left")
        
        # Recalculate Button
        tk.Button(
            extra_ctrl_frame, 
            text="Recalculate", 
            bg=self.RED, fg="white", 
            activebackground=self.RED_DARK, activeforeground="white",
            font=T.FONT_LABEL, relief="flat", bd=0,
            highlightthickness=0, padx=16, pady=6,
            cursor="hand2",
            command=self._reload_pricing_screen
        ).pack(side="left", padx=(18, 0))

        # --- Math Calculation ---
        try:
            pack_val = float(self.packing_value.get() or "0")
            if self.packing_mode.get() == "Percentage (%)":
                packing_amt = items_total * (pack_val / 100.0)
            else:
                packing_amt = pack_val
        except Exception:
            packing_amt = 0.0
            
        try:
            transport = float(self.transport_var.get() or "0")
        except Exception:
            transport = 0.0
            
        try:
            gst_rate = float(self.gst_rate.get() or "18")
        except Exception:
            gst_rate = 18.0
            
        taxable = items_total + packing_amt + transport
        gst_amt = taxable * (gst_rate / 100.0)
        
        # THE CRITICAL CHECK
        current_gst = self.gst_type.get() if hasattr(self, "gst_type") else "CGST + SGST"
        
        if current_gst == "IGST":
            cgst = 0.0
            sgst = 0.0
            igst = gst_amt
        else:
            cgst = gst_amt / 2.0
            sgst = gst_amt / 2.0
            igst = 0.0
            
        grand = taxable + gst_amt

        # --- Build Rows ---
        fmt = lambda v: f"₹{v:,.2f}"
        
        rows = []
        rows.append(("Machine (Cart Total)", fmt(items_total)))
        if packing_amt > 0:
            rows.append(("Packing", fmt(packing_amt)))
        rows.append(("Transportation", fmt(transport)))
        rows.append(("Taxable Value", fmt(taxable)))
        
        if current_gst == "IGST":
            rows.append((f"IGST ({gst_rate:g}%)", fmt(igst)))
        else:
            rows.append((f"CGST ({gst_rate/2:g}%)", fmt(cgst)))
            rows.append((f"SGST ({gst_rate/2:g}%)", fmt(sgst)))
            
        rows.append(("GRAND TOTAL", fmt(grand)))

        # --- Draw Table ---
        table_frame = tk.Frame(card, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1)
        table_frame.pack(fill="x", pady=(10, 20), padx=20)

        for label, value in rows:
            is_grand_total = (label == "GRAND TOTAL")
            row_bg = self.SOFT if is_grand_total else self.CARD
            
            row = tk.Frame(table_frame, bg=row_bg)
            row.pack(fill="x", pady=0)
            
            pad_y = 12 if is_grand_total else 8
            
            lbl_font = T.FONT_BODY_B if is_grand_total else T.FONT_BODY
            lbl_fg = self.TEXT if is_grand_total else self.MUTED
            tk.Label(row, text=label, bg=row_bg, fg=lbl_fg, font=lbl_font).pack(side="left", padx=15, pady=pad_y)
            
            val_font = T.FONT_H3 if is_grand_total else T.FONT_BODY_B
            val_fg = self.RED if is_grand_total else self.TEXT
            tk.Label(row, text=value, bg=row_bg, fg=val_fg, font=val_font).pack(side="right", padx=15, pady=pad_y)
            
            if not is_grand_total:
                tk.Frame(table_frame, bg=self.BORDER, height=1).pack(fill="x", padx=10)

    def _render_terms(self):

        self._clear_content()

        card = self._create_card(
            self.content_area
        )

        self._section_header(
            card,
            4,
            "Terms & conditions",
            "Choose whether the quotation should include the standard terms."
        )

        # ----------------------------------------------------
        # ACTION BAR
        # ----------------------------------------------------

        action_bar = tk.Frame(
            card,
            bg=self.CARD
        )

        action_bar.pack(
            fill="x",
            pady=(0, 14)
        )

        tk.Button(
            action_bar,
            text="Edit terms",
            command=self._open_terms_editor,
            bg=T.SURFACE,
            fg=T.TEXT_BODY,
            activebackground=T.SURFACE_HOVER,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.BORDER,
            highlightcolor=T.FOCUS,
            font=T.FONT_LABEL,
            cursor="hand2",
            padx=16,
            pady=6
        ).pack(
            side="left"
        )

        tk.Button(
            action_bar,
            text="Restore defaults",
            command=self._restore_default_terms,
            bg=T.SURFACE,
            fg=T.TEXT_MUTED,
            activebackground=T.SURFACE_HOVER,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.BORDER,
            highlightcolor=T.FOCUS,
            font=T.FONT_SMALL,
            cursor="hand2",
            padx=14,
            pady=6
        ).pack(
            side="left",
            padx=(8, 0)
        )

        tk.Button(
            action_bar,
            text="Preview quotation",
            command=self._open_preview,
            bg=T.SURFACE,
            fg=self.RED,
            activebackground=T.ACCENT_SOFT,
            activeforeground=self.RED,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.BORDER,
            highlightcolor=T.FOCUS,
            font=T.FONT_BODY_B,
            cursor="hand2",
            padx=16,
            pady=6
        ).pack(
            side="left",
            padx=(8, 0)
        )


        # ----------------------------------------------------
        # MAIN SWITCH
        # ----------------------------------------------------

        switch_box = tk.Frame(
            card,
            bg=self.SOFT
        )

        switch_box.pack(
            fill="x",
            pady=(0, 15)
        )

        def _master_toggle():
            """Keep the master switch and individual term selections synchronized."""
            enabled = bool(self.include_terms.get())
            for term_row in self.term_rows:
                term_row["selected"].set(enabled)

        tk.Checkbutton(
            switch_box,
            text="Include Terms & Conditions page",
            variable=self.include_terms,
            command=_master_toggle,
            bg=self.SOFT,
            activebackground=self.SOFT,
            selectcolor="white",
            fg=self.TEXT,
            font=T.FONT_BODY_B
        ).pack(
            side="left",
            padx=15,
            pady=13
        )

        # ----------------------------------------------------
        # TERMS LIST
        # ----------------------------------------------------

        self.term_rows = []

        if not self.custom_terms:

            empty = tk.Frame(
                card,
                bg=self.SOFT
            )

            empty.pack(
                fill="x",
                pady=6
            )

            tk.Label(
                empty,
                text=(
                    "No terms defined. "
                    "Click “Edit Terms & Conditions” to add some."
                ),
                bg=self.SOFT,
                fg=self.MUTED,
                font=T.FONT_SMALL
            ).pack(
                anchor="w",
                padx=14,
                pady=14
            )

        for title, value in self.custom_terms:

            row = tk.Frame(
                card,
                bg=self.CARD,
                highlightbackground=self.BORDER,
                highlightthickness=1
            )

            row.pack(
                fill="x",
                pady=3
            )

            enabled = tk.BooleanVar(
                value=True
            )

            def _term_toggle(var=enabled):
                """Turn the master switch on/off based on individual selections."""
                if self.term_rows:
                    self.include_terms.set(
                        any(r["selected"].get() for r in self.term_rows)
                    )

            tk.Checkbutton(
                row,
                variable=enabled,
                command=_term_toggle,
                bg=self.CARD,
                activebackground=self.CARD,
                selectcolor=self.CARD
            ).pack(
                side="left",
                padx=(10, 4)
            )

            tk.Label(
                row,
                text=title,
                bg=self.CARD,
                fg=self.TEXT,
                width=28,
                anchor="w",
                font=T.FONT_LABEL
            ).pack(
                side="left",
                padx=4,
                pady=9
            )

            tk.Label(
                row,
                text=value,
                bg=self.CARD,
                fg=self.MUTED,
                anchor="w",
                justify="left",
                wraplength=650,
                font=T.FONT_SMALL
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=8,
                pady=9
            )

            self.term_rows.append(
                {
                    "title": title,
                    "value": value,
                    "selected": enabled,
                }
            )

        if self.custom_terms:
            self.include_terms.set(True)

        self.status_text.set(
            "Choose whether to include Terms & Conditions."
        )


    # ========================================================
    # TERMS EDITOR LAUNCHER
    # ========================================================

    def _open_terms_editor(self):

        editor = TermsEditor(
            parent=self,
            terms=self.custom_terms
        )

        self.wait_window(editor)

        if editor.result is not None:

            self.custom_terms = editor.result

            self._save_terms()

            self._render_terms()


    # ========================================================
    # RESTORE DEFAULT TERMS
    # ========================================================

    def _restore_default_terms(self):

        confirm = messagebox.askyesno(
            "Restore default terms",
            (
                "Replace the current terms with the "
                "standard defaults?\n\n"
                "This will also overwrite your saved custom terms."
            ),
            parent=self
        )

        if not confirm:
            return

        self.custom_terms = [
            (title, value)
            for title, value in STANDARD_TERMS
        ]

        self._save_terms()

        self._render_terms()

        messagebox.showinfo(
            "Defaults restored",
            "Standard terms have been restored.",
            parent=self
        )


    # ========================================================
    # SUMMARY PANEL
    # ========================================================

    def _build_summary_panel(self):

        outer = tk.Frame(
            self.right_area,
            bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        outer.pack(
            fill="both",
            expand=True
        )

        header = tk.Frame(
            outer,
            bg=self.CARD
        )

        header.pack(
            fill="x",
            padx=22,
            pady=(22, 10)
        )

        tk.Label(
            header,
            text="QUOTATION",
            bg=self.CARD,
            fg=self.MUTED,
            font=T.FONT_LABEL
        ).pack(
            anchor="w"
        )

        tk.Label(
            header,
            text="Live summary",
            bg=self.CARD,
            fg=self.TEXT,
            font=T.FONT_H2
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

        self.summary_customer = tk.Label(
            outer,
            text="Customer not added",
            bg=self.CARD,
            fg=self.TEXT,
            font=T.FONT_BODY_B,
            anchor="w",
            justify="left",
            wraplength=300
        )

        self.summary_customer.pack(
            fill="x",
            padx=22,
            pady=(12, 2)
        )

        self.summary_company = tk.Label(
            outer,
            text="",
            bg=self.CARD,
            fg=self.MUTED,
            font=T.FONT_SMALL,
            anchor="w",
            wraplength=300
        )

        self.summary_company.pack(
            fill="x",
            padx=22
        )

        self._summary_separator(
            outer
        )

        self.summary_product = tk.Label(
            outer,
            text="No machine selected",
            bg=self.CARD,
            fg=self.TEXT,
            font=T.FONT_BODY_B,
            anchor="w",
            justify="left",
            wraplength=300
        )

        self.summary_product.pack(
            fill="x",
            padx=22
        )

        self._summary_separator(
            outer
        )

        self.summary_total_label = tk.Label(
            outer,
            text="PRODUCT",
            bg=self.CARD,
            fg=self.MUTED,
            font=T.FONT_LABEL
        )
        self.summary_total_label.pack(
            anchor="w",
            padx=22
        )

        self.summary_total = tk.Label(
            outer,
            text="₹ 0.00",
            bg=self.CARD,
            fg=self.RED,
            font=T.FONT_KPI,
            anchor="w"
        )

        self.summary_total.pack(
            anchor="w",
            padx=22,
            pady=(3, 15)
        )

        self.summary_status = tk.Label(
            outer,
            textvariable=self.status_text,
            bg=T.ACCENT_SOFT,
            fg=T.ACCENT_DARK,
            font=T.FONT_LABEL,
            anchor="w",
            justify="left",
            wraplength=290
        )

        self.summary_status.pack(
            fill="x",
            padx=18,
            pady=18,
            ipady=9
        )


    def _summary_separator(self, parent):

        tk.Frame(
            parent,
            bg=self.BORDER,
            height=1
        ).pack(
            fill="x",
            padx=22,
            pady=18
        )


    # ========================================================
    # FIXED NAVIGATION BAR
    # ========================================================

    def _build_navigation_bar(self):

        self.navigation = tk.Frame(
            self,
            bg=T.SURFACE,
            height=72,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        self.navigation.pack(
            side="bottom",
            fill="x"
        )

        self.navigation.pack_propagate(False)

        left_group = tk.Frame(
            self.navigation,
            bg=T.SURFACE
        )

        left_group.pack(
            side="left",
            padx=28
        )

        self.back_button = tk.Button(
            left_group,
            text="←  Back",
            command=self._back,
            bg=T.SURFACE,
            fg=T.TEXT_BODY,
            activebackground=T.SURFACE_HOVER,
            activeforeground=self.TEXT,
            disabledforeground=T.TEXT_FAINT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.BORDER,
            highlightcolor=T.FOCUS,
            padx=18,
            pady=7,
            font=T.FONT_BODY_B,
            cursor="hand2"
        )

        self.back_button.pack(
            side="left",
            padx=(0, 8)
        )

        self.clear_button = tk.Button(
            left_group,
            text="Clear",
            command=self.clear_form,
            bg=T.SURFACE,
            fg=T.TEXT_MUTED,
            activebackground=T.SURFACE_HOVER,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=14,
            pady=7,
            font=T.FONT_BODY,
            cursor="hand2"
        )

        self.clear_button.pack(
            side="left",
            padx=4
        )

        right_group = tk.Frame(
            self.navigation,
            bg=T.SURFACE
        )

        right_group.pack(
            side="right",
            padx=28
        )

        self.generate_button = tk.Button(
            right_group,
            text="Continue to Product  →",
            command=self._next,
            bg=self.RED,
            fg="white",
            activebackground=self.RED_DARK,
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=22,
            pady=8,
            font=T.FONT_BODY_B,
            cursor="hand2"
        )

        self.generate_button.pack(
            side="right"
        )


    # ========================================================
    # LOAD STEP
    # ========================================================

    
    def _clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def _load_step(self, step):

        self.current_step = step

        if step == 1:
            self._render_customer()

        elif step == 2:
            self._render_product()

        elif step == 3:
            self._render_pricing()

        elif step == 4:
            self._render_terms()

        self._update_stepper()

        self._update_summary()

        if step == 1:

            self.back_button.configure(
                state="disabled",
                fg=T.TEXT_FAINT
            )

        else:

            self.back_button.configure(
                state="normal",
                fg=self.TEXT
            )

        button_text = {

            1: "Continue to Product  →",

            2: "Continue to Pricing  →",

            3: "Continue to Terms  →",

            4: f"Review {self._doc_label()}  →",
        }

        self.generate_button.configure(
            text=button_text.get(
                step,
                "Continue  →"
            ),

            state="normal"
        )

        try:

            self.canvas.yview_moveto(0)

        except Exception:

            pass


    # ========================================================
    # NEXT
    # ========================================================

    def _next(self):
        # 1. Auto-add the current item if the user forgot to click "Add"
        try:
            if hasattr(self, "model") and self.model.get().strip() and hasattr(self, "machine_price"):
                if self.machine_price.get().strip():
                    self._add_item_to_cart(silent=True)
        except Exception:
            pass
        
        # 2. Check if cart has items. If yes, NEVER block them.
        has_cart = bool(getattr(self, "items", []))
        
        # 3. Only block on Step 2 if the cart is completely empty.
        if self.current_step == 2 and not has_cart:
            import tkinter.messagebox as mb
            mb.showwarning("Product required", "Please add at least one model to the cart using the 'Add to Quotation' button.", parent=self)
            return
        
        # 4. Navigation logic
        if self.current_step < 4:
            self.completed_steps.add(self.current_step)
            self._load_step(self.current_step + 1)
        else:
            # 5. Step 4 (Terms) -> Generate
            if hasattr(self, '_generate_quotation'):
                self._generate_quotation()
            else:
                import tkinter.messagebox as mb
                mb.showerror("Error", "Generation function not found.", parent=self)

    def _back(self):

        if self.current_step > 1:

            self._load_step(
                self.current_step - 1
            )


    # ========================================================
    # STEPPER UPDATE
    # ========================================================

    def _update_stepper(self):

        for index, widgets in enumerate(
            self.step_widgets,
            start=1
        ):

            circle, title, subtitle = widgets

            if index in self.completed_steps:

                circle.configure(
                    text="✓",
                    bg=self.GREEN,
                    fg="white"
                )

                title.configure(
                    fg=self.GREEN
                )

            elif index == self.current_step:

                circle.configure(
                    text=str(index),
                    bg=self.RED,
                    fg="white"
                )

                title.configure(
                    fg=self.RED
                )

            else:

                circle.configure(
                    text=str(index),
                    bg=T.NEUTRAL_BG,
                    fg=T.TEXT_MUTED
                )

                title.configure(
                    fg=self.MUTED
                )


    # ========================================================
    # NUMBER  (float — used only for validation checks)
    # ========================================================

    @staticmethod
    def _number(value):

        try:

            return float(
                str(value)
                .replace(",", "")
                .replace("₹", "")
                .strip()
                or 0
            )

        except (
            ValueError,
            TypeError
        ):

            return 0.0


    # ========================================================
    # DECIMAL  (safe money arithmetic)
    # ========================================================

    @staticmethod
    def _decimal(value):

        if value is None:
            return Decimal("0")

        try:

            s = (
                str(value)
                .replace(",", "")
                .replace("₹", "")
                .strip()
            )

            return Decimal(s) if s else Decimal("0")

        except (InvalidOperation, ValueError, TypeError):

            return Decimal("0")


    # ========================================================
    # PRICING VALIDATION
    # ========================================================

    def _validate_pricing(self):
        """Pricing is optional."""
        price = self._number(self.machine_price.get())
        qty = self._number(self.machine_qty.get())

        if qty <= 0:
            try:
                self.machine_qty.set("1")
            except Exception:
                pass

        if price <= 0:
            ok = messagebox.askyesno(
                "Price is empty",
                "Machine price is empty or zero. Continue anyway?",
                parent=self,
            )
            if not ok:
                return False

        if self.gst_type.get() not in (
            "CGST + SGST", "IGST", "No GST",
        ):
            messagebox.showerror(
                "Invalid GST type",
                "Please select CGST + SGST, IGST, or No GST.",
                parent=self,
            )
            return False

        return True


    # ========================================================
    # GST RATE SYNCHRONIZATION
    # ========================================================

    def _sync_gst_percentages(self):
        """
        Convert the manually selected GST type/rate into the legacy
        cgst_percent / sgst_percent fields expected by the existing
        quotation generator.

        CGST + SGST:
            18% total -> 9% CGST + 9% SGST

        IGST:
            18% total -> 0% CGST + 0% SGST
            The full rate is retained separately as igst_percent.

        No GST:
            0% CGST + 0% SGST + 0% IGST
        """

        rate = self._decimal(
            self.gst_rate.get()
        )

        gst_type = self.gst_type.get().strip()

        if gst_type == "CGST + SGST":

            half = rate / Decimal("2")

            self.cgst_percent.set(
                str(half)
            )

            self.sgst_percent.set(
                str(half)
            )

            return Decimal("0")

        if gst_type == "IGST":

            self.cgst_percent.set("0")
            self.sgst_percent.set("0")

            return rate

        # No GST
        self.cgst_percent.set("0")
        self.sgst_percent.set("0")

        return Decimal("0")


    # ========================================================
    # RECALCULATE  (Decimal-only)
    # ========================================================

    def _recalculate(self, *_args):
        items_total = sum(float(item.get("total", 0)) for item in getattr(self, "items", []))
        fmt = lambda v: f"₹{v:,.2f}"
        
        if hasattr(self, "summary_values"):
            def _set(k, v):
                try:
                    if k in self.summary_values: self.summary_values[k].set(v)
                except: pass
            _set("grand", fmt(items_total))
            _set("subtotal", fmt(items_total))
            _set("taxable", fmt(items_total))
            
        # Force update the direct red label
        try:
            if hasattr(self, "lbl_grand_total"):
                self.lbl_grand_total.configure(text=fmt(items_total))
        except: pass

    def _update_summary(self):

        customer = self.customer_name.get().strip()

        company = self.company.get().strip()

        if customer:

            self.summary_customer.configure(
                text=customer
            )

        else:

            self.summary_customer.configure(
                text="Customer not added"
            )

        self.summary_company.configure(
            text=company
        )

        model = self.model.get()

        if model:

            self.summary_product.configure(
                text=(
                    f"{model}\n"
                    f"{self.category.get()}"
                )
            )

        else:

            self.summary_product.configure(
                text="No machine selected"
            )

        self._recalculate()


    # ========================================================
    # FORM DATA
    # ========================================================

    def get_form_data(self):
        items = getattr(self, "items", [])
        items_total = sum(float(i.get("total", 0)) for i in items)
        first_model = items[0]["model"] if items else self.model.get().strip()
        final_price = items_total if items_total > 0 else float(self.machine_price.get() or 0)

        selected_terms = []
        for row in self.term_rows:
            if row["selected"].get():
                selected_terms.append({"title": row["title"], "value": row["value"]})

        # Calculate grand total from items
        grand_total = sum(float(item.get("total", 0)) for item in items)
        # Add GST (assume 18% for now, or read from gst_rate)
        try:
            gst_rate = float(self.gst_rate.get() or "18")
        except Exception:
            gst_rate = 18.0
        grand_total = grand_total * (1 + gst_rate / 100.0)
        
        # Ensure transportation is captured from the UI
        transport_val = 0.0
        if hasattr(self, "transport_var"):
            try:
                transport_val = float(self.transport_var.get() or "0")
            except Exception:
                pass
        elif hasattr(self, "transportation"):
            try:
                transport_val = float(self.transportation.get() or "0")
            except Exception:
                pass

        return {
            "grand_total": grand_total,
            "quotation_number": getattr(self, "_revision_number", None),
            "doc_type": self.doc_type.get() if hasattr(self, "doc_type") else "quotation",
            "customer_name": self.customer_name.get().strip(),
            "company": self.company.get().strip(),
            "contact_person": self.contact_person.get().strip(),
            "phone": self.phone.get().strip(),
            "email": self.email.get().strip(),
            "address": self.address.get().strip(),
            "city": self.city.get().strip(),
            "state": self.state.get().strip(),
            "pincode": self.pincode.get().strip(),
            "gstin": self.gstin.get().strip(),
            "model": first_model,
            "category": self.category.get(),
            "machine_price": final_price,
            "machine_qty": 1,
            "items": items,
            "packing_type": self.packing_mode.get(),
            "packing_value": self.packing_value.get(),
            "gst_type": self.gst_type.get(),
            "gst_rate": self.gst_rate.get(),
            "transportation": transport_val,
            "buyback": self.buyback.get() if hasattr(self, "buyback") else 0,
            "terms": selected_terms,
            "accessories": []
        }

    def _apply_prefill(self, data):
        """Populate form fields from a record and jump to Step 2 (Product).

        Accepts either a history record or a customer record. Field names
        are mapped best-effort, so missing keys are simply skipped.
        """
        if not data:
            return

        def _set(var_name, value):
            try:
                v = (value or "").strip() if isinstance(value, str) else value
                if v and hasattr(self, var_name):
                    getattr(self, var_name).set(v)
            except Exception:
                pass

        # ---- customer block (try multiple key spellings) ----
        _set("customer_name", data.get("customer_name") or data.get("name"))
        _set("company",       data.get("customer_company") or data.get("company"))
        _set("phone",         data.get("customer_phone") or data.get("phone"))
        _set("email",         data.get("customer_email") or data.get("email"))
        _set("address",       data.get("customer_address") or data.get("address"))
        _set("city",          data.get("customer_city") or data.get("city"))
        _set("state",         data.get("customer_state") or data.get("state"))
        _set("pincode",       data.get("customer_pincode") or data.get("pincode"))
        _set("gstin",         data.get("customer_gstin") or data.get("gstin"))
        _set("contact_person",data.get("contact_person"))

        # ---- product block (only if a model is present) ----
        model = (data.get("model") or "").strip()
        if model:
            try:
                values = list(self.model_combo["values"])
                if model not in values:
                    values.append(model)
                    self.model_combo["values"] = values
            except Exception:
                pass
            try:
                self.model.set(model)
                self._model_changed(None)
            except Exception:
                pass

        # ---- cart lines, discounts and commercial settings ----
        self._restore_record_details(data)

        # ---- jump to Product page (Step 2) ----
        try:
            self._load_step(2)
        except Exception:
            pass

    def _restore_record_details(self, data):
        """Restore cart rows and totals when prefilling a saved quotation."""
        def _num(value, default=0.0):
            try:
                text = str(value).replace(",", "").replace("₹", "").strip()
                return float(text) if text else default
            except Exception:
                return default

        items = []
        for raw in (data.get("items") or []):
            if not isinstance(raw, dict):
                continue
            model = str(raw.get("model") or "").strip()
            if not model:
                continue
            price = _num(raw.get("price"))
            qty = _num(raw.get("qty"), 1.0) or 1.0
            discount = _num(raw.get("discount"))
            total = _num(raw.get("total"), price * qty - discount)
            items.append({
                "model": model,
                "hsn": str(raw.get("hsn") or "85059000").strip() or "85059000",
                "price": price,
                "qty": int(qty) if float(qty).is_integer() else qty,
                "discount": discount,
                "raw_discount": raw.get("raw_discount", discount),
                "disc_mode": raw.get("disc_mode") or "Amount (₹)",
                "total": total,
            })

        if items:
            self.items = items
            try:
                self._refresh_cart_table()
            except Exception:
                pass
            # The cart already holds these lines; clear the model inputs so
            # "Continue" does not add the prefilled model a second time.
            try:
                self.model.set("")
                self.machine_price.set("")
                self.machine_qty.set("1")
                self.disc_var.set("0")
            except Exception:
                pass

        totals = data.get("totals") or {}

        transportation = _num(
            totals.get("transportation", data.get("transportation"))
        )
        if transportation:
            self.transportation.set(f"{transportation:g}")

        buyback = _num(totals.get("buyback"))
        if buyback:
            self.buyback.set(f"{buyback:g}")

        gst_type = str(
            totals.get("gst_type") or data.get("gst_type") or ""
        ).strip()
        if gst_type:
            self.gst_type.set(gst_type)

        gst_rate = _num(totals.get("gst_rate"))
        if gst_rate > 0:
            self.gst_rate.set(f"{gst_rate:g}")
            half = gst_rate / 2
            self.cgst_percent.set(f"{half:g}")
            self.sgst_percent.set(f"{half:g}")

        packing = _num(totals.get("packing"))
        subtotal = _num(totals.get("subtotal")) or sum(
            float(i.get("total", 0)) for i in items
        )
        if packing > 0 and subtotal > 0:
            percent = round(packing / subtotal * 100, 2)
            self.packing_mode.set("Percentage (%)")
            self.packing_value.set(f"{percent:g}")
            self.packing_percent.set(f"{percent:g}")
        elif totals:
            self.packing_mode.set("No Packing")
            self.packing_value.set("0")
            self.packing_percent.set("0")

        try:
            self._recalculate()
        except Exception:
            pass

    def _maybe_update_catalog(self):
        """If the user checked 'Also update catalog', update the
        catalog price for the selected model after confirmation.

        Returns True to continue with quotation generation,
        False to abort (user cancelled the confirmation dialog).
        """
        try:
            wants_update = bool(self.update_catalog.get())
        except Exception:
            wants_update = False

        if not wants_update:
            return True

        model = (self.model.get() or "").strip()
        if not model:
            return True

        try:
            new_price = float(self._decimal(self.machine_price.get()))
        except Exception:
            new_price = 0.0

        if new_price <= 0:
            messagebox.showwarning(
                "Cannot update catalog",
                "Catalog price must be greater than zero.",
                parent=self,
            )
            return True  # let quotation continue without catalog update

        # Show old price in confirmation
        old_price = None
        try:
            from app.services.catalog_service import get_product
            p = get_product(model)
            if p:
                old_price = p.get("price")
        except Exception:
            pass

        if old_price is not None:
            msg = (
                f"Update catalog price for {model}?\n\n"
                f"   Old: \u20b9 {float(old_price):,.2f}\n"
                f"   New: \u20b9 {new_price:,.2f}\n\n"
                f"This affects all future quotations for this model."
            )
        else:
            msg = (
                f"Update catalog price for {model} to "
                f"\u20b9 {new_price:,.2f}?\n\n"
                f"This affects all future quotations for this model."
            )

        ok = messagebox.askyesno(
            "Update catalog price",
            msg,
            parent=self,
        )
        if not ok:
            return False

        # Perform the update
        try:
            from app.services.catalog_admin_service import update_product
            update_product(model, {"price": new_price})
            messagebox.showinfo(
                "Catalog updated",
                f"Catalog price for {model} is now \u20b9 {new_price:,.2f}.",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror(
                "Catalog update failed",
                f"Could not update catalog:\n{e}",
                parent=self,
            )

        return True

    def _auto_save_customer(self, data):
        """Save the current quotation's customer to the customer database
        if they don't already exist. Called before generating a quotation.
        """
        try:
            from app.services.customer_service import (
                save_customer,
                find_duplicate,
                touch_last_used,
            )
        except Exception:
            return

        name = (data.get("customer_name") or "").strip()
        company = (data.get("company") or "").strip()
        phone = (data.get("phone") or "").strip()
        email = (data.get("email") or "").strip()

        if not name and not company:
            return

        try:
            existing = find_duplicate(name, company, phone, email)
        except Exception:
            existing = None

        if existing:
            try:
                cid = existing.get("id")
                if cid:
                    touch_last_used(cid)
            except Exception:
                pass
            return

        try:
            payload = {
                "name": name,
                "company": company,
                "phone": phone,
                "email": email,
                "address": (data.get("address") or "").strip(),
                "city": (data.get("city") or "").strip(),
                "state": (data.get("state") or "").strip(),
                "pincode": (data.get("pincode") or "").strip(),
                "gstin": (data.get("gstin") or "").strip(),
            }
            save_customer(payload)
        except Exception:
            pass


    def _show_preview(self, data):
        """Generate the PDF immediately and display it (Crystal style)."""
        import tkinter as tk
        from tkinter import messagebox
        import os
        import queue
        import threading
        
        # Parent the preview to the dashboard, not to this form: the form is
        # dismissed once the quotation is generated and must not take the
        # preview window down with it.
        owner = getattr(self, "app", None)
        if not isinstance(owner, (tk.Tk, tk.Toplevel)):
            owner = self.master if isinstance(self.master, (tk.Tk, tk.Toplevel)) else self
        preview_win = tk.Toplevel(owner)
        doc_label = (
            "Proforma Invoice"
            if str(data.get("doc_type", "")).lower().startswith("prof")
            else "Quotation"
        )
        preview_win.title(f"{doc_label} Preview")
        preview_win.geometry("850x950")
        preview_win.configure(bg=T.BG)
        
        # Use grid layout for guaranteed visibility
        preview_win.grid_rowconfigure(1, weight=1)
        preview_win.grid_columnconfigure(0, weight=1)
        
        # Header
        tk.Label(preview_win, text=f"{doc_label} preview", bg=T.BG, fg=T.TEXT, font=T.FONT_H2).grid(row=0, column=0, pady=10)
        
        # Image Frame
        image_frame = tk.Frame(preview_win, bg=T.BG)
        image_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        status_label = tk.Label(image_frame, text="Generating PDF… please wait.", bg=T.BG, fg=T.TEXT_MUTED, font=T.FONT_BODY)
        status_label.pack(expand=True)
        
        # Buttons (row 2)
        btn_frame = tk.Frame(preview_win, bg=T.BG)
        btn_frame.grid(row=2, column=0, pady=10)
        
        # Tk widgets must only be touched from the main thread, so the
        # worker posts UI updates here and the main thread drains them.
        ui_queue = queue.Queue()

        def post_update(fn):
            ui_queue.put(fn)

        def poll_updates():
            while True:
                try:
                    fn = ui_queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    fn()
                except Exception as e:
                    print(f"[preview] UI update failed: {e}")
            try:
                if preview_win.winfo_exists():
                    preview_win.after(60, poll_updates)
            except Exception:
                pass

        poll_updates()

        def do_generate():
            try:
                result = self._do_generate_final(data)
                if not result:
                    post_update(lambda: status_label.config(text="Generation failed."))
                    return
                
                latest_pdf = result.get("pdf_path")

                if not latest_pdf or not os.path.exists(latest_pdf):
                    # Word can be busy and fail transiently. Retry from the
                    # Word file that was just saved before giving up.
                    docx_path = result.get("docx_path")
                    if docx_path and os.path.exists(docx_path):
                        post_update(lambda: status_label.config(text="PDF conversion failed - retrying..."))
                        try:
                            from pathlib import Path
                            import shutil
                            from quotation_generator_crystal import _convert_docx_to_pdf
                            try:
                                from quotation_generator_crystal import get_pdf_dir
                            except ImportError:
                                get_pdf_dir = None

                            retry_pdf = _convert_docx_to_pdf(Path(docx_path))
                            if retry_pdf and retry_pdf.exists():
                                try:
                                    pdf_dir = get_pdf_dir() if get_pdf_dir else None
                                    if pdf_dir is None:
                                        pdf_dir = Path(docx_path).parent.parent / "pdf"
                                        pdf_dir.mkdir(parents=True, exist_ok=True)
                                    final_pdf = pdf_dir / retry_pdf.name
                                    if str(final_pdf) != str(retry_pdf):
                                        shutil.copy2(retry_pdf, final_pdf)
                                        retry_pdf = final_pdf
                                except Exception as e:
                                    print(f"[preview] Could not move PDF: {e}")

                                latest_pdf = str(retry_pdf)
                                result["pdf_path"] = latest_pdf
                                try:
                                    from app.services.quotation_history_service import update_quotation_pdf_path
                                    update_quotation_pdf_path(result.get("quotation_number"), latest_pdf)
                                except Exception:
                                    pass
                        except Exception as e:
                            print(f"[preview] PDF retry failed: {e}")

                if not latest_pdf or not os.path.exists(latest_pdf):
                    post_update(lambda: status_label.config(
                        text="PDF could not be generated. The Word file was saved successfully."
                    ))
                    return
                
                try:
                    import fitz
                except ImportError:
                    post_update(lambda: status_label.config(
                        text="PDF saved, but the preview needs PyMuPDF "
                             "(pip install pymupdf)."
                    ))
                    return
                doc = fitz.open(latest_pdf)
                page = doc[0]
                # Render close to the preview width; the Pillow-less
                # fallback cannot scale smoothly, so avoid a 2x bitmap.
                zoom = 2.0 if Image is not None else 1.35
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                img = (
                    Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    if Image is not None
                    else None
                )
                ppm_data = None if img is not None else pix.tobytes("ppm")
                doc.close()
                
                def show_image():
                    win_width = preview_win.winfo_width() - 40
                    if win_width < 100:
                        win_width = 760
                    if img is not None:
                        ratio = win_width / img.width
                        new_height = int(img.height * ratio)
                        resized_img = img.resize((win_width, new_height), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(resized_img)
                    else:
                        # Pillow is not installed: Tk can load PPM directly.
                        # It only scales by whole factors, so shrink by the
                        # smallest factor that fits the window.
                        photo = tk.PhotoImage(data=ppm_data)
                        while photo.width() > win_width and photo.width() // 2 > 100:
                            photo = photo.subsample(2, 2)
                    
                    status_label.pack_forget()
                    canvas = tk.Canvas(image_frame, bg=T.BG, highlightthickness=0)
                    scrollbar = ttk.Scrollbar(image_frame, orient="vertical", command=canvas.yview)
                    canvas.configure(yscrollcommand=scrollbar.set)
                    scrollbar.pack(side="right", fill="y")
                    canvas.pack(side="left", fill="both", expand=True)
                    canvas.create_image(0, 0, anchor="nw", image=photo)
                    canvas.image = photo
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                    gen_btn.config(state="normal", text="Generate Again")

                    # The quotation is saved and previewed; take the editor
                    # out of the way so only the preview stays on screen.
                    try:
                        self.withdraw()
                    except Exception:
                        pass
                
                post_update(show_image)
                
            except Exception as e:
                err_msg = str(e)
                post_update(lambda: status_label.config(text=f"Error: {err_msg}"))
        
        # Start generation in background
        threading.Thread(target=do_generate, daemon=True).start()
        
        gen_btn = tk.Button(btn_frame, text="Generate PDF", bg=T.ACCENT, fg="white", activebackground=T.ACCENT_DARK, activeforeground="white", font=T.FONT_BODY_B, relief="flat", bd=0, highlightthickness=0, cursor="hand2", command=lambda: threading.Thread(target=do_generate, daemon=True).start(), padx=20, pady=7)
        gen_btn.pack(side="left", padx=10)
        
        def close_preview():
            try:
                preview_win.destroy()
            finally:
                # Closing the preview finishes the whole flow.
                try:
                    self.destroy()
                except Exception:
                    pass

        preview_win.protocol("WM_DELETE_WINDOW", close_preview)
        tk.Button(btn_frame, text="Close", bg=T.SURFACE, fg=T.TEXT_BODY, activebackground=T.SURFACE_HOVER, activeforeground=T.TEXT, font=T.FONT_BODY, relief="flat", bd=0, highlightthickness=1, highlightbackground=T.BORDER, cursor="hand2", command=close_preview, padx=20, pady=6).pack(side="left", padx=10)


    def _open_latest_pdf(self):
        """Find the latest PDF in Downloads and open it."""
        import os
        import subprocess
        import platform
        from tkinter import messagebox
        
        home = os.path.expanduser("~")
        downloads_folder = os.path.join(home, "Downloads", "CrystalQuotation")
        
        latest_pdf = None
        latest_mtime = 0
        
        if os.path.exists(downloads_folder):
            for root, dirs, files in os.walk(downloads_folder):
                if "pdf" in root:
                    for f in files:
                        if f.endswith(".pdf"):
                            full_path = os.path.join(root, f)
                            mtime = os.path.getmtime(full_path)
                            if mtime > latest_mtime:
                                latest_mtime = mtime
                                latest_pdf = full_path
        
        if latest_pdf:
            if platform.system() == 'Windows':
                os.startfile(latest_pdf)
            elif platform.system() == 'Darwin':
                subprocess.call(['open', latest_pdf])
            else:
                subprocess.call(['xdg-open', latest_pdf])
        else:
            messagebox.showwarning("Preview", "PDF generated but could not be found in Downloads.", parent=self)


    def _do_generate_final(self, data):
        """Actually generate the PDF and Word files."""
        try:
            result = generate_quotation(**{
                "customer_name": data.get("customer_name", ""),
                "company": data.get("company", ""),
                "address": data.get("address", ""),
                "phone": data.get("phone", ""),
                "email": data.get("email", ""),
                "contact_person": data.get("contact_person", ""),
                "city": data.get("city", ""),
                "state": data.get("state", ""),
                "pincode": data.get("pincode", ""),
                "country": data.get("country", ""),
                "gstin": data.get("gstin", ""),
                "model": data.get("model", ""),
                "machine_price": data.get("machine_price", 0),
                "machine_qty": data.get("machine_qty", 1),
                "accessories": data.get("accessories", []),
                "transportation": float(data.get("transportation", 0)),
                "packing_mode": data.get("packing_mode", "Percentage (%)"),
                "packing_value": data.get("packing_value", 0),
                "packing_percent": data.get("packing_percent", 3.5),
                "cgst_percent": data.get("cgst_percent", 9),
                "sgst_percent": data.get("sgst_percent", 9),
                "igst_percent": data.get("gst_rate", 18) if data.get("gst_type") == "IGST" else None,
                "gst_type": data.get("gst_type", "CGST + SGST"),
                "gst_rate": data.get("gst_rate", 18),
                "selected_terms": data.get("selected_terms", []),
                "items": data.get("items", []),
                "quotation_number": data.get("quotation_number"),
                "doc_type": data.get("doc_type", "quotation"),
            })
            return result  # Return the dict with paths!
        except Exception as e:
            print(f"Generation Error: {e}")
            return None

    def _generate_quotation(self):
        """Generate the quotation from the Terms step."""
        try:
            data = self.get_form_data()
            
            # --- FORCE SAVE CUSTOMER TO CLOUD BEFORE QUOTATION ---
            try:
                from app.services.cloud_sync import upload_customer_to_cloud
                from app.services.paths import get_active_module
                
                cust_data = {
                    "name": data.get("customer_name", ""),
                    "company": data.get("company", ""),
                    "phone": data.get("phone", ""),
                    "email": data.get("email", ""),
                    "address": data.get("address", ""),
                    "city": data.get("city", ""),
                    "state": data.get("state", ""),
                    "pincode": data.get("pincode", ""),
                    "gstin": data.get("gstin", "")
                }
                
                if cust_data["name"] or cust_data["company"]:
                    print("[UI] Force saving customer to cloud...")
                    upload_customer_to_cloud(cust_data, module=get_active_module())
            except Exception as e:
                print(f"[UI] Customer save failed: {e}")
            
            self._auto_save_customer(data)
            self._show_preview(data)
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Generation Error", f"Error: {e}", parent=self)

    
    def clear_form(self):
        confirm = messagebox.askyesno("Clear quotation", "Clear the current quotation and start again?", parent=self)
        if not confirm:
            return
        self.customer_name.set("")
        self.company.set("")
        self.contact_person.set("")
        self.address.set("")
        self.city.set("")
        self.state.set("")
        self.pincode.set("")
        self.country.set("India")
        self.phone.set("")
        self.email.set("")
        self.gstin.set("")
        categories = self._get_categories()
        if categories:
            self.category.set(categories[0])
        models = self._get_models(self.category.get())
        if models:
            self.model.set(models[0])
        else:
            self.model.set("")
        self.machine_price.set("")
        self.machine_qty.set("1")
        self.transportation.set("0")
        self.packing_mode.set("Percentage (%)")
        self.packing_value.set("3.5")
        self.packing_percent.set("3.5")
        self.gst_type.set("CGST + SGST")
        self.gst_rate.set("18")
        self.cgst_percent.set("9")
        self.sgst_percent.set("9")
        self.include_terms.set(False)
        self.completed_steps.clear()
        self.items = []
        self.term_rows = []
        self._revision_number = None
        try:
            self.doc_type.set("quotation")
        except Exception:
            pass
        try:
            self.header_sub_label.configure(text=self._header_subtitle())
            self.title(f"CRYSTAL | ARMATECH ASSOCIATES — New {self._doc_label()}")
        except Exception:
            pass
        self._load_step(1)
        try:
            self.canvas.yview_moveto(0)
        except Exception:
            pass

    def _open_customer_lookup(self):
        import threading
        from app.services import customer_service

        self.config(cursor="watch")
        self.update()

        def fetch_and_show():
            try:
                if hasattr(customer_service, "list_customers"):
                    records = customer_service.list_customers()
                else:
                    records = customer_service.get_all_customers()
            except Exception:
                records = []

            self.after(0, lambda: self._show_customer_picker(records))
            self.after(0, lambda: self.config(cursor=""))

        threading.Thread(target=fetch_and_show, daemon=True).start()

    def _show_customer_picker(self, records):
        touch_last_used = getattr(
            __import__('app.services.customer_service', fromlist=['touch_last_used']),
            "touch_last_used",
            None
        )

        records = records or []

        if not records:
            messagebox.showinfo(
                "No saved customers",
                "You have not saved any customers yet.\n\n"
                "Open the Customer Database from the dashboard to add one.",
                parent=self,
            )
            return

        picker = tk.Toplevel(self)
        picker.title("Pick a saved customer")
        picker.geometry("640x540")
        picker.configure(bg=self.BG)
        picker.transient(self)
        picker.grab_set()
        W.set_window_icon(picker)
        W.apply_ttk_theme(picker)

        tk.Label(
            picker, text="SAVED CUSTOMERS",
            bg=self.BG, fg=T.TEXT_MUTED,
            font=T.FONT_LABEL,
        ).pack(anchor="w", padx=24, pady=(20, 2))
        tk.Label(
            picker, text="Pick a customer to fill the form",
            bg=self.BG, fg=T.TEXT,
            font=T.FONT_H2,
        ).pack(anchor="w", padx=24, pady=(0, 12))

        # ── Search entry (debounced) ──────────────────────────────
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            picker, textvariable=search_var,
            bg=T.SURFACE, fg=self.TEXT,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=self.BORDER,
            highlightcolor=T.FOCUS,
            font=T.FONT_BODY, insertbackground=self.RED,
        )
        search_entry.pack(fill="x", padx=24, ipady=6, pady=(0, 4))
        search_entry.focus_set()

        tk.Label(
            picker, text="Type a name, company or phone number",
            bg=self.BG, fg=T.TEXT_FAINT, font=T.FONT_TINY,
        ).pack(anchor="w", padx=26, pady=(0, 10))

        btn_row = tk.Frame(picker, bg=T.SURFACE,
                           highlightbackground=self.BORDER,
                           highlightthickness=1)
        btn_row.pack(side="bottom", fill="x")

        tk.Button(
            btn_row, text="Cancel", command=picker.destroy,
            bg=T.SURFACE, fg=T.TEXT_BODY,
            activebackground=T.SURFACE_HOVER,
            activeforeground=T.TEXT,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=self.BORDER,
            font=T.FONT_BODY, cursor="hand2",
            padx=20, pady=7,
        ).pack(side="right", padx=(8, 24), pady=14)

        tk.Button(
            btn_row, text="Use selected",
            command=lambda: apply_selection(),
            bg=self.RED, fg="white",
            activebackground=self.RED_DARK,
            activeforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=T.FONT_BODY_B, cursor="hand2",
            padx=22, pady=8,
        ).pack(side="right", pady=14)

        list_wrap = tk.Frame(
            picker, bg=T.SURFACE,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        list_wrap.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        listbox = tk.Listbox(
            list_wrap,
            bg=T.SURFACE, fg=self.TEXT,
            relief="flat", bd=0, highlightthickness=0,
            font=T.FONT_BODY,
            activestyle="none",
            selectbackground=T.ACCENT_SOFT,
            selectforeground=self.TEXT,
        )
        listbox.pack(fill="both", expand=True, padx=2, pady=2)

        def customer_value(record, *keys):
            for key in keys:
                value = record.get(key, "")
                if value not in (None, ""):
                    return str(value)
            return ""

        records.sort(key=lambda r: customer_value(r, "name", "contact_person").lower())

        VISIBLE_CAP = 200
        _state = {"filtered": [], "after_id": None}

        def _render(filtered):
            _state["filtered"] = filtered
            listbox.delete(0, "end")
            for r in filtered[:VISIBLE_CAP]:
                label = (
                    f"{customer_value(r, 'name', 'contact_person')}  -  "
                    f"{customer_value(r, 'company', 'company_name')}  -  "
                    f"{customer_value(r, 'phone')}"
                )
                listbox.insert("end", label)

        def _apply_filter():
            q = search_var.get().strip().lower()
            if not q:
                _render(records)
                return
            matches = [
                r for r in records
                if q in customer_value(r, "name", "contact_person").lower()
                or q in customer_value(r, "company", "company_name").lower()
                or q in customer_value(r, "phone").lower()
            ]
            _render(matches)

        def _on_type(*_):
            if _state["after_id"]:
                picker.after_cancel(_state["after_id"])
            _state["after_id"] = picker.after(250, _apply_filter)

        search_var.trace_add("write", _on_type)
        _apply_filter()

        def apply_selection():
            sel = listbox.curselection()
            if not sel:
                return
            record = _state["filtered"][sel[0]]

            self.customer_name.set(customer_value(record, 'name', 'contact_person'))
            self.company.set(customer_value(record, 'company', 'company_name'))
            self.contact_person.set("")
            self.address.set(customer_value(record, 'address'))
            self.city.set(customer_value(record, 'city'))
            self.state.set(customer_value(record, 'state'))
            self.pincode.set(customer_value(record, 'pincode', 'pin'))
            self.country.set(customer_value(record, 'country') or "India")
            self.gstin.set(customer_value(record, 'gstin').upper())
            self.phone.set(customer_value(record, 'phone'))
            self.email.set(customer_value(record, 'email'))

            try:
                if touch_last_used:
                    touch_last_used(record.get("id"))
            except Exception:
                pass

            self._update_summary()
            picker.destroy()

        listbox.bind("<Double-Button-1>", lambda e: apply_selection())

    def _open_preview(self):
        if not self._validate_customer():
            self._load_step(1)
            return
        if not self._validate_product():
            self._load_step(2)
            return
        if not self._validate_pricing():
            self._load_step(4)
            return

        data = self.get_form_data()

        try:
            from app.services.cloud_sync import upload_customer_to_cloud
            from app.services.paths import get_active_module
            
            cust_data = {
                "name": data.get("customer_name", ""),
                "company": data.get("company", ""),
                "phone": data.get("phone", ""),
                "email": data.get("email", ""),
                "address": data.get("address", ""),
                "city": data.get("city", ""),
                "state": data.get("state", ""),
                "pincode": data.get("pincode", ""),
                "gstin": data.get("gstin", "")
            }
            
            if cust_data["name"] or cust_data["company"]:
                upload_customer_to_cloud(cust_data, module=get_active_module())
        except Exception:
            pass
        
        self._auto_save_customer(data)
        self._show_preview(data)
