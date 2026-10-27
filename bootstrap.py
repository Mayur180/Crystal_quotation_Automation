"""
Bootstrap the app on a fresh PC.
Downloads catalog and users from Google Sheets if local data is missing.
Creates required folders.
"""
import os
import json
import requests
from pathlib import Path

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzhtawFNa_Wlo644joUFEJvRJV9LiiMXu7En_sOzWH2fK6rvVG_XEIqiTE6OgNMnyQ/exec"

def ensure_folders():
    """Create all required folders."""
    paths = [
        "data/Crystal",
        "data/VMM",
        "data/Crystal/backups",
        "output",
        "assets",
    ]
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)
    print("✅ Folders verified.")

def download_catalog():
    """Download catalog from Google Sheets if local file is missing."""
    catalog_file = Path("data/Crystal/catalog.json")
    if catalog_file.exists() and catalog_file.stat().st_size > 100:
        print(f"✅ Catalog already exists ({catalog_file.stat().st_size} bytes).")
        return True
    
    print("⬇️  Downloading catalog from Google Sheets...")
    try:
        response = requests.get(f"{WEBHOOK_URL}?action=get_catalog", timeout=15)
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            if products:
                catalog_file.write_text(json.dumps({"products": products}, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"✅ Downloaded {len(products)} products.")
                return True
            else:
                print("⚠️  No products found in Google Sheet. Using empty catalog.")
                catalog_file.write_text(json.dumps({"products": []}, indent=2), encoding="utf-8")
                return True
    except Exception as e:
        print(f"❌ Could not download catalog: {e}")
        catalog_file.write_text(json.dumps({"products": []}, indent=2), encoding="utf-8")
        return False

def download_users():
    """Download users from Google Sheets if local file is missing."""
    users_file = Path("data/Users.json")
    if users_file.exists() and users_file.stat().st_size > 10:
        print("✅ Users file already exists.")
        return True
    
    print("⬇️  Downloading users from Google Sheets...")
    try:
        from app.services.user_service import fetch_users_from_sheet
        result = fetch_users_from_sheet()
        if result:
            print("✅ Users downloaded.")
            return True
    except Exception as e:
        print(f"⚠️  Could not download users: {e}")
    return False

def bootstrap():
    """Run all bootstrap steps."""
    print("=" * 60)
    print("CRYSTAL Quotation Manager — Bootstrap")
    print("=" * 60)
    ensure_folders()
    download_catalog()
    download_users()
    print("=" * 60)
    print("✅ Bootstrap complete.")
    print("=" * 60)

if __name__ == "__main__":
    bootstrap()
