import tkinter as tk
import sys
from pathlib import Path

# Write log to file so we know if it ran
log = Path.home() / "Desktop" / "tkinter_test_log.txt"
with open(log, "w") as f:
    f.write("Script started\n")
    f.write(f"Python: {sys.version}\n")
    f.write(f"Tk version: {tk.TkVersion}\n")

try:
    root = tk.Tk()
    with open(log, "a") as f:
        f.write("Tk root created\n")
    root.title("Test Window")
    root.geometry("400x300")
    tk.Label(root, text="Tkinter Works!", font=("Arial", 20)).pack(pady=80)
    with open(log, "a") as f:
        f.write("Labels created\n")
    root.after(10000, root.destroy)  # auto-close after 10s
    root.mainloop()
    with open(log, "a") as f:
        f.write("Window closed normally\n")
except Exception as e:
    with open(log, "a") as f:
        f.write(f"ERROR: {e}\n")
