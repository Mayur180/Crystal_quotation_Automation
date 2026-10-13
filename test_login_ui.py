"""Temporary harness — just to preview the login window."""
import tkinter as tk
from ui.login_window import LoginWindow

def on_success(session):
    print("\n✅ LOGIN SUCCESS")
    print("   User:", session.username)
    print("   Name:", session.full_name)
    print("   Modules:", session.modules)
    root.destroy()

def on_cancel():
    print("\n❌ Cancelled")
    root.destroy()

root = tk.Tk()
root.title("CRYSTAL v4 — Login Test")
root.geometry("700x600")
root.configure(bg="#F4F6F8")

LoginWindow(root, on_success=on_success, on_cancel=on_cancel)

root.mainloop()
