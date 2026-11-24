"""Re-upload every locally saved Crystal quotation to the Google Sheet.

Quotations saved before the Totals column existed only reached the sheet as
summary rows, so other PCs could not show their discounts, packing or
transportation. Run this on the PC that created them (after redeploying
tools/apps_script_cloud_sync.gs) to backfill items and totals:

    python tools/resend_local_quotations.py
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.google_sheet_service import send_to_sheet
from app.services.quotation_history_service import local_quotations


def main():
    records = local_quotations()
    if not records:
        print("No local Crystal quotations found on this PC.")
        return

    print(f"Re-sending {len(records)} quotation(s) to the Google Sheet...")
    sent = failed = 0
    for rec in records:
        number = rec.get("quotation_number", "")
        payload = {
            "action": "quotation",
            "date": rec.get("date", ""),
            "user": os.environ.get("USERNAME") or "user",
            "quotation_number": number,
            "customer_name": rec.get("customer_name", ""),
            "customer_company": rec.get("customer_company", ""),
            "customer_phone": rec.get("customer_phone", ""),
            "customer_email": rec.get("customer_email", ""),
            "customer_address": rec.get("customer_address", ""),
            "customer_city": rec.get("customer_city", ""),
            "customer_state": rec.get("customer_state", ""),
            "customer_pincode": rec.get("customer_pincode", ""),
            "customer_gstin": rec.get("customer_gstin", ""),
            "model": rec.get("model", ""),
            "grand_total": rec.get("grand_total", ""),
            "status": rec.get("status", "Draft"),
            "items": rec.get("items") or [],
            "totals": rec.get("totals") or {},
        }
        if send_to_sheet(payload):
            sent += 1
        else:
            failed += 1
        time.sleep(0.3)

    print(f"Done: {sent} sent, {failed} failed.")


if __name__ == "__main__":
    main()
