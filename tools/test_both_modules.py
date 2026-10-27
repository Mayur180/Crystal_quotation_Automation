"""
Cross-module test — verifies both VMM and Crystal work.

Runs read-only checks. Does not touch data files, does not launch GUI.

Usage:
    python tools/test_both_modules.py

Exit code:
    0  → all tests passed
    1  → at least one test failed
"""
import os
import sys
import json
import traceback
from pathlib import Path

# ─── Project root on path ───
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ═══════════════════════════════════════════════════════════════
# TEST FRAMEWORK (lightweight)
# ═══════════════════════════════════════════════════════════════

class Result:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []

    def ok(self, label, detail=""):
        self.passed += 1
        print(f"  ✓ {label}" + (f"  ({detail})" if detail else ""))

    def fail(self, label, err):
        self.failed += 1
        self.failures.append((label, err))
        print(f"  ✗ {label}")
        print(f"      {err}")

    def assert_eq(self, label, actual, expected):
        if actual == expected:
            self.ok(label, f"{actual!r}")
        else:
            self.fail(label, f"expected {expected!r}, got {actual!r}")

    def assert_truthy(self, label, value):
        if value:
            self.ok(label)
        else:
            self.fail(label, f"value is falsy: {value!r}")

    def assert_file(self, label, path: Path):
        if path.is_file():
            self.ok(label, f"{path.name} ({path.stat().st_size:,} bytes)")
        else:
            self.fail(label, f"missing file: {path}")


R = Result()


# ═══════════════════════════════════════════════════════════════
# PER-MODULE CHECK
# ═══════════════════════════════════════════════════════════════

EXPECTED = {
    "VMM": {
        "min_products": 1,           # at least one product
        "prefix":       "AA/VMM",
        "data_dir":     "VMM",
    },
    "Crystal": {
        "min_products": 3000,        # expect ~3,323
        "prefix":       "CRY",
        "data_dir":     "Crystal",
    },
}


def test_module(name: str):
    print()
    print("═" * 60)
    print(f"  MODULE: {name}")
    print("═" * 60)

    expected = EXPECTED[name]

    # ─── 1. Switch module ───
    try:
        from app.services import paths
        paths.set_active_module(name)
        R.assert_eq(f"[{name}] active module", paths.get_active_module(), name)
    except Exception as e:
        R.fail(f"[{name}] set_active_module", e)
        return

    # ─── 2. Data directory resolves ───
    try:
        from app.services.paths import get_data_dir
        d = get_data_dir()
        expected_dir = str(d).endswith(expected["data_dir"])
        R.assert_eq(f"[{name}] data dir name", d.name, expected["data_dir"])
        R.assert_truthy(f"[{name}] data dir exists", d.is_dir())
    except Exception as e:
        R.fail(f"[{name}] get_data_dir", e)
        return

    # ─── 3. Required data files ───
    for fname in (
        "catalog.json",
        "company_settings.json",
        "custom_terms.json",
        "customers.json",
        "quotations.json",
        "quotation_counter.json",
    ):
        R.assert_file(f"[{name}] data/{fname}", d / fname)

    # ─── 4. Catalog loads via service ───
    try:
        from app.services.catalog_service import (
            get_catalog_summary,
            get_products,
            get_product_categories,
            get_product,
        )
        summary = get_catalog_summary() or {}
        count = summary.get("product_count", 0)
        R.assert_truthy(
            f"[{name}] catalog loads",
            count >= expected["min_products"],
        )
        R.ok(f"[{name}] product count", f"{count}")
        cats = summary.get("categories", [])
        R.assert_truthy(f"[{name}] categories present", len(cats) >= 1)
    except Exception as e:
        R.fail(f"[{name}] catalog service", e)

    # ─── 5. First product is retrievable ───
    try:
        products = get_products()
        if products:
            model = products[0].get("model")
            found = get_product(model)
            R.assert_truthy(f"[{name}] get_product({model!r})", found is not None)
        else:
            R.fail(f"[{name}] get_products", "empty catalog")
    except Exception as e:
        R.fail(f"[{name}] get_product", e)

    # ─── 6. Quotation number prefix ───
    try:
        from app.services.quotation_number_service import (
            _get_quotation_prefix,
        )
        prefix = _get_quotation_prefix()
        R.assert_eq(f"[{name}] quotation prefix", prefix, expected["prefix"])
    except Exception as e:
        R.fail(f"[{name}] quotation prefix", e)

    # ─── 7. Generator imports cleanly ───
    try:
        if name == "Crystal":
            import quotation_generator_crystal as gen
            R.assert_truthy(
                f"[{name}] generator imports",
                hasattr(gen, "generate_quotation"),
            )
            R.assert_truthy(
                f"[{name}] _crystal_page exists",
                hasattr(gen, "_crystal_page"),
            )
        else:
            import quotation_generator as gen
            R.assert_truthy(
                f"[{name}] generator imports",
                hasattr(gen, "generate_quotation"),
            )
    except Exception as e:
        R.fail(f"[{name}] generator import", e)

    # ─── 8. Custom terms JSON parses ───
    try:
        terms_path = d / "custom_terms.json"
        terms_data = json.loads(terms_path.read_text(encoding="utf-8"))
        if isinstance(terms_data, dict) and "terms" in terms_data:
            terms = list(terms_data["terms"].keys())
        elif isinstance(terms_data, list):
            terms = [t.get("title", "?") for t in terms_data if isinstance(t, dict)]
        else:
            terms = []
        R.ok(f"[{name}] terms loaded", f"{len(terms)} terms")
    except Exception as e:
        R.fail(f"[{name}] terms JSON", e)


