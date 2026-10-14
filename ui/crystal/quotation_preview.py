"""
CRYSTAL — Single-Page Quotation Preview.

Replaces the 6-tab VMM-style layout with one scrollable page:
    Header · Customer · Item · Totals · Amount in Words · Terms · Signature
"""
import os
import sys
import tkinter as tk
from tkinter import messagebox

# Project root on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Shared helpers from the Crystal generator
try:
    from quotation_generator_crystal import (
        _money, _text, _decimal,
    )
    from app.services.amount_in_words import amount_in_words as _amount_in_words
except Exception:
    def _money(v):
        try:
            return f"₹ {float(v):,.2f}"
        except Exception:
            return "₹ 0.00"

    def _text(v):
        return "" if v is None else str(v)

    def _decimal(v, default=0):
        try:
            return float(v or default)
        except Exception:
            return default

    def _amount_in_words(v):
        return f"{_money(v)} only"


class QuotationPreview(tk.Toplevel):

    # ─── Palette ───
    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    SOFT = "#F8F9FA"
    TEXT = "#17191D"
    MUTED = "#747A84"
    LIGHT_MUTED = "#9BA1AA"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_DARK = "#980000"
    RED_LIGHT = "#FFF3F3"
    GREEN = "#16804B"

    def __init__(self, parent, form_data, totals, product,
                 quotation_number, quotation_date, company,
                 on_finalise=None):
        super().__init__(parent)

        self.title("CRYSTAL | Quotation Preview")
        try:
            from ui.common.ui_helpers import set_window_icon
            set_window_icon(self)
        except Exception:
            pass

        # Adaptive size
        self.update_idletasks()
        try:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        except Exception:
            sw, sh = 1366, 768
        usable_h = max(600, sh - 90)
        usable_w = min(1080, max(900, sw - 100))
        x = max(0, (sw - usable_w) // 2)
        y = max(0, (sh - usable_h) // 2 - 20)
        self.geometry(f"{usable_w}x{usable_h}+{x}+{y}")
        self.minsize(920, 600)

        self.configure(bg=self.BG)
        self.transient(parent)
        self.grab_set()

        # Data
        self.form_data = form_data or {}
        self.totals = totals or {}
        self.product = product or {}
        self.quotation_number = quotation_number or "—"
        self.quotation_date = quotation_date or "—"
        self.company = company or {}
        self.on_finalise = on_finalise
        self.confirmed = False

        self._build_interface()
        self.protocol("WM_DELETE_WINDOW", self._close)

        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(self, on_escape=self._close)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════
    # LAYOUT
    # ═══════════════════════════════════════════════════════════

    def _build_interface(self):
        self._build_header()
        self._build_content_area()
        self._build_navigation()
        self._render_single_page()

    def _build_header(self):
        header = tk.Frame(self, bg=self.CARD, height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.CARD)
        brand.pack(side="left", padx=26)
        tk.Label(brand, text="CRYSTAL", bg=self.CARD, fg=self.RED,
                 font=("Arial", 20, "bold")).pack(side="left", pady=20)
        tk.Label(brand, text="  /  Quotation Preview", bg=self.CARD,
                 fg=self.MUTED, font=("Arial", 10)).pack(side="left", pady=24)

        right = tk.Frame(header, bg=self.CARD)
        right.pack(side="right", padx=26)
        tk.Label(right, text=f"Offer No.  {self.quotation_number}",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 11, "bold")).pack(anchor="e", pady=(18, 0))
        tk.Label(right, text=f"Date  {self.quotation_date}",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 9)).pack(anchor="e")

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

    def _build_content_area(self):
        wrap = tk.Frame(self, bg=self.BG)
        wrap.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(wrap, bg=self.BG, highlightthickness=0)
        scroll = tk.Scrollbar(wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(self._canvas, bg=self.BG)
        self._win = self._canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )

        self.content.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfigure(self._win, width=e.width),
        )

        # Mouse wheel
        self._canvas.bind_all("<MouseWheel>", self._mousewheel)

    def _mousewheel(self, event):
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _build_navigation(self):
        nav = tk.Frame(self, bg="white", height=70,
                       highlightbackground=self.BORDER, highlightthickness=1)
        nav.pack(side="bottom", fill="x")
        nav.pack_propagate(False)

        # Left: close
        left = tk.Frame(nav, bg="white")
        left.pack(side="left", padx=22)
        tk.Button(
            left, text="←  Close", command=self._close,
            bg="white", fg=self.TEXT,
            activebackground="#F3F4F6", activeforeground=self.TEXT,
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            width=14, height=2,
        ).pack(pady=14)

        # Right: Save as Word / Save PDF / Finalise
        right = tk.Frame(nav, bg="white")
        right.pack(side="right", padx=22)

        tk.Button(
            right, text="Finalise & Save  →", command=self._finalise,
            bg=self.RED, fg="white",
            activebackground=self.RED_DARK, activeforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 10, "bold"), cursor="hand2",
            width=24, height=2,
        ).pack(side="right", pady=14)

    # ═══════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════

    def _card(self, padding=22):
        outer = tk.Frame(self.content, bg=self.BORDER)
        outer.pack(fill="x", padx=24, pady=(0, 14))
        inner = tk.Frame(outer, bg=self.CARD)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        body = tk.Frame(inner, bg=self.CARD)
        body.pack(fill="both", expand=True, padx=padding, pady=padding)
        return body

    def _section_title(self, parent, title, subtitle=""):
        tk.Label(parent, text=title, bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 12, "bold"), anchor="w").pack(anchor="w")
        if subtitle:
            tk.Label(parent, text=subtitle, bg=self.CARD, fg=self.MUTED,
                     font=("Arial", 9), anchor="w").pack(anchor="w", pady=(2, 0))

    def _divider(self, parent):
        tk.Frame(parent, bg=self.BORDER, height=1).pack(fill="x", pady=(10, 10))

    # ═══════════════════════════════════════════════════════════
    # SINGLE-PAGE RENDER
    # ═══════════════════════════════════════════════════════════

    def _render_single_page(self):
        # Top spacing
        tk.Frame(self.content, bg=self.BG, height=18).pack()

        self._render_header_card()
        self._render_item_card()
        self._render_totals_card()
        self._render_terms_card()
        self._render_signature_card()

        # Bottom spacing
        tk.Frame(self.content, bg=self.BG, height=18).pack()

    def _render_header_card(self):
        card = self._card()

        # Left: CRYSTAL brand
        left = tk.Frame(card, bg=self.CARD)
        left.pack(side="left", anchor="n")

        tk.Label(left, text="CRYSTAL", bg=self.CARD, fg=self.RED,
                 font=("Arial", 22, "bold"), anchor="w").pack(anchor="w")
        tk.Label(left, text="A Name With Magnetic Fame",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 9, "italic"), anchor="w").pack(anchor="w")

        # Right: Seller info
        right = tk.Frame(card, bg=self.CARD)
        right.pack(side="right", anchor="n")

        tk.Label(right, text="ARMATECH ASSOCIATES",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 13, "bold"), anchor="e").pack(anchor="e")

        seller_addr = self.company.get(
            "address",
            "W-174A, 'S' Block, M.I.D.C., Bhosari Industrial Estate, PUNE - 411 026. (INDIA)",
        )
        seller_gstin = self.company.get("gstin", "27AAKCA9634B1ZT")
        seller_phone = self.company.get("phone", "+91 7020991684 / +91 9699820070")
        seller_email = self.company.get("email", "armatech@gmail.com")

        for line in [
            seller_addr,
            f"GSTIN: {seller_gstin}",
            f"Phone: {seller_phone}",
            f"Email: {seller_email}",
        ]:
            tk.Label(right, text=line, bg=self.CARD, fg=self.MUTED,
                     font=("Arial", 8), anchor="e",
                     justify="right").pack(anchor="e", pady=(2, 0))

        # Full-width divider
        self._divider(card)

        # Offer / Date
        meta = tk.Frame(card, bg=self.CARD)
        meta.pack(fill="x")
        tk.Label(meta, text=f"Quotation No: {self.quotation_number}",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 10, "bold")).pack(side="left")
        tk.Label(meta, text=f"Date: {self.quotation_date}",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 10, "bold")).pack(side="right")

        self._divider(card)

        # Bill To
        tk.Label(card, text="BILL TO", bg=self.CARD, fg=self.RED,
                 font=("Arial", 9, "bold"), anchor="w").pack(anchor="w")

        f = self.form_data
        buyer_lines = []
        if f.get("company"):
            buyer_lines.append(f["company"])
        if f.get("customer_name"):
            buyer_lines.append(f"Attn: {f['customer_name']}")
        if f.get("contact_person"):
            buyer_lines.append(f"Contact: {f['contact_person']}")
        if f.get("address"):
            buyer_lines.append(f["address"])
        loc = " ".join(filter(None, [f.get("city"), f.get("state"), f.get("pincode")]))
        if loc:
            buyer_lines.append(loc)
        if f.get("gstin"):
            buyer_lines.append(f"GSTIN: {f['gstin']}")
        if f.get("phone"):
            buyer_lines.append(f"Phone: {f['phone']}")
        if f.get("email"):
            buyer_lines.append(f"Email: {f['email']}")

        if not buyer_lines:
            buyer_lines = ["—"]

        for line in buyer_lines:
            tk.Label(card, text=line, bg=self.CARD, fg=self.TEXT,
                     font=("Arial", 9), anchor="w",
                     justify="left").pack(anchor="w", pady=(1, 0))

    def _render_item_card(self):
        card = self._card()
        self._section_title(card, "ITEM", "Product / machine configuration")

        # Table header
        table = tk.Frame(card, bg=self.BORDER)
        table.pack(fill="x", pady=(10, 0))

        header = tk.Frame(table, bg=self.RED)
        header.pack(fill="x")

        cols = [
            ("Sr.", 4),
            ("Description", 46),
            ("Qty.", 6),
            ("Unit Price", 14),
            ("Amount", 14),
        ]
        for text, w in cols:
            tk.Label(header, text=text, bg=self.RED, fg="white",
                     font=("Arial", 9, "bold"), anchor="w",
                     width=w, padx=6, pady=8).pack(side="left")

        # Row
        machine_price = _decimal(self.form_data.get("machine_price", 0))
        machine_qty = _decimal(self.form_data.get("machine_qty", 1))
        machine_total = machine_price * machine_qty

        name = (self.product.get("name")
                or self.product.get("product_name")
                or "CRYSTAL Product")
        model = self.product.get("model") or self.form_data.get("model") or ""
        desc = self.product.get("description") or ""

        full_desc = name
        if desc and desc != name:
            full_desc = f"{name}\n{desc}"
        if model:
            full_desc = f"{full_desc}\nModel: {model}"

        row = tk.Frame(table, bg=self.CARD)
        row.pack(fill="x")

        for text, w in [
            ("1", 4),
            (full_desc, 46),
            (f"{machine_qty:g}", 6),
            (_money(machine_price), 14),
            (_money(machine_total), 14),
        ]:
            tk.Label(row, text=_text(text), bg=self.CARD, fg=self.TEXT,
                     font=("Arial", 9), anchor="w", justify="left",
                     wraplength=420, width=w,
                     padx=6, pady=8).pack(side="left", anchor="n")

    def _render_totals_card(self):
        card = self._card()
        self._section_title(card, "TOTALS", "Amount breakdown")

        t = self.totals

        rows = [
            ("Machine", _money(t.get("machine_total", t.get("machine", 0))), False),
        ]

        # Optional rows
        if _decimal(t.get("packing", 0)) > 0:
            pct = _decimal(self.form_data.get("packing_value", 3.5))
            rows.append((f"Packing ({pct:.2f}%)", _money(t.get("packing", 0)), False))

        rows.append(("Taxable Value", _money(t.get("taxable", 0)), False))

        cgst_pct = _decimal(self.form_data.get("cgst_percent", 9))
        sgst_pct = _decimal(self.form_data.get("sgst_percent", 9))

        gst_type = str(self.form_data.get("gst_type", "CGST + SGST") or "")

        if gst_type == "IGST":
            igst_pct = _decimal(self.form_data.get("gst_rate", 18))
            rows.append((f"IGST ({igst_pct:.2f}%)", _money(t.get("igst", 0)), False))
        else:
            rows.append((f"CGST ({cgst_pct:.2f}%)", _money(t.get("cgst", 0)), False))
            rows.append((f"SGST ({sgst_pct:.2f}%)", _money(t.get("sgst", 0)), False))

        grand = t.get("grand_total", t.get("grand", 0))
        rows.append(("GRAND TOTAL", _money(grand), True))

        for label, value, is_grand in rows:
            bg = self.RED if is_grand else self.SOFT
            fg = "white" if is_grand else self.TEXT
            r = tk.Frame(card, bg=bg)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label, bg=bg, fg=fg,
                     font=("Arial", 10 if is_grand else 9,
                           "bold" if is_grand else "normal"),
                     anchor="e", width=30, padx=10, pady=8).pack(side="right")
            tk.Label(r, text=value, bg=bg, fg=fg,
                     font=("Arial", 11 if is_grand else 9, "bold"),
                     anchor="e", width=18, padx=10, pady=8).pack(side="right")

        # Amount in words
        tk.Frame(card, bg=self.CARD, height=8).pack()
        tk.Label(card, text=f"Amount in Words: {_amount_in_words(grand)}",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 9, "bold"),
                 anchor="w", justify="left",
                 wraplength=850).pack(anchor="w", pady=(6, 0))

    def _render_terms_card(self):
        if not self.form_data.get("include_terms", False):
            return

        selected = self.form_data.get("selected_terms") or []
        if not selected:
            return

        card = self._card()
        self._section_title(card, "TERMS & CONDITIONS",
                            "Commercial terms applicable to this quotation")

        table = tk.Frame(card, bg=self.BORDER)
        table.pack(fill="x", pady=(10, 0))

        header = tk.Frame(table, bg=self.RED)
        header.pack(fill="x")
        tk.Label(header, text="Sr.", bg=self.RED, fg="white",
                 font=("Arial", 9, "bold"), width=4,
                 padx=6, pady=8, anchor="w").pack(side="left")
        tk.Label(header, text="Term", bg=self.RED, fg="white",
                 font=("Arial", 9, "bold"), width=22,
                 padx=6, pady=8, anchor="w").pack(side="left")
        tk.Label(header, text="Details", bg=self.RED, fg="white",
                 font=("Arial", 9, "bold"),
                 padx=6, pady=8, anchor="w").pack(side="left", fill="x", expand=True)

        for i, term in enumerate(selected, 1):
            bg = self.SOFT if i % 2 == 0 else self.CARD
            r = tk.Frame(table, bg=bg)
            r.pack(fill="x")
            tk.Label(r, text=str(i), bg=bg, fg=self.TEXT,
                     font=("Arial", 9), width=4, padx=6, pady=7,
                     anchor="w").pack(side="left")
            tk.Label(r, text=term.get("title", "—"), bg=bg, fg=self.TEXT,
                     font=("Arial", 9, "bold"), width=22,
                     padx=6, pady=7, anchor="w",
                     justify="left", wraplength=200).pack(side="left", anchor="n")
            tk.Label(r, text=term.get("value", "—"), bg=bg, fg=self.TEXT,
                     font=("Arial", 9), padx=6, pady=7, anchor="w",
                     justify="left", wraplength=520).pack(side="left", fill="x", expand=True)

    def _render_signature_card(self):
        card = self._card()
        tk.Label(card,
                 text="We trust you will find our proposal in line with your "
                      "requirements. Please do not hesitate to contact us if "
                      "you need any further clarification.",
                 bg=self.CARD, fg=self.TEXT, font=("Arial", 9),
                 anchor="w", justify="left", wraplength=850).pack(anchor="w")

        tk.Label(card, text="Thanking you and assuring our best services always,",
                 bg=self.CARD, fg=self.TEXT, font=("Arial", 9),
                 anchor="w").pack(anchor="w", pady=(8, 0))

        tk.Label(card, text="With best regards,",
                 bg=self.CARD, fg=self.TEXT, font=("Arial", 9),
                 anchor="w").pack(anchor="w", pady=(6, 0))

        tk.Frame(card, bg=self.CARD, height=16).pack()

        # Signature block (right-aligned)
        sig = tk.Frame(card, bg=self.CARD)
        sig.pack(fill="x")
        tk.Label(sig, text="For ARMATECH ASSOCIATES",
                 bg=self.CARD, fg=self.TEXT, font=("Arial", 9),
                 anchor="e").pack(anchor="e")
        tk.Frame(sig, bg=self.CARD, height=24).pack()
        tk.Label(sig, text="Amol Lunawat",
                 bg=self.CARD, fg=self.TEXT, font=("Arial", 11, "bold"),
                 anchor="e").pack(anchor="e")
        tk.Label(sig, text="Authorized Representative",
                 bg=self.CARD, fg=self.MUTED, font=("Arial", 8),
                 anchor="e").pack(anchor="e")

    # ═══════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _finalise(self):
        self.confirmed = True
        if self.on_finalise:
            try:
                self.on_finalise()
            except Exception as e:
                messagebox.showerror("Generation failed", str(e))
                return
        self._close()

    def _close(self):
        try:
            self._canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
