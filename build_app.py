import PyInstaller.__main__
import os

args = [
    'main.py',
    '--name=CRYSTAL_Quotation_Manager',
    '--windowed',
    '--onefile',
    '--add-data=assets;assets',
    '--add-data=data;data',
    '--add-data=ui;ui',
    '--add-data=app;app',
    '--add-data=quotation_generator_crystal.py;.',
    '--hidden-import=bcrypt',
    '--hidden-import=requests',
    '--hidden-import=docx',
    '--hidden-import=docx2pdf',
    '--hidden-import=pymupdf',
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=PIL.ImageTk',
    '--hidden-import=tkinter',
    '--hidden-import=tkinter.ttk',
    '--hidden-import=tkinter.messagebox',
    '--hidden-import=tkinter.filedialog',
    '--hidden-import=json',
    '--hidden-import=threading',
    '--hidden-import=datetime',
    '--hidden-import=decimal',
    '--hidden-import=pathlib',
    '--hidden-import=win32com',
    '--hidden-import=win32com.client',
    '--collect-all=docx',
    '--collect-all=pymupdf',
    '--clean',
    '--noconfirm',
]

# Add icon if it exists
if os.path.exists('assets/crystal.ico'):
    args.insert(4, '--icon=assets/crystal.ico')

PyInstaller.__main__.run(args)
