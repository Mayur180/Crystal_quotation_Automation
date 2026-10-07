import shutil
import py_compile
from pathlib import Path

FORM = Path("ui/quotation_form.py")
shutil.copy2(FORM, FORM.with_suffix(".py.PREFILL2_BACKUP"))
print("[backup]", FORM.with_suffix(".py.PREFILL2_BACKUP"))

s = FORM.read_text(encoding="utf-8")

# Replace the entire _apply_prefill method
old = '''    def _apply_prefill(self, data):
        """Populate form fields from a history record (used by Duplicate)."""
        if not data:
            return
        try:
            # customer block
            self.customer_name.set(data.get("customer_name", "") or "")
            self.company.set(data.get("customer_company", "") or "")
            self.phone.set(data.get("customer_phone", "") or "")
            self.email.set(data.get("customer_email", "") or "")

            # product block — set model then fire the change handler
            model = data.get("model", "") or ""
            if model:
                # ensure the combo has the model as a choice
                try:
                    values = list(self.model_combo["values"])
                    if model not in values:
                        values.append(model)
                        self.model_combo["values"] = values
                except Exception:
                    pass
                self.model.set(model)
                try:
                    self._model_changed(None)
                except Exception:
                    pass
        except Exception:
            pass
'''

new = '''    def _apply_prefill(self, data):
        """Populate form fields from a record and jump to Step 2 (Product).

        Accepts either a history record or a customer record. Field names
        are mapped best-effort, so missing keys are simply skipped.
        """
        if not data:
            return

        def _set(var_name, value):
            try:
                v = (value or "").strip() if isinstance(value, str) else value
                if v and hasattr(self, var_name):
                    getattr(self, var_name).set(v)
            except Exception:
                pass

        # ---- customer block (try multiple key spellings) ----
        _set("customer_name", data.get("customer_name") or data.get("name"))
        _set("company",       data.get("customer_company") or data.get("company"))
        _set("phone",         data.get("customer_phone") or data.get("phone"))
        _set("email",         data.get("customer_email") or data.get("email"))
        _set("address",       data.get("customer_address") or data.get("address"))
        _set("city",          data.get("customer_city") or data.get("city"))
        _set("state",         data.get("customer_state") or data.get("state"))
        _set("pincode",       data.get("customer_pincode") or data.get("pincode"))
        _set("gstin",         data.get("customer_gstin") or data.get("gstin"))
        _set("contact_person",data.get("contact_person"))

        # ---- product block (only if a model is present) ----
        model = (data.get("model") or "").strip()
        if model:
            try:
                values = list(self.model_combo["values"])
                if model not in values:
                    values.append(model)
                    self.model_combo["values"] = values
            except Exception:
                pass
            try:
                self.model.set(model)
                self._model_changed(None)
            except Exception:
                pass

        # ---- jump to Product page (Step 2) ----
        try:
            self._load_step(2)
        except Exception:
            pass
'''

if old in s:
    s = s.replace(old, new, 1)
    print("[ok] _apply_prefill upgraded + jumps to Step 2")
else:
    print("[WARN] _apply_prefill old version not found")

FORM.write_text(s, encoding="utf-8")

print()
try:
    py_compile.compile(str(FORM), doraise=True)
    print("[check] FORM OK")
except py_compile.PyCompileError as e:
    print("[check] FAIL:", e)
    shutil.copy2(FORM.with_suffix(".py.PREFILL2_BACKUP"), FORM)
    print("[restore] reverted")
