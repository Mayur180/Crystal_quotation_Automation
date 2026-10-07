"""
Create-PDF-on-demand feature.

- When user clicks Open PDF on a quotation with no PDF,
  prompt to create it, convert DOCX -> PDF, save path, open.
- Adds update_quotation_pdf_path() to history service.
"""

import shutil
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SVC = ROOT / "app" / "services" / "quotation_history_service.py"
UI  = ROOT / "ui" / "quotation_history.py"


# ============================================================
# 1. Add update_quotation_pdf_path() to service
# ============================================================

shutil.copy2(SVC, SVC.with_suffix(".py.CREATE_PDF_BACKUP"))
print(f"[backup] {SVC.name}")

svc = SVC.read_text(encoding="utf-8")

if "def update_quotation_pdf_path" not in svc:
    new_func = '''

def update_quotation_pdf_path(quotation_number, pdf_path):
    """Update the pdf_path field of a stored quotation.

    Returns True if a record was updated, False otherwise.
    """
    target = _text(quotation_number)
    if not target:
        return False

    records = _load_raw()
    updated = False
    for r in records:
        if _text(r.get("quotation_number")) == target:
            r["pdf_path"] = _text(pdf_path)
            updated = True

    if not updated:
        return False

    try:
        _save_raw(records)
        return True
    except Exception:
        return False

'''
    # Insert before "def get_quotation"
    marker = "def get_quotation(quotation_number):"
    if marker in svc:
        svc = svc.replace(marker, new_func.lstrip("\n") + marker, 1)
        SVC.write_text(svc, encoding="utf-8")
        print("[ok] service: update_quotation_pdf_path added")
    else:
        print("[warn] service: get_quotation anchor not found")
else:
    print("[skip] service: function already exists")


# ============================================================
# 2. Patch ui/quotation_history.py
# ============================================================

shutil.copy2(UI, UI.with_suffix(".py.CREATE_PDF_BACKUP"))
print(f"[backup] {UI.name}")

ui = UI.read_text(encoding="utf-8")


# ---- 2a. Replace _open_pdf ----
old_pdf = '''    def _open_pdf(self):
        rec = self._current_record()
        if not rec:
            messagebox.showinfo("No selection",
                                "Please select a quotation first.",
                                parent=self)
            return
        path = rec.get("pdf_path")
        if not path:
            messagebox.showinfo(
                "No PDF",
                "This quotation does not have a PDF copy.",
                parent=self,
            )
            return
        if not _open_path(path):
            messagebox.showerror(
                "File not found",
                f"PDF file is missing:\\n{path}",
                parent=self,
            )'''

new_pdf = '''    def _open_pdf(self):
        rec = self._current_record()
        if not rec:
            messagebox.showinfo("No selection",
                                "Please select a quotation first.",
                                parent=self)
            return

        path = rec.get("pdf_path")

        # ---- case 1: PDF exists ----
        if path and os.path.isfile(path):
            if not _open_path(path):
                messagebox.showerror(
                    "File not found",
                    f"PDF file is missing:\\n{path}",
                    parent=self,
                )
            return

        # ---- case 2: no PDF -> ask ----
        ok = messagebox.askyesno(
            "PDF not created",
            "PDF is not created for this quotation.\\n\\n"
            "Do you want to create it now?",
            parent=self,
        )
        if not ok:
            return

        self._create_pdf_from_docx(rec)

    def _create_pdf_from_docx(self, record):
        """Convert the DOCX for this quotation into a PDF and open it."""
        docx_path = record.get("docx_path") or ""

        if not docx_path or not os.path.isfile(docx_path):
            messagebox.showerror(
                "Cannot create PDF",
                "The DOCX file for this quotation is missing.\\n\\n"
                "Without a DOCX we cannot generate a PDF.",
                parent=self,
            )
            return

        pdf_path = os.path.splitext(docx_path)[0] + ".pdf"

        # Already exists? just open it
        if os.path.isfile(pdf_path):
            try:
                from app.services.quotation_history_service import (
                    update_quotation_pdf_path,
                )
                update_quotation_pdf_path(
                    record.get("quotation_number"), pdf_path
                )
            except Exception:
                pass
            _open_path(pdf_path)
            self._reload()
            return

        # Show progress
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            self._do_convert(docx_path, pdf_path)
        finally:
            try:
                self.config(cursor="")
            except Exception:
                pass

        if not os.path.isfile(pdf_path):
            messagebox.showerror(
                "PDF creation failed",
                "PDF could not be created.\\n\\n"
                "Check that Microsoft Word is available and the "
                "DOCX file is not locked.",
                parent=self,
            )
            return

        # Save new path back to history
        try:
            from app.services.quotation_history_service import (
                update_quotation_pdf_path,
            )
            update_quotation_pdf_path(
                record.get("quotation_number"), pdf_path
            )
        except Exception:
            pass

        # Open it and refresh the table (Files column updates)
        _open_path(pdf_path)
        try:
            self._reload()
        except Exception:
            pass

    def _do_convert(self, docx_path, pdf_path):
        """Run docx2pdf, fall back to win32com if needed."""
        # Try docx2pdf first (simplest API)
        try:
            from docx2pdf import convert
            convert(docx_path, pdf_path)
            if os.path.isfile(pdf_path):
                return
        except Exception:
            pass

        # Fallback: direct win32com Word automation
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0

            doc = word.Documents.Open(os.path.abspath(docx_path))

            # FileFormat=17 is wdFormatPDF
            doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)

            doc.Close(SaveChanges=False)
            word.Quit()
        except Exception as e:
            messagebox.showerror(
                "PDF conversion error",
                f"docx2pdf and Word automation both failed.\\n\\n{e}",
                parent=self,
            )'''

if old_pdf in ui:
    ui = ui.replace(old_pdf, new_pdf, 1)
    print("[ok] ui: _open_pdf replaced + _create_pdf_from_docx added")
else:
    print("[warn] ui: _open_pdf anchor not found")


UI.write_text(ui, encoding="utf-8")


# ============================================================
# 3. Compile check
# ============================================================

print()
print("=" * 60)
print("Compile check")
print("=" * 60)

ok = True
for p in (SVC, UI):
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"[ok] {p.relative_to(ROOT)}")
    except py_compile.PyCompileError as e:
        print(f"[FAIL] {p.relative_to(ROOT)}: {e}")
        ok = False

if ok:
    print()
    print("=" * 60)
    print("Create-PDF feature installed.")
    print("=" * 60)
    print()
    print("Test:")
    print("  1. python main.py -> Quotation History")
    print("  2. Pick a quotation with a DOCX but no PDF")
    print("  3. Click 'Open PDF'")
    print("  4. Confirm -> PDF is generated and opens")
