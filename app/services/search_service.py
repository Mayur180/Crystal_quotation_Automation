"""
Global search service — searches across customers, quotations, and leads.
"""
import json
from pathlib import Path
from app.services.paths import get_data_dir


def _read_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def search_customers(query, data_dir=None):
    """Search customers by name, company, phone, or email."""
    base = data_dir or get_data_dir()
    crystal = base.parent / "Crystal" if not data_dir else data_dir
    if not crystal.exists():
        crystal = base
    
    data = _read_json(crystal / "customers.json") or {}
    customers = data.get("customers", []) if isinstance(data, dict) else data
    if not isinstance(customers, list):
        return []
    
    q = query.lower().strip()
    results = []
    for c in customers:
        searchable = " ".join([
            str(c.get("name", "")),
            str(c.get("company", "")),
            str(c.get("phone", "")),
            str(c.get("email", "")),
        ]).lower()
        if q in searchable:
            results.append({
                "type": "Customer",
                "title": c.get("name", "—"),
                "subtitle": c.get("company", "") or c.get("phone", ""),
                "raw": c,
            })
    return results


def search_quotations(query, data_dir=None):
    """Search quotations by number, customer, or model."""
    base = data_dir or get_data_dir()
    crystal = base.parent / "Crystal" if not data_dir else data_dir
    if not crystal.exists():
        crystal = base
    
    data = _read_json(crystal / "quotations.json")
    if isinstance(data, list):
        quotations = data
    elif isinstance(data, dict):
        quotations = data.get("quotations", [])
    else:
        return []
    
    q = query.lower().strip()
    results = []
    for qt in quotations:
        searchable = " ".join([
            str(qt.get("quotation_number", "")),
            str(qt.get("customer_name", "")),
            str(qt.get("company", "")),
            str(qt.get("model", "")),
        ]).lower()
        if q in searchable:
            results.append({
                "type": "Quotation",
                "title": qt.get("quotation_number", "—"),
                "subtitle": f"{qt.get('customer_name', '—')} | ₹{qt.get('grand_total', 0)}",
                "raw": qt,
            })
    return results


def search_leads(query):
    """Search leads by customer, company, phone, or notes."""
    from app.services.lead_service import load_leads
    try:
        leads = load_leads() or []
    except Exception:
        leads = []
    
    q = query.lower().strip()
    results = []
    for lead in leads:
        searchable = " ".join([
            str(lead.get("customer", "")),
            str(lead.get("company", "")),
            str(lead.get("phone", "")),
            str(lead.get("email", "")),
            str(lead.get("notes", "")),
        ]).lower()
        if q in searchable:
            results.append({
                "type": "Lead",
                "title": lead.get("customer", "—"),
                "subtitle": f"{lead.get('company', '')} | {lead.get('status', '')}",
                "raw": lead,
            })
    return results


def global_search(query):
    """Search across all entities and return combined results."""
    if not query or len(query.strip()) < 2:
        return []
    
    results = []
    results.extend(search_customers(query))
    results.extend(search_quotations(query))
    results.extend(search_leads(query))
    return results
