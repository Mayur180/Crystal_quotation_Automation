"""User Management window (admin-only)."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from app.services import user_service as US
from ui.crystal import theme as T
from ui.crystal import widgets as W


def _friendly_ts(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return "—"
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.strftime("%d-%m-%Y %H:%M")
    except Exception:
        return text


class UserManager(tk.Toplevel):

    BG = T.BG
    CARD = T.SURFACE
    TEXT = T.TEXT
    MUTED = T.TEXT_MUTED
    BORDER = T.BORDER

    def __init__(self, parent, *, current_username=""):
        super().__init__(parent)
        self.title("CRYSTAL | User Management")
        self.geometry("1000x640")
        self.minsize(900, 560)
        self.configure(bg=self.BG)
        W.set_window_icon(self)
        self.transient(parent)
        self.grab_set()
        self._current_username = current_username
        W.apply_ttk_theme(self)
        self._build()
        self._refresh()
        try:
            self.bind("<Escape>", lambda _e: self.destroy())
        except Exception:
            pass

    def _build(self):
        header = W.PageHeader(
            self, title="User Management",
            subtitle="Accounts, roles and module access",
            meta="—", padx=28,
        )
        header.pack(fill="x")
        self.count_label = header.meta_label

        # ---- toolbar ----
        bar = tk.Frame(
            self, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        bar.pack(fill="x", padx=28, pady=(14, 10))
        row = tk.Frame(bar, bg=T.SURFACE)
        row.pack(fill="x", padx=14, pady=10)
        tk.Label(
            row, text="Select a user to edit, reset a password or change status.",
            bg=T.SURFACE, fg=T.TEXT_MUTED, font=T.FONT_SMALL,
        ).pack(side="left")
        W.PrimaryButton(
            row, "Add user", self._on_add, icon="+", padx=14, pady=7,
        ).pack(side="right")

        # ---- footer (pack before expanding table) ----
        foot = tk.Frame(
            self, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        foot.pack(side="bottom", fill="x")
        W.GhostButton(
            foot, "Close", self.destroy, padx=18, pady=7,
        ).pack(side="right", padx=22, pady=13)
        W.DangerButton(
            foot, "Delete", self._on_delete, padx=13, pady=7,
        ).pack(side="right", padx=(0, 10), pady=13)
        W.GhostButton(
            foot, "Deactivate", self._on_deactivate, padx=13, pady=7,
        ).pack(side="right", padx=(0, 6), pady=13)
        W.GhostButton(
            foot, "Activate", self._on_activate, padx=13, pady=7,
        ).pack(side="right", padx=(0, 6), pady=13)
        W.GhostButton(
            foot, "Reset password", self._on_reset_pw, padx=13, pady=7,
        ).pack(side="right", padx=(0, 6), pady=13)
        W.GhostButton(
            foot, "Edit", self._on_edit, padx=13, pady=7,
        ).pack(side="right", padx=(0, 6), pady=13)

        # ---- table ----
        card = tk.Frame(
            self, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=28, pady=(0, 14))

        cols = ("username", "full_name", "role", "modules", "active", "created")
        self.tree = ttk.Treeview(card, columns=cols,
                                 show="headings", selectmode="browse")
        for col, label, width, anchor, stretch in [
            ("username",  "Username",  150, "w", False),
            ("full_name", "Full name", 220, "w", True),
            ("role",      "Role",      100, "w", False),
            ("modules",   "Modules",   150, "w", False),
            ("active",    "Status",    100, "w", False),
            ("created",   "Created",   150, "e", False),
        ]:
            self.tree.heading(col, text=label, anchor=anchor)
            self.tree.column(col, width=width, anchor=anchor, stretch=stretch)
        self.tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        self.tree.tag_configure("oddrow", background=T.SURFACE)
        self.tree.tag_configure("inactive", foreground=T.TEXT_MUTED)

        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 2), pady=(0, 2))
        self.tree.pack(side="left", fill="both", expand=True,
                       padx=2, pady=(0, 2))

        self._empty = W.EmptyState(
            card, icon="👤", title="No users found",
            hint="Add a user to give someone access to the app.",
        )

    def _set_empty(self, visible):
        try:
            if visible:
                self._empty.place(relx=0.5, rely=0.5, anchor="center")
                self._empty.lift()
            else:
                self._empty.place_forget()
        except Exception:
            pass

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        try:
            users = US.load_users()
        except Exception as e:
            messagebox.showerror("User Management",
                                 f"Could not load users:\n{e}", parent=self)
            users = []
        for i, u in enumerate(users):
            modules = ", ".join(US.get_user_modules(u.get("user_id", "")))
            active = bool(u.get("is_active", True))
            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            if not active:
                tags.append("inactive")
            self.tree.insert(
                "", "end", iid=u.get("user_id", ""),
                values=(
                    u.get("username", ""),
                    u.get("full_name", "") or "—",
                    (u.get("role") or "user").capitalize(),
                    modules or "—",
                    "Active" if active else "Inactive",
                    _friendly_ts(u.get("created_at")),
                ),
                tags=tuple(tags),
            )
        if self.count_label is not None:
            self.count_label.configure(text=f"{len(users):,} user(s)")
        self._set_empty(not users)

    def _selected_user(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return US.find_user_by_id(sel[0])

    def _on_add(self):
        UserEditDialog(self, current_username=self._current_username,
                       on_saved=self._refresh)

    def _on_edit(self):
        u = self._selected_user()
        if not u:
            messagebox.showinfo("Edit user", "Select a user first.", parent=self)
            return
        UserEditDialog(self, user=u,
                       current_username=self._current_username,
                       on_saved=self._refresh)

    def _on_reset_pw(self):
        u = self._selected_user()
        if not u:
            messagebox.showinfo("Reset password", "Select a user first.", parent=self)
            return
        from tkinter import simpledialog
        new_pw = simpledialog.askstring(
            "Reset password", f"New password for {u['username']}:",
            show="*", parent=self)
        if not new_pw:
            return
        try:
            US.set_password(u["user_id"], new_pw)
            messagebox.showinfo("Reset password", "Password updated.", parent=self)
        except Exception as e:
            messagebox.showerror("Reset password", str(e), parent=self)

    def _on_deactivate(self):
        u = self._selected_user()
        if not u:
            messagebox.showinfo("Deactivate", "Select a user first.", parent=self)
            return
        if not messagebox.askyesno("Deactivate",
                                   f"Deactivate '{u['username']}'?",
                                   parent=self):
            return
        try:
            US.deactivate_user(u["user_id"])
            self._refresh()
        except Exception as e:
            messagebox.showerror("Deactivate", str(e), parent=self)

    def _on_activate(self):
        u = self._selected_user()
        if not u:
            messagebox.showinfo("Activate", "Select a user first.", parent=self)
            return
        if u.get("is_active", True):
            messagebox.showinfo("Activate",
                                f"'{u['username']}' is already active.",
                                parent=self)
            return
        try:
            US.activate_user(u["user_id"])
            self._refresh()
        except Exception as e:
            messagebox.showerror("Activate", str(e), parent=self)

    def _on_delete(self):
        u = self._selected_user()
        if not u:
            messagebox.showinfo("Delete", "Select a user first.", parent=self)
            return
        confirmed = messagebox.askyesno(
            "Delete user - permanent",
            f"Permanently delete '{u['username']}'?\n\n"
            f"This removes the account and all module access.\n"
            f"This cannot be undone.",
            parent=self,
            icon="warning",
        )
        if not confirmed:
            return
        try:
            US.delete_user(u["user_id"], by_username=self._current_username)
            self._refresh()
        except Exception as e:
            messagebox.showerror("Delete", str(e), parent=self)


class UserEditDialog(tk.Toplevel):

    CARD = T.SURFACE

    def __init__(self, parent, *, user=None, current_username="", on_saved=None):
        super().__init__(parent)
        self.title("CRYSTAL | Edit user" if user else "CRYSTAL | New user")
        self.geometry("500x600")
        self.resizable(False, False)
        self.configure(bg=self.CARD)
        W.set_window_icon(self)
        self.transient(parent)
        self.grab_set()
        self._user = user
        self._current_username = current_username
        self._on_saved = on_saved or (lambda: None)
        W.apply_ttk_theme(self)
        self._build()
        if user:
            self._load_user(user)
        try:
            self.bind("<Escape>", lambda _e: self.destroy())
        except Exception:
            pass

    def _build(self):
        head = tk.Frame(self, bg=self.CARD)
        head.pack(fill="x", padx=28, pady=(22, 0))
        tk.Label(
            head, text="Edit user" if self._user else "New user",
            bg=self.CARD, fg=T.TEXT, font=T.FONT_H1, anchor="w",
        ).pack(anchor="w")
        tk.Label(
            head,
            text="Account details, role and module access.",
            bg=self.CARD, fg=T.TEXT_MUTED, font=T.FONT_SMALL, anchor="w",
        ).pack(anchor="w", pady=(2, 0))
        tk.Frame(self, bg=T.ACCENT, height=2).pack(
            fill="x", padx=28, pady=(12, 0))

        # footer first so it never gets clipped
        foot = tk.Frame(self, bg=self.CARD)
        foot.pack(side="bottom", fill="x", padx=28, pady=(10, 18))
        W.PrimaryButton(
            foot, "Save user", self._on_save, padx=16, pady=8,
        ).pack(side="right")
        W.GhostButton(
            foot, "Cancel", self.destroy, padx=16, pady=8,
        ).pack(side="right", padx=(0, 8))

        wrap = tk.Frame(self, bg=self.CARD)
        wrap.pack(fill="both", expand=True, padx=28, pady=(18, 0))

        def _lbl(text):
            tk.Label(wrap, text=text, bg=self.CARD, fg=T.TEXT_MUTED,
                     font=T.FONT_LABEL, anchor="w").pack(
                anchor="w", pady=(10, 4))

        self.var_username = tk.StringVar()
        self.var_full = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_role = tk.StringVar(value="user")
        self.var_module_vmm = tk.BooleanVar(value=False)
        self.var_module_crystal = tk.BooleanVar(value=False)

        _lbl("USERNAME *")
        self.username_entry = W.SearchEntry(
            wrap, textvariable=self.var_username,
            placeholder="e.g. accounts", show_icon=False,
        )
        self.username_entry.pack(fill="x")

        _lbl("FULL NAME")
        W.SearchEntry(
            wrap, textvariable=self.var_full,
            placeholder="Display name", show_icon=False,
        ).pack(fill="x")

        _lbl("PASSWORD *" + ("  (blank = keep current)" if self._user else ""))
        self.pw_entry = W.SearchEntry(
            wrap, textvariable=self.var_password,
            placeholder="Minimum 4 characters", show_icon=False,
        )
        self.pw_entry.pack(fill="x")
        self.pw_entry.entry.configure(show="*")

        _lbl("ROLE")
        ttk.Combobox(
            wrap, textvariable=self.var_role,
            values=["user", "admin"], state="readonly",
            font=T.FONT_SMALL,
        ).pack(fill="x", ipady=4)

        _lbl("MODULE ACCESS")
        mod_row = tk.Frame(wrap, bg=self.CARD)
        mod_row.pack(fill="x", pady=(2, 0))
        for text, var, pad in (
            ("Crystal", self.var_module_crystal, (0, 18)),
            ("VMM", self.var_module_vmm, (0, 0)),
        ):
            tk.Checkbutton(
                mod_row, text=text, variable=var,
                bg=self.CARD, fg=T.TEXT_BODY, font=T.FONT_BODY,
                activebackground=self.CARD, activeforeground=T.TEXT,
                selectcolor=T.SURFACE, highlightthickness=0,
                bd=0, cursor="hand2",
            ).pack(side="left", padx=pad)

        try:
            self.username_entry.entry.focus_set()
        except Exception:
            pass

    def _load_user(self, u):
        self.var_username.set(u.get("username", ""))
        self.var_full.set(u.get("full_name", ""))
        self.var_role.set(u.get("role", "user") or "user")
        mods = US.get_user_modules(u.get("user_id", ""))
        self.var_module_vmm.set("VMM" in mods)
        self.var_module_crystal.set("Crystal" in mods)
        try:
            self.username_entry.entry.configure(state="readonly",
                                               readonlybackground=T.SURFACE_ALT)
        except Exception:
            pass

    def _on_save(self):
        username = self.var_username.get().strip()
        full = self.var_full.get().strip()
        pw = self.var_password.get()
        role = self.var_role.get()
        modules = []
        if self.var_module_vmm.get():
            modules.append("VMM")
        if self.var_module_crystal.get():
            modules.append("Crystal")
        if not username:
            messagebox.showerror("Save failed", "Username is required.",
                                 parent=self)
            return
        if not self._user and not pw.strip():
            messagebox.showerror("Save failed", "Password is required.",
                                 parent=self)
            return
        if not modules:
            messagebox.showerror("Save failed",
                                 "Select at least one module.", parent=self)
            return
        try:
            if self._user:
                US.update_user(self._user["user_id"],
                               username=username, full_name=full, role=role)
                if pw.strip():
                    US.set_password(self._user["user_id"], pw)
                US.set_user_modules(self._user["user_id"], modules)
            else:
                US.create_user(username=username, password=pw,
                               full_name=full, role=role,
                               modules=modules,
                               created_by=self._current_username)
        except Exception as e:
            messagebox.showerror("Save failed", str(e), parent=self)
            return
        self._on_saved()
        self.destroy()
