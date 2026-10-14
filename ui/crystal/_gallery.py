"""CRYSTAL Widget Gallery V2."""
import tkinter as tk
from ui.crystal import theme as T
from ui.crystal import widgets as W


class Gallery(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CRYSTAL — Widget Gallery V2")
        self.geometry("1200x820")
        self.configure(bg=T.BG)

        W.TopBar(self, logo_text="CRYSTAL", nav_label="Widget Gallery",
                 user_label="Admin", on_logout=self.destroy).pack(fill="x")

        canvas = tk.Canvas(self, bg=T.BG, highlightthickness=0)
        scroll = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(canvas, bg=T.BG)
        canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        pad = T.SP_XL

        # Stat cards
        self._sec(body, "Overview", "Live business metrics").pack(fill="x", padx=pad, pady=(pad, 0))
        row = tk.Frame(body, bg=T.BG)
        row.pack(fill="x", padx=pad, pady=(12, 0))
        cards = [
            ("₹0.00",   "This Month",  None, "neutral", "+0% vs last", None),
            ("0",       "Quotes",      None, "neutral", "Draft: 0",    None),
            ("3,323",   "Products",    None, "up",      "+12 today",   T.ACCENT),
            ("12",      "Accessories", None, "neutral", "All active",  T.SUCCESS),
        ]
        for i, (v, l, _s, dk, dt, ac) in enumerate(cards):
            c = W.StatCard(row, value=v, label=l, delta=dt, delta_kind=dk, accent_color=ac)
            c.pack(side="left", fill="both", expand=True,
                   padx=(0 if i == 0 else 12, 0))

        # Buttons
        self._sec(body, "Buttons", "Actions in three styles").pack(fill="x", padx=pad, pady=(pad, 0))
        row = tk.Frame(body, bg=T.BG)
        row.pack(fill="x", padx=pad, pady=(12, 0))
        W.PrimaryButton(row, "New Quotation", lambda: None, icon="＋").pack(side="left")
        W.GhostButton(row,   "Cancel",        lambda: None).pack(side="left", padx=10)
        W.DangerButton(row,  "Delete",        lambda: None, icon="✕").pack(side="left")

        # Quick Actions
        self._sec(body, "Quick Actions", "Primary workflow shortcuts").pack(fill="x", padx=pad, pady=(pad, 0))
        col = tk.Frame(body, bg=T.BG)
        col.pack(fill="x", padx=pad, pady=(12, 0))
        for icon, label, sub, primary in [
            ("＋", "New Quotation",      "Create a fresh quote",      True),
            ("📦", "Manage Products",    "3,323 products in catalog", False),
            ("🔧", "Manage Accessories", "12 active accessories",     False),
            ("👥", "Customers",          "47 saved customers",        False),
        ]:
            r = W.ActionRow(col, icon=icon, label=label, sublabel=sub,
                            command=lambda l=label: W.Toast.show(self, f"Opened: {l}", kind="success"),
                            primary=primary)
            r.pack(fill="x", pady=6)

        # Form
        self._sec(body, "Form Fields", "Labeled inputs with focus ring").pack(fill="x", padx=pad, pady=(pad, 0))
        form = W.Card(body, title="Customer Details",
                      subtitle="Enter the buyer information")
        form.pack(fill="x", padx=pad, pady=(12, 0))
        two_col = tk.Frame(form.body, bg=T.SURFACE)
        two_col.pack(fill="x")
        left  = tk.Frame(two_col, bg=T.SURFACE); left.pack(side="left",  fill="x", expand=True)
        right = tk.Frame(two_col, bg=T.SURFACE); right.pack(side="left", fill="x", expand=True, padx=(20, 0))
        W.Field(left,  label="Customer Name", required=True).pack(fill="x", pady=6)
        W.Field(left,  label="Phone").pack(fill="x", pady=6)
        W.Field(right, label="Company", required=True).pack(fill="x", pady=6)
        W.Field(right, label="Email").pack(fill="x", pady=6)
        W.Combo(form.body, label="City",
                values=["Pune", "Mumbai", "Delhi", "Bangalore"]).pack(fill="x", pady=(12, 0))

        # Toasts
        self._sec(body, "Notifications", "Click to preview").pack(fill="x", padx=pad, pady=(pad, 0))
        row = tk.Frame(body, bg=T.BG)
        row.pack(fill="x", padx=pad, pady=(12, pad))
        W.GhostButton(row, "Info",    lambda: W.Toast.show(self, "Information message", kind="info")).pack(side="left")
        W.GhostButton(row, "Success", lambda: W.Toast.show(self, "Saved successfully",  kind="success")).pack(side="left", padx=10)
        W.GhostButton(row, "Warning", lambda: W.Toast.show(self, "Check your input",    kind="warning")).pack(side="left")
        W.GhostButton(row, "Error",   lambda: W.Toast.show(self, "Something failed",    kind="error")).pack(side="left", padx=10)

    def _sec(self, parent, title, subtitle=None):
        f = tk.Frame(parent, bg=T.BG)
        tk.Label(f, text=title, bg=T.BG, fg=T.TEXT,
                 font=T.FONT_H1).pack(anchor="w")
        if subtitle:
            tk.Label(f, text=subtitle, bg=T.BG, fg=T.TEXT_MUTED,
                     font=T.FONT_SMALL).pack(anchor="w", pady=(2, 0))
        return f


if __name__ == "__main__":
    Gallery().mainloop()