# ═══════════════════════════════════════════════════════════════
# MODULE-SWITCH ISOLATION
# ═══════════════════════════════════════════════════════════════

def test_isolation():
    print()
    print("═" * 60)
    print("  MODULE ISOLATION")
    print("═" * 60)

    try:
        from app.services import paths
        from app.services.catalog_service import get_catalog_summary

        paths.set_active_module("VMM")
        vmm_count = get_catalog_summary()["product_count"]

        paths.set_active_module("Crystal")
        crystal_count = get_catalog_summary()["product_count"]

        R.assert_truthy(
            "switch VMM → Crystal changes data",
            vmm_count != crystal_count,
        )
        R.ok("VMM products", f"{vmm_count}")
        R.ok("Crystal products", f"{crystal_count}")

        # Reset to VMM
        paths.set_active_module("VMM")
    except Exception as e:
        R.fail("isolation test", e)


# ═══════════════════════════════════════════════════════════════
# VMM FILE FROZEN CHECK
# ═══════════════════════════════════════════════════════════════

def test_vmm_frozen():
    print()
    print("═" * 60)
    print("  VMM FROZEN CHECK")
    print("═" * 60)

    try:
        import subprocess
        out = subprocess.run(
            ["git", "status", "--short", "ui/vmm/", "quotation_generator.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        changes = out.stdout.strip()
        if not changes:
            R.ok("VMM files unmodified")
        else:
            R.fail("VMM files modified", changes)
    except Exception as e:
        R.fail("git status", e)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("╔" + "═" * 58 + "╗")
    print("║" + "  CRYSTAL / ARMATECH — CROSS-MODULE TEST".center(58) + "║")
    print("╚" + "═" * 58 + "╝")

    for module in ("VMM", "Crystal"):
        try:
            test_module(module)
        except Exception:
            print(f"  ✗ [{module}] unexpected error:")
            traceback.print_exc()
            R.failed += 1

    test_isolation()
    test_vmm_frozen()

    # ─── Summary ───
    print()
    print("═" * 60)
    print("  SUMMARY")
    print("═" * 60)
    print(f"  Passed: {R.passed}")
    print(f"  Failed: {R.failed}")

    if R.failures:
        print()
        print("  Failures:")
        for label, err in R.failures:
            print(f"    ✗ {label}")
            print(f"        {err}")

    print()
    if R.failed == 0:
        print("  ✓ ALL TESTS PASSED")
        return 0
    else:
        print("  ✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
