"""Lead tracking service."""
import json, pathlib, datetime
from app.services.paths import get_data_dir

def _leads_file():
    return get_data_dir() / "leads.json"

def load_leads():
    """Load leads from local JSON cache. Only sync from sheet if local is empty."""
    p = _leads_file()
    
    # 1. Try to read from local JSON first
    if p.exists():
        try:
            local_leads = json.loads(p.read_text(encoding="utf-8")).get("leads", [])
            if local_leads:
                return local_leads
        except Exception:
            pass
    
    # 2. If local is empty, fetch from Google Sheet and save locally
    try:
        from app.services.google_sheet_service import fetch_leads_from_sheet
        sheet_leads = fetch_leads_from_sheet()
        if sheet_leads:
            # Save the fetched leads to local JSON so we have a copy
            save_leads(sheet_leads)
            return sheet_leads
    except Exception as e:
        print(f"[lead-sync] Could not fetch from sheet: {e}")
    
    return []

def save_leads(leads):
    p = _leads_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"leads": leads}, indent=2, ensure_ascii=False), encoding="utf-8")

def add_lead(customer, company, phone, email, qty, source, notes):
    leads = load_leads()
    new_lead = {
        "id": f"L{int(datetime.datetime.now().timestamp())}",
        "date": datetime.date.today().isoformat(),
        "customer": customer,
        "company": company,
        "phone": phone,
        "email": email,
        "qty": qty,
        "source": source,
        "notes": notes,
        "status": "Pending"
    }
    leads.append(new_lead)
    save_leads(leads)
    
    # Sync to Google Sheet
    try:
        from app.services.google_sheet_service import send_to_sheet
        send_to_sheet({"action": "lead", **new_lead})
    except Exception as e:
        print(f"[lead-sync] failed: {e}")
    
    return new_lead

def mark_lead_sent(lead_id):
    leads = load_leads()
    for lead in leads:
        if (lead.get("leadid") or lead.get("id")) == lead_id:
            lead["status"] = "Sent"
            save_leads(leads)
            try:
                from app.services.google_sheet_service import send_to_sheet
                send_to_sheet({"action": "lead_update", "id": lead_id, "status": "Sent"})
            except Exception: pass
            return True
    return False

def delete_lead(lead_id):
    leads = load_leads()
    new_leads = [l for l in leads if (l.get("leadid") or l.get("id")) != lead_id]
    if len(leads) == len(new_leads):
        return False
    save_leads(new_leads)
    return True


def restore_leads_from_sheet():
    """Forcefully fetch leads from Google Sheet and overwrite local JSON."""
    try:
        from app.services.google_sheet_service import fetch_leads_from_sheet
        sheet_leads = fetch_leads_from_sheet()
        if sheet_leads is not None:
            save_leads(sheet_leads)
            return True
    except Exception as e:
        print(f"[restore_leads] Error: {e}")
    return False
