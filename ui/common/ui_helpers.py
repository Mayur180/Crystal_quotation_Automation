# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# UI HELPERS
#
# Keyboard shortcuts shared across windows.
#
# File:
#   ui/ui_helpers.py
#
# Two functions:
#   install_table_shortcuts(tree, on_enter, on_delete)
#   install_modal_shortcuts(window, on_escape, on_enter)
# ============================================================

import tkinter as tk
from tkinter import ttk


def set_window_icon(window):
    """
    Set the CRYSTAL logo as the window icon (title bar + taskbar).
    Works in both script mode and frozen .exe mode.
    """
    try:
        import sys as _sys
        from pathlib import Path as _Path

        if getattr(_sys, "frozen", False):
            _base = _Path(_sys.executable).parent
        else:
            _here = _Path(__file__).resolve().parent
            _base = None
            for _candidate in [_here, *_here.parents]:
                if (_candidate / "assets").is_dir():
                    _base = _candidate
                    break
            if _base is None:
                _base = _here.parent

        _ico = _base / "assets" / "logo" / "LOGO.ico"

        if _ico.is_file():
            window.iconbitmap(default=str(_ico))
    except Exception:
        pass





# ============================================================
# TABLE KEYBOARD NAVIGATION
# ============================================================

def install_table_shortcuts(tree, on_enter=None, on_delete=None):
    """
    Wire standard keyboard navigation on a ttk.Treeview:

        ↑ / ↓       Move selection up / down one row
        PageUp      Move up one visible page
        PageDown    Move down one visible page
        Home        Jump to first row
        End         Jump to last row
        Enter       Call on_enter(selected_id)
        Delete      Call on_delete(selected_id)

    The tree must have focus for these to fire — click once on
    it, or call tree.focus_set() after showing the window.
    """

    if tree is None:
        return

    # Ensure tree can receive focus
    try:
        tree.configure(takefocus=True)
    except Exception:
        pass

    # ---------- helpers ----------

    def _items():
        try:
            return tree.get_children()
        except Exception:
            return []

    def _current_index():
        sel = tree.selection()
        if not sel:
            return -1
        items = _items()
        try:
            return items.index(sel[0])
        except ValueError:
            return -1

    def _select_index(index):
        items = _items()
        if not items:
            return
        if index < 0:
            index = 0
        if index >= len(items):
            index = len(items) - 1
        item = items[index]
        tree.selection_set(item)
        tree.focus(item)
        tree.see(item)

    # ---------- movement ----------

    def move_up(_event=None):
        idx = _current_index()
        if idx < 0:
            _select_index(0)
        else:
            _select_index(idx - 1)
        return "break"

    def move_down(_event=None):
        idx = _current_index()
        if idx < 0:
            _select_index(0)
        else:
            _select_index(idx + 1)
        return "break"

    def page_up(_event=None):
        idx = _current_index()
        if idx < 0:
            idx = 0
        _select_index(idx - 15)
        return "break"

    def page_down(_event=None):
        idx = _current_index()
        if idx < 0:
            idx = 0
        _select_index(idx + 15)
        return "break"

    def go_home(_event=None):
        _select_index(0)
        return "break"

    def go_end(_event=None):
        items = _items()
        if items:
            _select_index(len(items) - 1)
        return "break"

    # ---------- actions ----------

    def activate(_event=None):
        sel = tree.selection()
        if not sel:
            return "break"
        if on_enter is not None:
            try:
                on_enter(sel[0])
            except Exception:
                pass
        return "break"

    def delete(_event=None):
        sel = tree.selection()
        if not sel:
            return "break"
        if on_delete is not None:
            try:
                on_delete(sel[0])
            except Exception:
                pass
        return "break"

    # ---------- bind ----------

    tree.bind("<Up>", move_up, add="+")
    tree.bind("<Down>", move_down, add="+")
    tree.bind("<Prior>", page_up, add="+")     # Page Up
    tree.bind("<Next>", page_down, add="+")    # Page Down
    tree.bind("<Home>", go_home, add="+")
    tree.bind("<End>", go_end, add="+")
    tree.bind("<Return>", activate, add="+")
    tree.bind("<KP_Enter>", activate, add="+")
    tree.bind("<Delete>", delete, add="+")


# ============================================================
# MODAL / WINDOW KEYBOARD SHORTCUTS
# ============================================================

def install_modal_shortcuts(window, on_escape=None, on_enter=None):
    """
    Wire Escape and Enter on a Toplevel window:

        Escape  Close / cancel — calls on_escape() if given,
                otherwise window.destroy()
        Enter   Confirm — calls on_enter() if given

    Binds on the window and forwards when focus is a Text widget
    is not required for Enter; Escape always works.
    """

    if window is None:
        return

    def escape(_event=None):
        if on_escape is not None:
            try:
                on_escape()
                return "break"
            except Exception:
                pass
        try:
            window.destroy()
        except Exception:
            pass
        return "break"

    def enter(_event=None):
        if on_enter is not None:
            try:
                on_enter()
            except Exception:
                pass
            return "break"
        return None

    try:
        window.bind("<Escape>", escape, add="+")
    except Exception:
        pass

    if on_enter is not None:
        try:
            window.bind("<Return>", enter, add="+")
            window.bind("<KP_Enter>", enter, add="+")
        except Exception:
            pass


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()
    root.title("UI Helpers — Demo")
    root.geometry("500x400")

    tree = ttk.Treeview(root, columns=("a", "b"), show="headings",
                        height=12)
    tree.heading("a", text="Name")
    tree.heading("b", text="Value")
    tree.pack(fill="both", expand=True, padx=20, pady=20)

    for i in range(20):
        tree.insert("", "end", iid=str(i), values=(f"Row {i+1}", i * 10))

    install_table_shortcuts(
        tree,
        on_enter=lambda i: print("Enter on", i),
        on_delete=lambda i: print("Delete on", i),
    )

    tree.focus_set()

    root.mainloop()