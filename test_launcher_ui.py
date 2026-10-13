"""Temporary harness — preview the launcher window."""
import tkinter as tk
from ui.launcher_window import LauncherWindow
from app.services.auth_service import UserSession

# Fake session — pretend admin just logged in
session = UserSession(
    user_id="U001",
    username="admin",
    full_name="System Administrator",
    modules=["VMM", "Crystal"],
)

def on_select(module_name):
    print(f"\n✅ MODULE SELECTED: {module_name}")
    root.destroy()

def on_logout():
    print("\n🚪 Logout clicked")
    root.destroy()

root = tk.Tk()
root.title("CRYSTAL v4 — Launcher Test")
root.geometry("900x650")
root.configure(bg="#F4F6F8")

LauncherWindow(root, session=session, on_select=on_select, on_logout=on_logout)

root.mainloop()
