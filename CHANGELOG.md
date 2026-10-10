# CRYSTAL Quotation Manager — Changelog

All notable changes to this project are documented here.

---

## [3.0] — 10 October 2026

### ✨ Major new features

#### Quotation workflow
- Full customer data captured in every quotation (name, company, phone, email, address, city, state, PIN, GSTIN, contact person)
- **BuyBack Offer** field — subtracted from taxable value automatically
- **Optional Accessories note** on Commercial Quotation page
- **Adaptive page sizing** — long-description models now fit on one page
- **A4 page size** (was US Letter by mistake)
- **Auto-update catalog price** when saving a quotation with the checkbox enabled
- **Auto-save new customers** to the customer DB from quotations
- **Duplicate quotation** (Ctrl+D or right-click)
- **Quote from previous** — opens pre-filled form from Customers window

#### Quotation History
- **Search + date range + status filter**
- **Row coloring by status** (Draft / Sent / Accepted / Rejected / Expired)
- **Set Status** dialog (button, right-click, or `S` key)
- **Send WhatsApp** with pre-filled message (button, right-click, or `W` key)
- **Send Email** via Gmail compose (button, right-click, or `E` key)
- **Create PDF on demand** — prompts if PDF is missing
- **Export monthly report to CSV / PDF**

#### Activity Log
- User-tagged entries
- Search + event-type filter
- Clear Log with confirmation

#### Monthly Report
- Summary card for a selected month
- Top customers + Top models
- 12-month breakdown table
- Export to **CSV**
- Export to **PDF** (A4)

#### Google Sheets integration ⭐
- Automatic row added to Google Sheet on every new quotation
- Separate **Customers** sheet with deduplication
- Full customer data sent (phone, email, address, city, state, PIN, GSTIN)
- Silent failure — never blocks quotation save if Sheets unreachable
- Sends via Apps Script webhook (no API keys needed)

#### Catalog
- All **16 models** updated with correct specs:
  - **Manual VMM**: AA-9011M, AA-9012M, AA-9013M
  - **Semi-Automatic VMM**: AA-9021SA, AA-9022SA, AA-9023SA
  - **Fully Automatic VMM**: AA-9031A, AA-9032A, AA-9033A
  - **Automatic VMM with Cabinet**: AA-9041AC, AA-9042AC, AA-9043AC, AA-9044AC
  - **VMS**: AA-9051V, AA-9052V, AA-9053V
- Correct dimension, weight, FOV, resolution, accuracy, repeatability
- Removed "CNC" wording per manager's request

#### Company Settings
- **NEW: Output Folder** field
  - Browse button to pick folder
  - Files saved under `<folder>/DD-MM-YYYY/word/` and `<folder>/DD-MM-YYYY/pdf/`
  - Persists in `%APPDATA%/CrystalQuotation/settings.json`

#### Terms & Conditions
- 11 standard terms updated to match manager's approved template
- Editable via Terms Editor
- Updated payment, packing, delivery wording

### 🔧 Architecture changes
- **Removed multi-user login wizard** — was causing Tk root conflicts on other PCs
- **Single Tk root** — fixes app not opening on some PCs
- Removed shared folder requirement
- Cleaner path resolution:
  - `data/` — for JSON data files
  - `%APPDATA%/CrystalQuotation/` — for settings
  - User-chosen folder — for generated DOCX/PDF

### 🐛 Bug fixes
- F-string escaping issues in status dialog
- Adaptive page 1 layout for VMS models
- A4 page size (was Letter)
- Optional-field asterisks — only Company and Model are required
- Frozen EXE no longer hangs on unreachable network paths
- Customer save returns `(record, created_bool)` tuple correctly
- Output folder field now populates from settings on load

### ❌ Removed
- Multi-user login wizard
- `setup.json` dependency
- Shared folder path logic
- Team Activity window
- Reconfigure Setup item
- Admin role checks
- CNC wording across catalog

### 🧪 Testing
- **Full audit** (`full_audit.py`) — 70+ checks
- **End-to-end test** (`test_end_to_end.py`) — 36 checks
- Google Sheet webhook tested end-to-end

### 📦 Packaging
- **PyInstaller windowed EXE** (no console window)
- Folder mode (no temp extraction)
- Bundled Tcl/Tk (1248 files)
- Total size: ~61 MB
- Auto-run on double-click

---

## [Pre-3.0]
- Initial dashboard with sidebar
- Quotation generation with DOCX / PDF
- Customer database
- Product catalog
- Basic search

---

*Maintained by Mayuresh Karnavat / ArmaTech Associates*
