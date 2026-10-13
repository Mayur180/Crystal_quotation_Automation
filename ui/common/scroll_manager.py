"""
CRYSTAL — unified mouse wheel router.

Tk's `bind_all` uses a single global slot per event. When multiple
windows each register a handler, they overwrite each other, and
calling `unbind_all` in one window kills the handler for every
window. That produces the "scroll wheel doesn't work / scrolls the
wrong canvas" bug.

This module installs ONE global wheel handler at app startup.
Individual widgets (canvas + scrollbar) register with it. When a
wheel event fires, the handler walks up from the widget under the
pointer until it finds a registered canvas, then scrolls it.
"""

from __future__ import annotations
import tkinter as tk


class ScrollManager:
    _installed = False
    _registry = {}  # id(widget) -> (widget, orientation)

    @classmethod
    def register(cls, widget, orientation: str = "vertical"):
        """Register a Canvas-like widget as scrollable."""
        try:
            if widget is None:
                return
            cls._registry[id(widget)] = (widget, orientation)
            if not cls._installed:
                cls._install()
        except Exception:
            pass

    @classmethod
    def unregister(cls, widget):
        try:
            cls._registry.pop(id(widget), None)
        except Exception:
            pass

    @classmethod
    def _install(cls):
        cls._installed = True
        root = tk._default_root
        if root is None:
            return
        root.bind_all("<MouseWheel>", cls._on_wheel, add="+")
        root.bind_all("<Shift-MouseWheel>", cls._on_wheel, add="+")
        root.bind_all("<Button-4>", cls._on_wheel, add="+")
        root.bind_all("<Button-5>", cls._on_wheel, add="+")

    @classmethod
    def _find_target(cls, widget):
        """Walk up the parent chain looking for a registered canvas."""
        node = widget
        try:
            while node is not None:
                if id(node) in cls._registry:
                    return cls._registry[id(node)]
                node = getattr(node, "master", None)
        except Exception:
            pass
        return None

    @classmethod
    def _on_wheel(cls, event):
        try:
            target = cls._find_target(event.widget)
            if target is None:
                return

            canvas, orientation = target
            try:
                if not canvas.winfo_exists():
                    return
            except Exception:
                return

            delta = getattr(event, "delta", 0)
            num = getattr(event, "num", None)

            # Linux uses Button-4/5
            if num == 4:
                step = -3
            elif num == 5:
                step = 3
            elif delta:
                step = -1 if delta > 0 else 1
                magnitude = max(1, min(6, int(abs(delta) / 120) or 1))
                step *= magnitude
            else:
                return

            if orientation == "horizontal":
                canvas.xview_scroll(step, "units")
            else:
                canvas.yview_scroll(step, "units")
        except Exception:
            pass
