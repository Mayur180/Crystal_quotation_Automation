"""CRYSTAL — Terms & Conditions editor (modal)."""
import tkinter as tk
from tkinter import ttk, messagebox

from ui.crystal import theme as T
from ui.crystal import widgets as W


class TermsEditor(tk.Toplevel):
    def __init__(self, parent, terms):
        super().__init__(parent)
        self.title("CRYSTAL | Edit Terms & Conditions")
        self.configure(bg=T.BG)
        self.geometry("820x660")
        self.minsize(720, 560)
        self.transient(parent)
        self.grab_set()
        try:
            W.set_window_icon(self)
        except Exception:
            pass
        W.apply_ttk_theme(self)

        self.working_terms = [{"title": t, "value": v} for t, v in terms]
        self.result = None
        self.selected_index = None

        self._build_interface()
        self._refresh_list()
        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(self, on_escape=self._cancel)
        except Exception:
            self.bind("<Escape>", lambda e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build_interface(self):
        header = W.PageHeader(
            self, title="Terms & Conditions",
            subtitle="Edit the terms shown on quotations",
            padx=24,
        )
        header.pack(fill="x")

        footer = tk.Frame(
            self, bg=T.SURFACE, height=64,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        W.GhostButton(footer, "Cancel", self._cancel, padx=18, pady=7).pack(
            side="right", padx=(0, 24), pady=13)
        W.PrimaryButton(footer, "Save terms", self._save, padx=20, pady=8).pack(
            side="right", padx=(0, 8), pady=13)

        body = tk.Frame(self, bg=T.BG)
        body.pack(fill="both", expand=True, padx=24, pady=(14, 12))

        list_card = tk.Frame(
            body, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        list_card.pack(fill="both", expand=True)

        actions = tk.Frame(body, bg=T.BG)
        actions.pack(fill="x", pady=(10, 0))

        def action(text, cmd):
            return tk.Button(
                actions, text=text, command=cmd,
                bg=T.SURFACE, fg=T.TEXT_BODY,
                activebackground=T.SURFACE_HOVER, activeforeground=T.TEXT,
                relief="flat", bd=0, highlightthickness=1,
                highlightbackground=T.BORDER, highlightcolor=T.FOCUS,
                font=T.FONT_SMALL, cursor="hand2", padx=12, pady=5,
            )

        action("Move up", self._move_up).pack(side="left")
        action("Move down", self._move_down).pack(side="left", padx=(8, 0))
        action("Remove", self._delete).pack(side="left", padx=(8, 0))

        self.tree = ttk.Treeview(
            list_card, columns=("title", "value"),
            show="headings", height=7,
        )
        self.tree.heading("title", text="Term", anchor="w")
        self.tree.heading("value", text="Value", anchor="w")
        self.tree.column("title", width=200, anchor="w")
        self.tree.column("value", width=520, anchor="w", stretch=True)
        self.tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        self.tree.tag_configure("oddrow", background=T.SURFACE)

        vsb = ttk.Scrollbar(list_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", pady=2, padx=(0, 2))
        self.tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        editor = tk.Frame(
            body, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        editor.pack(fill="x", pady=(10, 0))

        inner = tk.Frame(editor, bg=T.SURFACE)
        inner.pack(fill="x", padx=16, pady=14)

        tk.Label(
            inner, text="TERM TITLE", bg=T.SURFACE,
            fg=T.TEXT_MUTED, font=T.FONT_LABEL,
        ).pack(anchor="w")

        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(
            inner, textvariable=self.title_var,
            bg=T.SURFACE, fg=T.TEXT, relief="flat", bd=0,
            highlightthickness=1, highlightbackground=T.BORDER,
            highlightcolor=T.FOCUS, font=T.FONT_BODY,
            insertbackground=T.ACCENT,
        )
        self.title_entry.pack(fill="x", ipady=6, pady=(4, 10))

        tk.Label(
            inner, text="TERM VALUE", bg=T.SURFACE,
            fg=T.TEXT_MUTED, font=T.FONT_LABEL,
        ).pack(anchor="w")

        value_wrap = tk.Frame(
            inner, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        value_wrap.pack(fill="x", pady=(4, 10))

        self.value_text = tk.Text(
            value_wrap, height=3, wrap="word",
            bg=T.SURFACE, fg=T.TEXT_BODY,
            relief="flat", bd=0, highlightthickness=0,
            font=T.FONT_SMALL, insertbackground=T.ACCENT,
        )
        self.value_text.pack(fill="x", padx=8, pady=6)

        W.PrimaryButton(
            inner, "Add term", self._add, padx=16, pady=6,
        ).pack(anchor="e")

        list_card.pack_forget()
        actions.pack_forget()
        editor.pack_forget()
        editor.pack(side="bottom", fill="x", pady=(10, 0))
        actions.pack(side="bottom", fill="x", pady=(10, 0))
        list_card.pack(fill="both", expand=True)

    def _refresh_list(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for i, term in enumerate(self.working_terms):
            self.tree.insert(
                "", "end", iid=str(i),
                values=(term["title"], term["value"]),
                tags=("evenrow" if i % 2 == 0 else "oddrow",),
            )

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _on_select(self, _e=None):
        index = self._selected()
        if index is None or not (0 <= index < len(self.working_terms)):
            return
        term = self.working_terms[index]
        self.selected_index = index
        self.title_var.set(term["title"])
        self.value_text.delete("1.0", "end")
        self.value_text.insert("1.0", term["value"])

    def _read_fields(self):
        title = self.title_var.get().strip()
        value = self.value_text.get("1.0", "end").strip()
        if not title or not value:
            messagebox.showwarning(
                "Incomplete term",
                "Enter both a title and a value for the term.",
                parent=self,
            )
            return None
        return title, value

    def _add(self):
        fields = self._read_fields()
        if not fields:
            return
        self.working_terms.append({"title": fields[0], "value": fields[1]})
        self._refresh_list()
        self.tree.selection_set(str(len(self.working_terms) - 1))

    def _delete(self):
        index = self._selected()
        if index is None:
            messagebox.showinfo(
                "Select a term", "Choose a term to remove.", parent=self)
            return
        self.working_terms.pop(index)
        self._refresh_list()
        self.title_var.set("")
        self.value_text.delete("1.0", "end")

    def _move_up(self):
        index = self._selected()
        if index is None or index == 0:
            return
        terms = self.working_terms
        terms[index - 1], terms[index] = terms[index], terms[index - 1]
        self._refresh_list()
        self.tree.selection_set(str(index - 1))

    def _move_down(self):
        index = self._selected()
        if index is None or index >= len(self.working_terms) - 1:
            return
        terms = self.working_terms
        terms[index + 1], terms[index] = terms[index], terms[index + 1]
        self._refresh_list()
        self.tree.selection_set(str(index + 1))

    def _save(self):
        self.result = [(t["title"], t["value"]) for t in self.working_terms]
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()
