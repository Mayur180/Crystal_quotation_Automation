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


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


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

    BG = "#F4F5F7"
    CARD = "#FFFFFF"

    TEXT = "#17191D"
    MUTED = "#747A84"
    LIGHT_MUTED = "#9BA1AA"

    BORDER = "#E1E4E8"

    RED = "#C40000"
    RED_DARK = "#980000"
    RED_LIGHT = "#FFF3F3"

    GREEN = "#16804B"
    GREEN_LIGHT = "#ECF8F1"

    SOFT = "#F8F9FA"


    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, app=None, parent=None, prefill=None):

        super().__init__(parent or app)

        self.app = app

        self.title(
            "CRYSTAL | ARMATECH ASSOCIATES — New Quotation"
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

        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Crystal.TCombobox",
            fieldbackground="white",
            background="white",
            foreground=self.TEXT,
            bordercolor=self.BORDER,
            lightcolor=self.BORDER,
            darkcolor=self.BORDER,
            padding=8,
            font=("Arial", 10),
        )

        style.map(
            "Crystal.TCombobox",
            fieldbackground=[
                ("readonly", "white")
            ],
            foreground=[
                ("readonly", self.TEXT)
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

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Scrollbar intentionally hidden; mouse-wheel scrolling remains enabled.
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
            height=82
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        brand = tk.Frame(
            header,
            bg=self.CARD
        )

        brand.pack(
            side="left",
            padx=30
        )

        tk.Label(
            brand,
            text="CRYSTAL",
            bg=self.CARD,
            fg=self.RED,
            font=("Arial", 23, "bold")
        ).pack(
            side="left",
            pady=17
        )

        tk.Label(
            brand,
            text="  /  New Quotation",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Arial", 11)
        ).pack(
            side="left",
            pady=21
        )

        company = tk.Frame(
            header,
            bg=self.CARD
        )

        company.pack(
            side="right",
            padx=30
        )

        tk.Label(
            company,
            text="ARMATECH ASSOCIATES",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Arial", 12, "bold")
        ).pack(
            anchor="e",
            pady=(14, 1)
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
            font=("Arial", 9)
        ).pack(
            anchor="e"
        )

        tk.Frame(
            header,
            bg=self.RED,
            height=3
        ).pack(
            side="bottom",
            fill="x"
        )


    # ========================================================
    # STEPPER
    # ========================================================

    def _build_stepper(self):

        self.stepper = tk.Frame(
            self,
            bg=self.CARD,
            height=88
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
            padx=42,
            pady=16
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
                bg="#E9EBEE",
                fg="#737983",
                width=3,
                font=("Arial", 10, "bold")
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
                padx=8
            )

            title_label = tk.Label(
                text_box,
                text=title,
                bg=self.CARD,
                fg=self.MUTED,
                font=("Arial", 9, "bold")
            )

            title_label.pack(
                anchor="w"
            )

            subtitle_label = tk.Label(
                text_box,
                text=subtitle,
                bg=self.CARD,
                fg=self.LIGHT_MUTED,
                font=("Arial", 8)
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
                    bg="#E5E7EA",
                    height=2
                ).pack(
                    side="left",
                    fill="x",
                    expand=True,
                    padx=8
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
            width=3,
            font=("Arial", 9, "bold")
        ).pack(
            side="left",
            padx=(0, 10)
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
            font=("Arial", 16, "bold")
        ).pack(
            anchor="w"
        )

        tk.Label(
            text_box,
            text=subtitle,
            bg=self.CARD,
            fg=self.MUTED,
            font=("Arial", 9)
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

        label_text = label

        if required:
            label_text += "  *"

        tk.Label(
            box,
            text=label_text,
            bg=self.CARD,
            fg=self.TEXT,
            font=("Arial", 9, "bold")
        ).pack(
            anchor="w",
            pady=(0, 6)
        )

        entry = tk.Entry(
            box,
            textvariable=variable,
            bg="white",
            fg=self.TEXT,
            relief="solid",
            bd=1,
            font=("Arial", 10),
            insertbackground=self.RED
        )

        entry.pack(
            fill="x",
            ipady=7
        )

        return box


    # ========================================================
    # STEP 1 — CUSTOMER
    # ========================================================

    def _render_customer(self):

        self._clear_content()

        card = self._create_card(
            self.content_area
        )

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
            label_row, text="Customer name",
            bg=self.CARD, fg=self.TEXT,
            font=("Arial", 9, "bold")
        ).pack(side="left")

        tk.Button(
            label_row,
            text="🔍  Lookup Saved",
            command=self._open_customer_lookup,
            bg=self.SOFT, fg=self.TEXT,
            activebackground="#ECEEF1", activeforeground=self.TEXT,
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 8, "bold"), cursor="hand2",
            padx=8, pady=2,
        ).pack(side="right")

        tk.Entry(
            name_box, textvariable=self.customer_name,
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 10), insertbackground=self.RED,
        ).pack(fill="x", ipady=7)

        self._make_entry(
            grid, "Company", self.company, True
        ).grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=7)

        self._make_entry(
            grid, "Contact Person", self.contact_person, False
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
        city_entry.bind(
            "<KeyRelease>",
            self._auto_fill_state_from_city,
            add="+"
        )

        state_box = tk.Frame(grid, bg=self.CARD)
        state_box.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=7)

        tk.Label(
            state_box, text="State",
            bg=self.CARD, fg=self.TEXT,
            font=("Arial", 9, "bold")
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
            card, bg=self.RED_LIGHT
        )
        note.pack(fill="x", pady=(15, 0))

        tk.Label(
            note,
            text="* Required field  •  GSTIN is optional for non-GST customers, but must be valid when entered.",
            bg=self.RED_LIGHT, fg=self.RED_DARK,
            font=("Arial", 9)
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

        top = tk.Frame(card, bg=self.CARD)
        top.pack(fill="x", pady=(0, 20))

        tk.Label(top, text="PRODUCT CATEGORY", bg=self.CARD, fg=self.MUTED, font=("Arial", 8, "bold")).pack(anchor="w")
        self.category_combo = ttk.Combobox(top, textvariable=self.category, values=self._get_categories(), state="readonly", style="Crystal.TCombobox")
        self.category_combo.pack(fill="x", pady=(6, 16))
        self.category_combo.bind("<<ComboboxSelected>>", self._category_changed)

        tk.Label(top, text="SELECT MODEL", bg=self.CARD, fg=self.MUTED, font=("Arial", 8, "bold")).pack(anchor="w")
        self.model_combo = ttk.Combobox(top, textvariable=self.model, values=self._get_models(self.category.get()), state="normal", style="Crystal.TCombobox")
        self.model_combo.pack(fill="x", pady=(6, 16))
        self.model_combo.bind("<<ComboboxSelected>>", self._model_changed)
        self.model_combo.bind("<KeyRelease>", self._on_model_keyrelease)

        row = tk.Frame(top, bg=self.CARD)
        row.pack(fill="x", pady=10)
        tk.Label(row, text="Price (₹)", bg=self.CARD, fg=self.MUTED, font=("Arial", 8, "bold")).pack(side="left", padx=(0, 5))
        tk.Entry(row, textvariable=self.machine_price, width=10, font=("Arial", 10)).pack(side="left", padx=(0, 20))

        tk.Label(row, text="Qty", bg=self.CARD, fg=self.MUTED, font=("Arial", 8, "bold")).pack(side="left", padx=(0, 5))
        tk.Entry(row, textvariable=self.machine_qty, width=6, font=("Arial", 10)).pack(side="left", padx=(0, 20))

        # --- Discount UI ---
        tk.Label(row, text="Discount:", bg=self.CARD, fg=self.MUTED, font=("Arial", 8, "bold")).pack(side="left", padx=(0, 5))
        
        self.disc_mode = tk.StringVar(value="Amount (₹)")
        disc_mode_box = ttk.Combobox(row, textvariable=self.disc_mode, values=["Amount (₹)", "Percentage (%)"], state="readonly", width=12, font=("Arial", 9))
        disc_mode_box.pack(side="left", padx=(0, 5))
        
        self.disc_var = tk.StringVar(value="0")
        tk.Entry(row, textvariable=self.disc_var, width=8, font=("Arial", 10)).pack(side="left", padx=(0, 20))
        
        tk.Button(top, text="➕ Add to Quotation", bg="#C40000", fg="white", font=("Arial", 10, "bold"), relief="flat", command=self._add_item_to_cart).pack(anchor="e", pady=10)

        self.cart_frame = tk.Frame(card, bg=self.CARD)
        self.cart_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        cols = ("model", "qty", "price", "discount", "total")
        self.cart_tree = ttk.Treeview(self.cart_frame, columns=cols, show="headings", height=6)
        for c, w, t in [("model", 200, "Model"), ("qty", 60, "Qty"), ("price", 100, "Price"), ("discount", 100, "Discount"), ("total", 100, "Total")]:
            self.cart_tree.heading(c, text=t)
            self.cart_tree.column(c, width=w, anchor="w")
        
        vsb = ttk.Scrollbar(self.cart_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=vsb.set)
        self.cart_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tk.Button(card, text="🗑 Remove Selected", bg=self.SOFT, fg=self.TEXT, font=("Arial", 9), command=self._remove_cart_item).pack(anchor="w", pady=10)

        self._refresh_cart_table()

    def _add_item_to_cart(self, silent=False):
        model = self.model.get().strip()
        if not model:
            if not silent: messagebox.showwarning("Empty", "Select a model first.", parent=self)
            return
        try: price = float(str(self.machine_price.get() or "0").strip() or "0")
        except: price = 0.0
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
        
        if mode_val == "Percentage (%)":
            disc = subtotal * (disc_val / 100.0)
        else:
            disc = disc_val
            
        # Ensure discount doesn't exceed subtotal
        if disc > subtotal:
            disc = subtotal
            
        total = subtotal - disc
        self.items.append({"model": model, "price": price, "qty": qty, "discount": disc, "total": total})
        self._refresh_cart_table()
        self.model.set("")
        self.machine_price.set("")
        self.machine_qty.set("1")
        self.disc_var.set("0")

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
                item["model"], item["qty"], f"₹{item['price']:,.0f}", f"₹{item['discount']:,.0f}", f"₹{item['total']:,.0f}"
            ))

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
        model = self.model.get()

        if not model:
            self.product_title.set("Select a machine")
            self.product_subtitle.set("")
            self.machine_price.set("")
            self._recalculate()
            return

        size = MODEL_SIZE.get(
            model,
            "Catalog specification available"
        )

        self.product_title.set(
            f"CRYSTAL  •  {model}"
        )

        self.product_subtitle.set(
            f"{self.category.get()}   ·   "
            f"Measuring range / size: {size}"
        )

        # --------------------------------------------------------
        # AUTO-FILL PRICE FROM CATALOG
        # --------------------------------------------------------
        auto_price = None

        if get_product is not None:
            try:
                product = get_product(model)
                if isinstance(product, dict):
                    raw = product.get("price")
                    if raw not in (None, ""):
                        auto_price = raw
            except Exception:
                auto_price = None

        if auto_price is not None:
            try:
                from decimal import Decimal as _Dec
                d = _Dec(str(auto_price))
                if d == d.to_integral_value():
                    self.machine_price.set(str(int(d)))
                else:
                    self.machine_price.set(str(d))
            except Exception:
                self.machine_price.set(str(auto_price))
        else:
            self.machine_price.set("")

        # Update summary panel
        try:
            self._recalculate()
        except Exception:
            pass
        try:
            self._update_summary()
        except Exception:
            pass


    # ========================================================
    # PRODUCT VALIDATION
    # ========================================================

    def _validate_product(self):
        """Only MODEL is required."""
        model = (self.model.get() or "").strip()
        if not model:
            messagebox.showerror(
                "Product required",
                "Please select a model.",
                parent=self,
            )
            return False
        return True


    # ========================================================
    # GET ACCESSORIES  (from catalog — active only)
    # ========================================================

    # ========================================================
    # STEP 4 — PRICING
    # ========================================================

    def _render_pricing(self):
        self._clear_content()
        card = self._create_card(self.content_area)
        self._section_header(card, 3, "Final pricing", "Review the commercial calculation before continuing.")

        # 1. Calculate Cart Total
        items_total = sum(float(item.get("total", 0)) for item in getattr(self, "items", []))
        
        # 2. Get Packing and GST from the inputs
        try:
            packing_val = float(self.packing_value.get() or "0")
            if self.packing_mode.get() == "Percentage (%)":
                packing_amt = items_total * (packing_val / 100.0)
            else:
                packing_amt = packing_val
        except Exception:
            packing_amt = 0.0
            
        try:
            gst_rate = float(self.gst_rate.get() or "0")
        except Exception:
            gst_rate = 0.0
            
        try:
            transport = float(self.transportation.get() or "0")
        except Exception:
            transport = 0.0

        # --- Single Packing UI ---
        packing_ctrl_frame = tk.Frame(card, bg=self.CARD)
        packing_ctrl_frame.pack(fill="x", pady=(10, 10))
        
        tk.Label(packing_ctrl_frame, text="Packing Type:", bg=self.CARD, fg=self.TEXT, font=("Arial", 9, "bold")).pack(side="left", padx=(0, 5))
        
        packing_mode_box = ttk.Combobox(
            packing_ctrl_frame,
            textvariable=self.packing_mode,
            values=["Percentage (%)", "Amount (₹)", "No Packing"],
            state="readonly",
            width=15
        )
        packing_mode_box.pack(side="left", padx=(0, 15))
        
        
        tk.Label(packing_ctrl_frame, text="Value:", bg=self.CARD, fg=self.TEXT, font=("Arial", 9, "bold")).pack(side="left", padx=(0, 5))
        
        packing_val_entry = tk.Entry(packing_ctrl_frame, textvariable=self.packing_value, width=10)
        packing_val_entry.pack(side="left")
        
        # -------------------------

        # 3. Calculate GST (Fixed Math)
        try:
            pack_val = float(self.packing_value.get() or 0)
        except ValueError:
            pack_val = 0.0
            
        packing_amt = 0.0
        mode = self.packing_mode.get()
        
        # Strict check to ensure "No Packing" zeroes it out
        if mode == "No Packing":
            packing_amt = 0.0
        elif mode == "Percentage (%)":
            packing_amt = items_total * (pack_val / 100.0)
        elif mode == "Amount (₹)":
            packing_amt = pack_val
            
        taxable = items_total + packing_amt + transport
        gst_amt = taxable * (gst_rate / 100.0)
        cgst = gst_amt / 2.0
        sgst = gst_amt / 2.0
        
        grand = taxable + gst_amt



        # 4. Display Rows
        fmt = lambda v: f"₹{v:,.2f}"
        rows = [
            ("Machine (Cart Total)", fmt(items_total)),
            *([("Packing", fmt(packing_amt))] if packing_amt > 0 else []),
            ("Transportation", fmt(transport)),
            ("BuyBack Offer", "₹0.00"),
            ("Taxable Value", fmt(taxable)),
            (f"CGST ({gst_rate/2:g}%)", fmt(cgst)),
            (f"SGST ({gst_rate/2:g}%)", fmt(sgst)),
            ("IGST (0%)", "₹0.00"),
            ("GRAND TOTAL", fmt(grand))
        ]

        for label, value in rows:
            row = tk.Frame(card, bg=self.CARD)
            row.pack(fill="x", pady=6)
            # Make the Grand Total bold
            font_style = ("Arial", 11, "bold") if label == "GRAND TOTAL" else ("Arial", 10)
            tk.Label(row, text=label, bg=self.CARD, fg=self.TEXT, font=font_style).pack(side="left")
            tk.Label(row, text=value, bg=self.CARD, fg=self.TEXT, font=font_style).pack(side="right")

        self._recalculate()

    def _render_terms(self):

        self._clear_content()

        card = self._create_card(
            self.content_area
        )

        self._section_header(
            card,
            5,
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
            text="✎  Edit Terms & Conditions",
            command=self._open_terms_editor,
            bg=self.SOFT,
            fg=self.TEXT,
            activebackground="#ECEEF1",
            activeforeground=self.TEXT,
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=14,
            pady=7
        ).pack(
            side="left"
        )

        tk.Button(
            action_bar,
            text="↺  Restore Defaults",
            command=self._restore_default_terms,
            bg="white",
            fg=self.MUTED,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Arial", 9),
            cursor="hand2",
            padx=14,
            pady=7
        ).pack(
            side="left",
            padx=(8, 0)
        )

        tk.Button(
            action_bar,
            text="👁  Preview Quotation",
            command=self._open_preview,
            bg=self.GREEN,
            fg="white",
            activebackground="#0F5A35",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=14,
            pady=7
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
            font=("Arial", 10, "bold")
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
                font=("Arial", 9, "italic")
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
                font=("Arial", 9, "bold")
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
                font=("Arial", 9)
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
            font=("Arial", 8, "bold")
        ).pack(
            anchor="w"
        )

        tk.Label(
            header,
            text="Live summary",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Arial", 17, "bold")
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

        self.summary_customer = tk.Label(
            outer,
            text="Customer not added",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Arial", 10, "bold"),
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
            font=("Arial", 9),
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
            font=("Arial", 10, "bold"),
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
            font=("Arial", 8, "bold")
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
            font=("Arial", 25, "bold"),
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
            bg=self.RED_LIGHT,
            fg=self.RED_DARK,
            font=("Arial", 9, "bold"),
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
            bg="white",
            height=78,
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
            bg="white"
        )

        left_group.pack(
            side="left",
            padx=26
        )

        self.back_button = tk.Button(
            left_group,
            text="←  Back",
            command=self._back,
            bg="white",
            fg=self.TEXT,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="solid",
            bd=1,
            highlightthickness=0,
            width=12,
            height=2,
            font=("Arial", 9, "bold"),
            cursor="hand2"
        )

        self.back_button.pack(
            side="left",
            padx=(0, 8),
            pady=15
        )

        self.clear_button = tk.Button(
            left_group,
            text="Clear",
            command=self.clear_form,
            bg="white",
            fg=self.MUTED,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            width=9,
            height=2,
            font=("Arial", 9),
            cursor="hand2"
        )

        self.clear_button.pack(
            side="left",
            padx=4,
            pady=15
        )

        right_group = tk.Frame(
            self.navigation,
            bg="white"
        )

        right_group.pack(
            side="right",
            padx=26
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
            width=28,
            height=2,
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )

        self.generate_button.pack(
            side="right",
            pady=14
        )


    # ========================================================
    # LOAD STEP
    # ========================================================

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
                fg="#B5B8BD"
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

            4: "Review Quotation  →",
        }

        self.generate_button.configure(
            text=button_text.get(
                step,
                "Continue  →"
            ),

            state="normal",

            width=28
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
                    bg="#E9EBEE",
                    fg="#737983"
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

        return {
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
            "transportation": self.transportation.get(),
            "buyback": self.buyback.get(),
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

        # ---- jump to Product page (Step 2) ----
        try:
            self._load_step(2)
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

    def _generate_quotation(self):

        # Ask about catalog update BEFORE validation
        if not self._maybe_update_catalog():
            return

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

        # ---- auto-save new customers before generating ----
        self._auto_save_customer(data)

        if generate_quotation is None:

            messagebox.showerror(
                "Generator unavailable",
                (
                    "The quotation generator could not be imported.\n\n"
                    "Check:\n"
                    "app/generators/quotation_generator.py"
                ),
                parent=self
            )

            return

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
                "country": data.get("country", "India"),
                "gstin": data.get("gstin", ""),
                "model": data.get("model", ""),
                "machine_price": data.get("machine_price", 0),
                "machine_qty": data.get("machine_qty", 1),
                "accessories": data.get("accessories", []),
                "transportation": data.get("transportation", 0),
                "packing_percent": data.get("packing_percent", 3.5),
                "packing_mode": data.get("packing_mode", "Percentage (%)"),
                "packing_value": data.get("packing_value", ""),
                "cgst_percent": data.get("cgst_percent", 9),
                "sgst_percent": data.get("sgst_percent", 9),
                "gst_rate": data.get("gst_rate", 18),
                "gst_type": data.get("gst_type", "CGST + SGST"),
                "selected_terms": data.get("terms", []),
                "items": data.get("items", []),
            })

            output_path = None

            if isinstance(
                result,
                str
            ):

                output_path = result

            elif isinstance(
                result,
                dict
            ):

                output_path = (

                    result.get("word_path")

                    or result.get("docx_path")

                    or result.get("output_path")

                    or result.get("path")
                )

            self.completed_steps.add(
                5
            )

            self._update_stepper()

            if output_path:

                pdf_path = None
                if isinstance(result, dict):
                    pdf_path = (
                        result.get("pdf_path")
                        or result.get("pdf")
                    )

                import sys as _sys
                print(f"[DIALOG] output_path={output_path!r}", file=_sys.stderr)
                print(f"[DIALOG] pdf_path={pdf_path!r}", file=_sys.stderr)
                print(f"[DIALOG] result type={type(result).__name__}", file=_sys.stderr)
                message = (
                    "Quotation generated successfully.\n\n"
                    f"Word file:\n{output_path}"
                )
                if pdf_path:
                    message += f"\n\nPDF file:\n{pdf_path}"

                messagebox.showinfo(
                    "Quotation Generated",
                    message,
                    parent=self
                )

            else:

                messagebox.showinfo(
                    "Quotation Generated",
                    "Quotation generation completed successfully.",
                    parent=self
                )

            self.status_text.set(
                "Quotation generated successfully."
            )
            # ---- Phase 3: close after successful generation ----
            self._close_and_return_to_dashboard()
            return



        except Exception as exc:

            messagebox.showerror(
                "Quotation Generation Error",
                (
                    "The quotation could not be generated.\n\n"
                    f"{type(exc).__name__}: {exc}"
                ),
                parent=self
            )
            
    def _open_customer_lookup(self):
        """Open a small picker; on selection, fill customer fields."""
        try:
            from app.services import customer_service

            if hasattr(customer_service, "list_customers"):
                records = customer_service.list_customers()
            else:
                records = customer_service.get_all_customers()

            touch_last_used = getattr(
                customer_service,
                "touch_last_used",
                None
            )

        except Exception as exc:
            messagebox.showerror(
                "Lookup unavailable",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        records = records or []

        if not records:
            messagebox.showinfo(
                "No saved customers",
                "You have not saved any customers yet.\n\n"
                "Open the Customer Database from the dashboard to add one.",
                parent=self,
            )
            return

        # Simple chooser dialog
        picker = tk.Toplevel(self)
        picker.title("Pick a saved customer")
        picker.geometry("620x480")
        picker.configure(bg=self.BG)
        picker.transient(self)
        picker.grab_set()

        tk.Label(
            picker, text="SELECT A SAVED CUSTOMER",
            bg=self.CARD, fg=self.MUTED,
            font=("Arial", 8, "bold"),
        ).pack(anchor="w", padx=22, pady=(18, 6))

        listbox = tk.Listbox(
            picker,
            bg="white", fg=self.TEXT,
            relief="solid", bd=1,
            font=("Arial", 10),
            activestyle="none",
            selectbackground=self.RED_LIGHT,
            selectforeground=self.TEXT,
        )
        listbox.pack(fill="both", expand=True, padx=22, pady=(0, 12))

        def customer_value(record, *keys):
            for key in keys:
                value = record.get(key, "")
                if value not in (None, ""):
                    return str(value)
            return ""

        for r in records:
            label = (
                f"{customer_value(r, 'name', 'contact_person')}  —  "
                f"{customer_value(r, 'company', 'company_name')}  —  "
                f"{customer_value(r, 'phone')}"
            )
            listbox.insert("end", label)

        def apply_selection():
            sel = listbox.curselection()
            if not sel:
                return
            record = records[sel[0]]

            self.customer_name.set(
                customer_value(record, 'name', 'contact_person')
            )
            self.company.set(
                customer_value(record, 'company', 'company_name')
            )
            self.contact_person.set(
                customer_value(record, 'contact_person')
            )
            self.address.set(
                customer_value(record, 'address')
            )
            self.city.set(
                customer_value(record, 'city')
            )
            self.state.set(
                customer_value(record, 'state')
            )
            self.pincode.set(
                customer_value(record, 'pincode', 'pin')
            )
            self.country.set(
                customer_value(record, 'country') or "India"
            )
            self.gstin.set(
                customer_value(record, 'gstin').upper()
            )
            self.phone.set(
                customer_value(record, 'phone')
            )
            self.email.set(
                customer_value(record, 'email')
            )

            try:
                if touch_last_used:
                    touch_last_used(record.get("id"))
            except Exception:
                pass

            self._update_summary()
            picker.destroy()

        btn_row = tk.Frame(picker, bg=self.CARD,
                           highlightbackground=self.BORDER,
                           highlightthickness=1)
        btn_row.pack(side="bottom", fill="x")

        tk.Button(
            btn_row, text="Cancel", command=picker.destroy,
            bg="white", fg=self.TEXT,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            width=14, height=2,
        ).pack(side="right", padx=(8, 22), pady=14)

        tk.Button(
            btn_row, text="Use Selected",
            command=apply_selection,
            bg=self.RED, fg="white",
            activebackground=self.RED_DARK,
            activeforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 10, "bold"), cursor="hand2",
            width=18, height=2,
        ).pack(side="right", pady=14)

        listbox.bind("<Double-Button-1>", lambda e: apply_selection())




    def _open_preview(self):
        """
        Compute the current quotation data and open the six-page preview.
        Does NOT increment the offer counter — generation does that later.
        """

        # ---- 1. Validate everything (same checks as generate) ----
        if not self._validate_customer():
            self._load_step(1)
            return
        if not self._validate_product():
            self._load_step(2)
            return
        if not self._validate_pricing():
            self._load_step(4)
            return

        # ---- 2. Build data ----
        data = self.get_form_data()

        # ---- auto-save new customers ----
        self._auto_save_customer(data)

        # ---- 3. Resolve product from catalog ----
        try:
            from quotation_generator_crystal import (
                _resolve_product,
                calculate_totals,
            )
        except Exception as exc:
            messagebox.showerror(
                "Preview unavailable",
                f"Could not import quotation_generator_crystal.\n\n"
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        product = _resolve_product(data["model"])

        # ---- 4. Compute totals with the SAME engine the generator uses ----
        # The current generator's calculation engine accepts CGST/SGST
        # percentages. We feed it the effective percentages for the
        # selected GST type, then normalize the returned totals so the
        # preview can display IGST / No GST correctly.
        preview_cgst = data["cgst_percent"]
        preview_sgst = data["sgst_percent"]

        if data["gst_type"] == "IGST":
            preview_cgst = 0.0
            preview_sgst = 0.0

        elif data["gst_type"] == "No GST":
            preview_cgst = 0.0
            preview_sgst = 0.0

        totals = calculate_totals(
            machine_price=data["machine_price"],
            machine_qty=data["machine_qty"],
            accessories=data["accessories"],
            transportation=data["transportation"],
            packing_percent=data["packing_percent"],
            packing_mode=data["packing_mode"],
            packing_value=data["packing_value"],
            cgst_percent=preview_cgst,
            sgst_percent=preview_sgst,
        )

        if data["gst_type"] == "IGST":

            taxable = totals.get("taxable", Decimal("0"))
            igst_amount = (
                taxable
                * Decimal(str(data["gst_rate"]))
                / Decimal("100")
            )

            totals["cgst"] = Decimal("0")
            totals["sgst"] = Decimal("0")
            totals["igst"] = igst_amount
            totals["grand_total"] = taxable + igst_amount

        elif data["gst_type"] == "No GST":

            totals["cgst"] = Decimal("0")
            totals["sgst"] = Decimal("0")
            totals["igst"] = Decimal("0")
            totals["grand_total"] = totals.get(
                "taxable",
                Decimal("0")
            )

        else:

            totals["igst"] = Decimal("0")

        totals["gst_type"] = data["gst_type"]
        totals["gst_rate"] = Decimal(str(data["gst_rate"]))
        totals["gst"] = (
            totals.get("cgst", Decimal("0"))
            + totals.get("sgst", Decimal("0"))
            + totals.get("igst", Decimal("0"))
        )

        # ---- 5. Company ----
        try:
            from app.company import COMPANY
        except Exception:
            COMPANY = {
                "name": "ARMATECH ASSOCIATES",
                "brand": "CRYSTAL VMM",
                "address": "",
                "phone": "",
                "email": "",
                "website": "",
            }

        # ---- 6. Preview offer number (peek, do not increment) ----
        quotation_number, quotation_date = self._peek_offer_number(data)

        # ---- 7. Open the preview ----
        try:
            from ui.crystal.quotation_preview import QuotationPreview
        except Exception as exc:
            messagebox.showerror(
                "Preview unavailable",
                f"Could not import ui.crystal.quotation_preview.\n\n"
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        QuotationPreview(
            parent=self,
            form_data=data,
            totals=totals,
            product=product,
            quotation_number=quotation_number,
            quotation_date=quotation_date,
            company=COMPANY,
            on_finalise=self._generate_quotation,
        )

    def _peek_offer_number(self, data):
        """
        Read the NEXT offer number without incrementing the counter.
        Uses the module-aware quotation_number_service so Crystal gets
        CRY/26-27/NNN and VMM gets AA/VMM/26-27/NNN.
        """

        import json as _json
        from pathlib import Path as _Path

        # ─── Resolve the NEXT number without incrementing ───
        qn = None
        try:
            from app.services.quotation_number_service import (
                get_next_quotation_number,
                _get_quotation_prefix,
            )
            # get_next_quotation_number() increments, so we can't use it here.
            # Instead, read the counter file directly, using the correct
            # module-aware prefix and file location.
            from app.services.paths import get_data_dir
            counter_file = get_data_dir() / "quotation_counter.json"

            prefix = _get_quotation_prefix()
            fy = "26-27"

            serial = 1
            if counter_file.is_file():
                counter = _json.loads(counter_file.read_text(encoding="utf-8")) or {}
                last = int(counter.get("last_number", 0))
                serial = last + 1

            qn = f"{prefix}/{fy}/{serial:04d}"
        except Exception:
            # Fallback — try the old path just in case
            try:
                counter_file = _Path(PROJECT_ROOT) / "data" / "offer_counter.json"
                serial = 1
                if counter_file.is_file():
                    counter = _json.loads(counter_file.read_text(encoding="utf-8")) or {}
                    serial = int(counter.get("AA/VMM/26-27", 0)) + 1
                qn = f"CRY/26-27/{serial:04d}"
            except Exception:
                qn = "CRY/26-27/0001"

        # ─── Date — take from data or today ───
        qd = data.get("quotation_date") or ""
        try:
            from datetime import date as _d, datetime as _dt
            # If ISO, reformat to DD-MM-YYYY
            if qd and "-" in qd and len(qd) == 10 and qd[4] == "-":
                y, m, d = qd.split("-")
                qd = f"{d}-{m}-{y}"
        except Exception:
            pass

        if not qd:
            try:
                from datetime import datetime as _dt2
                qd = _dt2.now().strftime("%d-%m-%Y")
            except Exception:
                qd = ""

        return qn, qd

    # ========================================================
    # PHASE 3 — Refresh dashboard + close form cleanly
    # ========================================================

    def _refresh_parent_dashboard(self):
        """Notify the dashboard (if present) to reload its recent list."""
        try:
            parent = getattr(self, "master", None)
            if parent is None:
                parent = getattr(self, "app", None)
            if parent is None:
                return
            if hasattr(parent, "_reload_recent"):
                parent._reload_recent()
            try:
                parent.focus_force()
                parent.lift()
            except Exception:
                pass
        except Exception:
            pass

    def _close_and_return_to_dashboard(self):
        """Refresh dashboard, then destroy this form."""
        try:
            self._refresh_parent_dashboard()
        finally:
            try:
                self.destroy()
            except Exception:
                pass


# ========================================================
    # CLEAR FORM
    # ========================================================

    def clear_form(self):

        confirm = messagebox.askyesno(
            "Clear quotation",
            (
                "Clear the current quotation "
                "and start again?"
            ),
            parent=self
        )

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

            self.category.set(
                categories[0]
            )

        models = self._get_models(
            self.category.get()
        )

        if models:

            self.model.set(
                models[0]
            )

        else:

            self.model.set("")

        self.machine_price.set("")

        self.machine_qty.set(
            "1"
        )

        self.transportation.set(
            "0"
        )

        self.packing_mode.set(
            "Percentage (%)"
        )

        self.packing_value.set(
            "3.5"
        )

        self.packing_percent.set(
            "3.5"
        )

        self.gst_type.set(
            "CGST + SGST"
        )

        self.gst_rate.set(
            "18"
        )

        self.cgst_percent.set(
            "9"
        )

        self.sgst_percent.set(
            "9"
        )

        self.include_terms.set(
            False
        )

        self.completed_steps.clear()
        self.term_rows = []

        self._load_step(1)

        try:
            self.canvas.yview_moveto(0)
        except Exception:
            pass


    # ========================================================
    # CLEAR CONTENT
    # ========================================================

    def _clear_content(self):

        for widget in self.content_area.winfo_children():

            widget.destroy()


# ============================================================
# TERMS EDITOR DIALOG
# ============================================================

class TermsEditor(tk.Toplevel):
    """
    Modal dialog for editing the quotation terms list.
    """

    # Reuse palette
    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_DARK = "#980000"
    GREEN = "#16804B"
    GREEN_LIGHT = "#ECF8F1"
    SOFT = "#F8F9FA"

    def __init__(self, parent, terms):

        super().__init__(parent)

        self.title("Edit Terms & Conditions")

        self.geometry("820x680")
        self.minsize(700, 520)

        self.configure(bg=self.BG)

        self.transient(parent)
        self.grab_set()

        # Working copy
        self.working_terms = [
            {"title": t, "value": v}
            for t, v in terms
        ]

        self.result = None

        self.selected_index = None
        self.row_widgets = []

        self._build_interface()

        self._refresh_list()

        self.protocol(
            "WM_DELETE_WINDOW",
            self._cancel
        )


    # ========================================================
    # INTERFACE
    # ========================================================

    def _build_interface(self):

        # Header
        header = tk.Frame(
            self,
            bg=self.CARD,
            height=70
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Terms & Conditions",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=24, pady=(16, 0))

        tk.Label(
            header,
            text=(
                "Edit, reorder, add or remove the terms "
                "that appear on your quotations."
            ),
            bg=self.CARD,
            fg=self.MUTED,
            font=("Arial", 9)
        ).pack(anchor="w", padx=24)

        tk.Frame(
            header,
            bg=self.RED,
            height=3
        ).pack(side="bottom", fill="x")

        # List
        list_wrap = tk.Frame(self, bg=self.BG)

        list_wrap.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(14, 0)
        )

        self.canvas = tk.Canvas(
            list_wrap,
            bg=self.BG,
            highlightthickness=0,
            bd=0
        )

        scrollbar = ttk.Scrollbar(
            list_wrap,
            orient="vertical",
            command=self.canvas.yview
        )

        self.list_frame = tk.Frame(
            self.canvas,
            bg=self.BG
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.list_frame,
            anchor="nw"
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Scrollbar intentionally hidden; mouse-wheel scrolling remains enabled.
        self.canvas.bind_all(
            "<MouseWheel>",
            self._mousewheel,
            add="+"
        )
        self.canvas.bind_all(
            "<Shift-MouseWheel>",
            self._mousewheel,
            add="+"
        )
        self.canvas.bind_all(
            "<Button-4>",
            self._mousewheel_up,
            add="+"
        )
        self.canvas.bind_all(
            "<Button-5>",
            self._mousewheel_down,
            add="+"
        )
        self.canvas.bind_all(
            "<Prior>",
            lambda e: self.canvas.yview_scroll(-8, "units"),
            add="+"
        )
        self.canvas.bind_all(
            "<Next>",
            lambda e: self.canvas.yview_scroll(8, "units"),
            add="+"
        )

        self.list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(
                self.canvas_window,
                width=e.width
            )
        )

        # Editor
        editor = tk.Frame(
            self,
            bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        editor.pack(
            fill="x",
            padx=18,
            pady=(14, 8)
        )

        tk.Label(
            editor,
            text="EDIT SELECTED TERM",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Arial", 8, "bold")
        ).pack(anchor="w", padx=16, pady=(14, 4))

        title_row = tk.Frame(editor, bg=self.CARD)
        title_row.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(
            title_row,
            text="Title",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Arial", 9, "bold"),
            width=10,
            anchor="w"
        ).pack(side="left")

        self.edit_title = tk.Entry(
            title_row,
            bg="white",
            fg=self.TEXT,
            relief="solid",
            bd=1,
            font=("Arial", 10),
            insertbackground=self.RED
        )

        self.edit_title.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=6
        )

        details_row = tk.Frame(editor, bg=self.CARD)
        details_row.pack(fill="x", padx=16, pady=(0, 14))

        tk.Label(
            details_row,
            text="Details",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Arial", 9, "bold"),
            width=10,
            anchor="w"
        ).pack(side="left", anchor="n", pady=6)

        self.edit_details = tk.Text(
            details_row,
            height=3,
            bg="white",
            fg=self.TEXT,
            relief="solid",
            bd=1,
            font=("Arial", 10),
            insertbackground=self.RED,
            wrap="word"
        )

        self.edit_details.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=4
        )

        # Action buttons
        action_bar = tk.Frame(self, bg=self.BG)
        action_bar.pack(fill="x", padx=18, pady=(4, 8))

        self._make_action_button(
            action_bar,
            "＋  Add New",
            self._add_new,
            primary=True
        ).pack(side="left")

        self._make_action_button(
            action_bar,
            "🗑  Remove",
            self._remove_selected
        ).pack(side="left", padx=(8, 0))

        self._make_action_button(
            action_bar,
            "▲  Up",
            self._move_up
        ).pack(side="left", padx=(8, 0))

        self._make_action_button(
            action_bar,
            "▼  Down",
            self._move_down
        ).pack(side="left", padx=(8, 0))

        self._make_action_button(
            action_bar,
            "✓  Apply Changes",
            self._apply_edits,
            primary=True
        ).pack(side="right")

        # Footer
        footer = tk.Frame(
            self,
            bg="white",
            height=66,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        self._make_footer_button(
            footer,
            "Restore Defaults",
            self._restore_defaults
        ).pack(side="left", padx=(22, 0), pady=14)

        self._make_footer_button(
            footer,
            "Cancel",
            self._cancel
        ).pack(side="right", padx=(8, 22), pady=14)

        self._make_footer_button(
            footer,
            "Save Terms",
            self._save,
            primary=True
        ).pack(side="right", pady=14)


    # ========================================================
    # BUTTON HELPERS
    # ========================================================

    def _make_action_button(
        self,
        parent,
        text,
        command,
        primary=False
    ):

        if primary:
            bg = self.RED
            fg = "white"
            active_bg = self.RED_DARK
            active_fg = "white"
            relief = "flat"
            bd = 0
        else:
            bg = "white"
            fg = self.TEXT
            active_bg = "#F3F4F6"
            active_fg = self.TEXT
            relief = "solid"
            bd = 1

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=active_fg,
            relief=relief,
            bd=bd,
            highlightthickness=0,
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=14,
            pady=7
        )


    def _make_footer_button(
        self,
        parent,
        text,
        command,
        primary=False
    ):

        if primary:
            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=self.RED,
                fg="white",
                activebackground=self.RED_DARK,
                activeforeground="white",
                relief="flat",
                bd=0,
                highlightthickness=0,
                font=("Arial", 10, "bold"),
                cursor="hand2",
                width=16,
                height=2
            )

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg="white",
            fg=self.TEXT,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Arial", 9),
            cursor="hand2",
            width=16,
            height=2
        )


    # ========================================================
    # LIST RENDERING
    # ========================================================

    def _mousewheel(self, event):
        """Scroll Terms & Conditions with mouse wheel or precision touchpad."""
        try:
            if not self.winfo_exists() or not self.canvas.winfo_exists():
                return

            if event.widget.winfo_toplevel() is not self:
                return

            delta = getattr(event, "delta", 0)
            if delta:
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


    def _refresh_list(self, keep_selection=True):

        previous = self.selected_index

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        self.row_widgets = []

        if not self.working_terms:

            empty = tk.Frame(
                self.list_frame,
                bg=self.SOFT,
                highlightbackground=self.BORDER,
                highlightthickness=1
            )

            empty.pack(fill="x", pady=6)

            tk.Label(
                empty,
                text=(
                    "No terms yet. "
                    "Click “Add New” to create one."
                ),
                bg=self.SOFT,
                fg=self.MUTED,
                font=("Arial", 9, "italic")
            ).pack(anchor="w", padx=14, pady=16)

            self.selected_index = None
            self._load_editor()

            return

        for index, term in enumerate(self.working_terms):

            row = tk.Frame(
                self.list_frame,
                bg=self.CARD,
                highlightbackground=self.BORDER,
                highlightthickness=1,
                cursor="hand2"
            )

            row.pack(fill="x", pady=4)

            is_selected = (index == self.selected_index)

            if is_selected:
                row.configure(
                    highlightbackground=self.RED,
                    highlightthickness=2
                )

            tk.Label(
                row,
                text=str(index + 1),
                bg=(self.RED if is_selected else "#E9EBEE"),
                fg=("white" if is_selected else self.MUTED),
                width=3,
                font=("Arial", 9, "bold")
            ).pack(side="left", padx=(10, 10), pady=12)

            text_box = tk.Frame(row, bg=self.CARD)
            text_box.pack(
                side="left",
                fill="x",
                expand=True,
                pady=10
            )

            tk.Label(
                text_box,
                text=term["title"] or "(untitled)",
                bg=self.CARD,
                fg=self.TEXT,
                font=("Arial", 10, "bold"),
                anchor="w"
            ).pack(anchor="w")

            tk.Label(
                text_box,
                text=term["value"] or "(no details)",
                bg=self.CARD,
                fg=self.MUTED,
                font=("Arial", 9),
                anchor="w",
                justify="left",
                wraplength=560
            ).pack(anchor="w", pady=(2, 0))

            for widget in (row, text_box):
                widget.bind(
                    "<Button-1>",
                    lambda e, i=index: self._select(i)
                )

            for child in text_box.winfo_children():
                child.bind(
                    "<Button-1>",
                    lambda e, i=index: self._select(i)
                )

            self.row_widgets.append(row)

        if keep_selection and previous is not None:

            if 0 <= previous < len(self.working_terms):
                self.selected_index = previous
            else:
                self.selected_index = None

        self._load_editor()


    def _select(self, index):

        self.selected_index = index

        self._refresh_list()


    # ========================================================
    # EDITOR LOAD
    # ========================================================

    def _load_editor(self):

        self.edit_title.delete(0, "end")
        self.edit_details.delete("1.0", "end")

        if (
            self.selected_index is None
            or not (0 <= self.selected_index < len(self.working_terms))
        ):

            self.edit_title.configure(state="disabled")
            self.edit_details.configure(state="disabled")

            return

        self.edit_title.configure(state="normal")
        self.edit_details.configure(state="normal")

        term = self.working_terms[self.selected_index]

        self.edit_title.insert(0, term["title"])
        self.edit_details.insert("1.0", term["value"])


    # ========================================================
    # EDITOR OPERATIONS
    # ========================================================

    def _apply_edits(self):

        if self.selected_index is None:

            messagebox.showinfo(
                "No term selected",
                "Please select a term from the list first.",
                parent=self
            )

            return

        title = self.edit_title.get().strip()
        details = self.edit_details.get("1.0", "end").strip()

        if not title or not details:

            messagebox.showerror(
                "Incomplete term",
                "Both the title and the details are required.",
                parent=self
            )

            return

        self.working_terms[self.selected_index] = {
            "title": title,
            "value": details,
        }

        self._refresh_list()


    def _add_new(self):

        if (
            self.selected_index is not None
            and self.edit_title.cget("state") == "normal"
        ):

            title = self.edit_title.get().strip()
            details = self.edit_details.get("1.0", "end").strip()

            if title and details:
                self.working_terms[self.selected_index] = {
                    "title": title,
                    "value": details,
                }

        self.working_terms.append(
            {
                "title": "NEW TERM",
                "value": "Enter details here",
            }
        )

        self.selected_index = len(self.working_terms) - 1

        self._refresh_list()


    def _remove_selected(self):

        if self.selected_index is None:

            messagebox.showinfo(
                "No term selected",
                "Select a term to remove.",
                parent=self
            )

            return

        term = self.working_terms[self.selected_index]

        confirm = messagebox.askyesno(
            "Remove term",
            f"Remove this term?\n\n{term['title']}",
            parent=self
        )

        if not confirm:
            return

        del self.working_terms[self.selected_index]

        if not self.working_terms:
            self.selected_index = None
        elif self.selected_index >= len(self.working_terms):
            self.selected_index = len(self.working_terms) - 1

        self._refresh_list()


    def _move_up(self):

        index = self.selected_index

        if index is None or index <= 0:
            return

        self.working_terms[index - 1], self.working_terms[index] = (
            self.working_terms[index],
            self.working_terms[index - 1],
        )

        self.selected_index = index - 1

        self._refresh_list()


    def _move_down(self):

        index = self.selected_index

        if index is None or index >= len(self.working_terms) - 1:
            return

        self.working_terms[index + 1], self.working_terms[index] = (
            self.working_terms[index],
            self.working_terms[index + 1],
        )

        self.selected_index = index + 1

        self._refresh_list()


    # ========================================================
    # FOOTER ACTIONS
    # ========================================================

    def _restore_defaults(self):

        confirm = messagebox.askyesno(
            "Restore defaults",
            "Discard your current edits and restore the standard terms?",
            parent=self
        )

        if not confirm:
            return

        self.working_terms = [
            {"title": t, "value": v}
            for t, v in STANDARD_TERMS
        ]

        self.selected_index = None

        self._refresh_list()


    def _save(self):

        if (
            self.selected_index is not None
            and self.edit_title.cget("state") == "normal"
        ):

            title = self.edit_title.get().strip()
            details = self.edit_details.get("1.0", "end").strip()

            if title and details:
                self.working_terms[self.selected_index] = {
                    "title": title,
                    "value": details,
                }

        cleaned = []

        for term in self.working_terms:

            title = term["title"].strip()
            value = term["value"].strip()

            if not title or not value:
                continue

            cleaned.append((title, value))

        if not cleaned:

            messagebox.showerror(
                "No valid terms",
                (
                    "Please provide at least one term "
                    "with a title and details."
                ),
                parent=self
            )

            return

        self.result = cleaned

        self.destroy()


    def _cancel(self):

        self.result = None

        self.destroy()


# ============================================================
# STANDALONE TEST
# ============================================================


