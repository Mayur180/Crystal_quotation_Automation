/**
 * ARMATECH ASSOCIATES – CRYSTAL / VMM CLOUD SYNC
 * Google Apps Script Web App
 *
 * Sheets used:
 *   Quotations, QuotationItems, Customers, Users, Leads, Logins, Catalog
 *
 * Script Properties (Project Settings > Script Properties):
 *   ADMIN_EMAIL          Optional; defaults to mayuresh1803@gmail.com
 *   BACKUP_FOLDER_NAME   Optional; defaults to CRYSTAL_Backup
 *   DRIVE_LINK_SHARING   Optional; set to ANYONE only if public-link access is intended.
 *   API_SECRET           Optional; if set, clients must send api_key in POST JSON
 *                        or ?api_key=... in GET requests. Do not set it until the
 *                        desktop application is updated to send the same secret.
 *
 * IMPORTANT:
 *   - Rows are only removed when the app explicitly sends action=delete_quotation.
 *   - Existing sheet headers are checked. A mismatch raises an error instead of
 *     silently replacing the first row and potentially corrupting the sheet.
 *   - Drive files are private by default. Set DRIVE_LINK_SHARING=ANYONE only
 *     after considering the privacy implications of quotation documents.
 */

// -----------------------------------------------------------------------------
// CONFIGURATION
// -----------------------------------------------------------------------------

var QUOTATIONS_HEADERS = [
  "Date", "User", "Quotation No", "Customer", "Company", "Phone", "Email",
  "Address", "City", "State", "Pincode", "GSTIN", "Model", "Grand Total",
  "Status", "PDF Link", "Word Link", "Updated", "Totals", "Type"
];

// Line items live in their own sheet so every PC can see the materials
// inside a quotation without changing the Quotations column layout.
var QUOTATION_ITEMS_HEADERS = [
  "Quotation No", "Model", "HSN", "Qty", "Price", "Discount", "Total",
  "Updated", "Disc Mode", "Raw Discount"
];

var CUSTOMERS_HEADERS = [
  "Created", "User", "Name", "Company", "Phone", "Email",
  "Address", "City", "State", "Pincode", "GSTIN", "Updated"
];

var USERS_HEADERS = [
  "Timestamp", "User ID", "Username", "Full Name", "Role",
  "Active", "Modules", "Created At", "Created By"
];

var LEADS_HEADERS = [
  "Date", "Customer", "Company", "Phone", "Email", "Quantity",
  "Source", "Notes", "Status", "LastReminder", "LeadID"
];

var LOGINS_HEADERS = [
  "Timestamp", "User ID", "Username", "Full Name", "PC Name"
];

var CATALOG_HEADERS = [
  "Model", "Name", "Description", "Price", "Category", "HSN", "Unit", "Tax"
];

var DEFAULT_BACKUP_FOLDER_NAME = "CRYSTAL_Backup";
var DEFAULT_ADMIN_EMAIL = "mayuresh1803@gmail.com";


// -----------------------------------------------------------------------------
// COMMON HELPERS
// -----------------------------------------------------------------------------

function getScriptProperty_(name, fallback) {
  var value = PropertiesService.getScriptProperties().getProperty(name);
  return value === null || value === "" ? fallback : value;
}

function getSpreadsheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    throw new Error(
      "No active spreadsheet. Open this script from the target Google Sheet, " +
      "or replace getActiveSpreadsheet() with openById() and configure its ID."
    );
  }
  return ss;
}

function ensureSheet(name, headers) {
  var ss = getSpreadsheet_();
  var sheet = ss.getSheetByName(name);

  if (!sheet) {
    sheet = ss.insertSheet(name);
  }

  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold");
    sheet.setFrozenRows(1);
    return sheet;
  }

  var width = Math.max(sheet.getLastColumn(), 1);
  var currentHeaders = sheet.getRange(1, 1, 1, width).getValues()[0];

  // Existing columns must match in place; blank trailing cells are filled
  // with new headers (e.g. "Totals") so old sheets migrate instead of failing.
  var blanks = [];
  for (var i = 0; i < headers.length; i++) {
    var current = String(currentHeaders[i] || "").trim();
    if (current === headers[i]) continue;
    if (current === "") {
      blanks.push(i);
      continue;
    }
    throw new Error(
      'Header mismatch in sheet "' + name + '" at column ' + (i + 1) +
      '. Expected "' + headers[i] + '" but found "' +
      current +
      '". No existing data was changed. Correct the header manually or run a migration.'
    );
  }

  for (var b = 0; b < blanks.length; b++) {
    sheet.getRange(1, blanks[b] + 1).setValue(headers[blanks[b]]);
  }
  if (blanks.length) {
    sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold");
  }
  sheet.setFrozenRows(1);
  return sheet;
}

function respond(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function errorResponse_(err) {
  var message = err && err.message ? err.message : String(err);
  return respond({ status: "error", message: message });
}

function withScriptLock_(callback) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    return callback();
  } finally {
    lock.releaseLock();
  }
}

function cleanString_(value) {
  return value === null || value === undefined ? "" : String(value).trim();
}

// Accept both key styles ("customer" and "customer_name") so no client
// version can ever write a quotation row with blank contact columns.
function pick_(data, keys) {
  for (var i = 0; i < keys.length; i++) {
    var value = data[keys[i]];
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      return value;
    }
  }
  return "";
}

function dateForSheet_(value) {
  if (!value) return "";
  if (value instanceof Date && !isNaN(value.getTime())) return value;
  var parsed = new Date(value);
  return isNaN(parsed.getTime()) ? cleanString_(value) : parsed;
}

function dateForApi_(value) {
  if (value instanceof Date && !isNaN(value.getTime())) {
    return Utilities.formatDate(
      value,
      Session.getScriptTimeZone(),
      "yyyy-MM-dd"
    );
  }
  return value === null || value === undefined ? "" : value;
}

function rowToObject_(headers, row, normalizeHeaders) {
  var obj = {};
  for (var i = 0; i < headers.length; i++) {
    var key = normalizeHeaders
      ? String(headers[i]).toLowerCase().replace(/ /g, "_")
      : String(headers[i]);
    obj[key] = dateForApi_(row[i]);
  }
  return obj;
}

function checkApiSecret_(data, params) {
  var expected = PropertiesService.getScriptProperties().getProperty("API_SECRET");
  if (!expected) return true; // Backward compatible until the desktop client is updated.

  var supplied = "";
  if (data && data.api_key) supplied = String(data.api_key);
  if (!supplied && params && params.api_key) supplied = String(params.api_key);

  if (supplied !== expected) {
    throw new Error("Unauthorized request. API key is missing or invalid.");
  }
  return true;
}


// -----------------------------------------------------------------------------
// LOGIN
// -----------------------------------------------------------------------------

function handleLogin(data) {
  return withScriptLock_(function () {
    var sheet = ensureSheet("Logins", LOGINS_HEADERS);
    var rows = sheet.getDataRange().getValues();
    var now = new Date();
    var oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

    var userId = cleanString_(data.user_id);
    var pcName = cleanString_(data.pc_name);

    for (var i = rows.length - 1; i >= 1; i--) {
      var rowTime = rows[i][0] instanceof Date
        ? rows[i][0]
        : new Date(rows[i][0]);

      if (
        cleanString_(rows[i][1]) === userId &&
        cleanString_(rows[i][4]) === pcName &&
        !isNaN(rowTime.getTime()) &&
        rowTime > oneHourAgo
      ) {
        return respond({ status: "ok", note: "recent_login_skipped" });
      }
    }

    sheet.appendRow([
      dateForSheet_(data.timestamp) || now,
      userId,
      cleanString_(data.username),
      cleanString_(data.full_name),
      pcName
    ]);

    return respond({ status: "ok", sheet: "Logins" });
  });
}


// -----------------------------------------------------------------------------
// LEADS
// -----------------------------------------------------------------------------

function handleLead(data) {
  return withScriptLock_(function () {
    var sheet = ensureSheet("Leads", LEADS_HEADERS);
    var rows = sheet.getDataRange().getValues();

    if (data.action === "lead_update") {
      var leadId = cleanString_(data.id);
      for (var i = 1; i < rows.length; i++) {
        if (cleanString_(rows[i][10]) === leadId) {
          sheet.getRange(i + 1, 9).setValue("Sent");
          return respond({ status: "ok", note: "updated" });
        }
      }
      return respond({ status: "ok", note: "not_found" });
    }

    var customer = cleanString_(data.customer);
    var leadDate = cleanString_(data.date);

    for (var j = 1; j < rows.length; j++) {
      var existingDate = dateForApi_(rows[j][0]);
      if (
        cleanString_(rows[j][1]) === customer &&
        cleanString_(existingDate) === leadDate
      ) {
        return respond({ status: "ok", note: "duplicate" });
      }
    }

    sheet.appendRow([
      dateForSheet_(data.date) || new Date(),
      customer,
      cleanString_(data.company),
      cleanString_(data.phone),
      cleanString_(data.email),
      data.qty === undefined || data.qty === null ? "" : data.qty,
      cleanString_(data.source),
      cleanString_(data.notes),
      "Pending",
      "",
      cleanString_(data.id)
    ]);

    return respond({ status: "ok", note: "new_lead" });
  });
}

function handleGetLeads() {
  try {
    var sheet = ensureSheet("Leads", LEADS_HEADERS);
    var values = sheet.getDataRange().getValues();
    if (values.length <= 1) return respond({ status: "ok", leads: [] });

    var headers = values[0];
    var leads = [];
    for (var i = 1; i < values.length; i++) {
      if (values[i].every(function (cell) { return cell === ""; })) continue;
      leads.push(rowToObject_(headers, values[i], true));
    }
    return respond({ status: "ok", leads: leads, count: leads.length });
  } catch (err) {
    return errorResponse_(err);
  }
}


// -----------------------------------------------------------------------------
// USERS
// -----------------------------------------------------------------------------

function handleGetUsers() {
  try {
    var sheet = ensureSheet("Users", USERS_HEADERS);
    var values = sheet.getDataRange().getValues();
    if (values.length <= 1) return respond({ status: "ok", users: [] });

    var users = [];
    for (var i = 1; i < values.length; i++) {
      if (values[i].every(function (cell) { return cell === ""; })) continue;
      users.push(rowToObject_(values[0], values[i], true));
    }
    return respond({ status: "ok", users: users, count: users.length });
  } catch (err) {
    return errorResponse_(err);
  }
}

function handleUser(data) {
  return withScriptLock_(function () {
    var sheet = ensureSheet("Users", USERS_HEADERS);
    var existing = sheet.getDataRange().getValues();
    var userId = cleanString_(data.user_id);
    if (!userId) throw new Error("user_id is required for user create/update.");

    var rowIdx = -1;
    for (var i = 1; i < existing.length; i++) {
      if (cleanString_(existing[i][1]) === userId) {
        rowIdx = i + 1;
        break;
      }
    }

    var active = data.is_active;
    if (active === undefined || active === null) active = "";

    var row = [
      new Date(),
      userId,
      cleanString_(data.username),
      cleanString_(data.full_name),
      cleanString_(data.role),
      active,
      cleanString_(data.modules),
      dateForSheet_(data.created_at),
      cleanString_(data.created_by)
    ];

    if (rowIdx > 0) {
      sheet.getRange(rowIdx, 1, 1, USERS_HEADERS.length).setValues([row]);
      return respond({ status: "ok", note: "updated" });
    }

    sheet.appendRow(row);
    return respond({ status: "ok", note: "new" });
  });
}


// -----------------------------------------------------------------------------
// CATALOG
// -----------------------------------------------------------------------------

function handleGetCatalog() {
  try {
    var sheet = ensureSheet("Catalog", CATALOG_HEADERS);
    var values = sheet.getDataRange().getValues();
    if (values.length <= 1) return respond({ status: "ok", products: [] });

    var products = [];
    for (var i = 1; i < values.length; i++) {
      if (values[i].every(function (cell) { return cell === ""; })) continue;
      products.push(rowToObject_(values[0], values[i], true));
    }
    return respond({ status: "ok", products: products, count: products.length });
  } catch (err) {
    return errorResponse_(err);
  }
}

// Replace the shared product catalog. The desktop app sends the full
// catalog; the sheet keeps only the columns every PC needs for quotations.
function handleCatalogBulk(data) {
  return withScriptLock_(function () {
    var products = data.products;
    if (!products || !products.length) {
      throw new Error("No products supplied.");
    }
    if (products.length > 30000) {
      throw new Error("Too many products: " + products.length);
    }

    var sheet = ensureSheet("Catalog", CATALOG_HEADERS);
    var seen = {};
    var rows = [];
    for (var i = 0; i < products.length; i++) {
      var p = products[i] || {};
      var model = cleanString_(p.model);
      if (!model || seen[model]) continue;
      seen[model] = true;
      rows.push([
        model,
        cleanString_(pick_(p, ["name", "product_name"])),
        cleanString_(p.description),
        Number(p.price || p.rate || 0) || 0,
        cleanString_(p.category),
        cleanString_(p.hsn),
        cleanString_(p.unit),
        cleanString_(pick_(p, ["tax_percent", "tax"]))
      ]);
    }
    if (!rows.length) throw new Error("No valid products supplied.");

    var lastRow = sheet.getLastRow();
    if (lastRow > 1) {
      sheet.getRange(2, 1, lastRow - 1, CATALOG_HEADERS.length).clearContent();
    }
    sheet.getRange(2, 1, rows.length, CATALOG_HEADERS.length).setValues(rows);
    return respond({ status: "ok", count: rows.length });
  });
}


// -----------------------------------------------------------------------------
// QUOTATIONS
// -----------------------------------------------------------------------------

function handleQuotation(data) {
  return withScriptLock_(function () {
    var sheet = ensureSheet("Quotations", QUOTATIONS_HEADERS);
    var quotationNumber = cleanString_(data.quotation_number);
    if (!quotationNumber) {
      throw new Error("quotation_number is required.");
    }

    var pdfUrl = "";
    var docxUrl = "";
    var uploadError = "";

    // Upload files before writing the row. If upload fails, keep any old links.
    try {
      if (data.pdf_base64) {
        pdfUrl = _uploadToDrive(
          data.pdf_base64,
          data.pdf_filename || "quotation.pdf",
          "PDFs",
          "application/pdf"
        );
      }
      if (data.docx_base64) {
        docxUrl = _uploadToDrive(
          data.docx_base64,
          data.docx_filename || "quotation.docx",
          "Word",
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        );
      }
    } catch (err) {
      uploadError = err && err.message ? err.message : String(err);
    }

    var rows = sheet.getDataRange().getValues();
    var rowIdx = -1;
    var oldPdfCell = "";
    var oldWordCell = "";
    var oldTotalsCell = "";

    for (var i = 1; i < rows.length; i++) {
      if (cleanString_(rows[i][2]) === quotationNumber) {
        rowIdx = i + 1;
        oldPdfCell = rows[i][15] || "";
        oldWordCell = rows[i][16] || "";
        oldTotalsCell = rows[i][18] || "";
        break;
      }
    }

    var pdfCell = pdfUrl
      ? '=HYPERLINK("' + pdfUrl.replace(/"/g, '""') + '","View PDF")'
      : oldPdfCell;

    var docxCell = docxUrl
      ? '=HYPERLINK("' + docxUrl.replace(/"/g, '""') + '","View Word")'
      : oldWordCell;

    // Keep an existing breakdown when an old client omits it.
    var totalsCell = oldTotalsCell;
    if (data.totals !== undefined && data.totals !== null) {
      try {
        totalsCell = typeof data.totals === "string"
          ? data.totals
          : JSON.stringify(data.totals);
      } catch (totalsErr) {
        totalsCell = oldTotalsCell;
      }
    }

    // Document type: "quotation" unless the client says proforma.
    var docType = String(pick_(data, ["doc_type", "type"]) || "").toLowerCase()
      .indexOf("prof") >= 0
      ? "proforma"
      : "quotation";
    if (quotationNumber.toUpperCase().indexOf("PI/") === 0) docType = "proforma";

    var row = [
      dateForSheet_(data.date) || new Date(),
      cleanString_(data.user),
      quotationNumber,
      cleanString_(pick_(data, ["customer", "customer_name", "name"])),
      cleanString_(pick_(data, ["company", "customer_company", "company_name"])),
      cleanString_(pick_(data, ["phone", "customer_phone", "mobile"])),
      cleanString_(pick_(data, ["email", "customer_email"])),
      cleanString_(pick_(data, ["address", "customer_address"])),
      cleanString_(pick_(data, ["city", "customer_city"])),
      cleanString_(pick_(data, ["state", "customer_state"])),
      cleanString_(pick_(data, ["pincode", "customer_pincode"])),
      cleanString_(pick_(data, ["gstin", "customer_gstin"])),
      cleanString_(pick_(data, ["model"])),
      data.grand_total === undefined || data.grand_total === null
        ? ""
        : data.grand_total,
      cleanString_(pick_(data, ["status"])),
      pdfCell,
      docxCell,
      new Date(),
      totalsCell,
      docType
    ];

    // Only replace materials when the client actually sent them; old clients
    // that omit "items" must not wipe existing line items. A materials write
    // failure must not lose the quotation row itself.
    var itemsError = "";
    if (data.items !== undefined && data.items !== null) {
      try {
        _writeQuotationItems_(quotationNumber, data.items);
      } catch (itemsErr) {
        itemsError = itemsErr && itemsErr.message ? itemsErr.message : String(itemsErr);
      }
    }

    if (rowIdx > 0) {
      sheet.getRange(rowIdx, 1, 1, QUOTATIONS_HEADERS.length).setValues([row]);
      return respond({
        status: "ok",
        note: "updated",
        pdfUrl: pdfUrl || "",
        docxUrl: docxUrl || "",
        uploadError: uploadError,
        itemsError: itemsError
      });
    }

    sheet.appendRow(row);
    return respond({
      status: "ok",
      note: "new",
      pdfUrl: pdfUrl || "",
      docxUrl: docxUrl || "",
      uploadError: uploadError,
      itemsError: itemsError
    });
  });
}

function handleListQuotations(params) {
  try {
    var sheet = ensureSheet("Quotations", QUOTATIONS_HEADERS);
    var values = sheet.getDataRange().getValues();
    if (values.length <= 1) return respond({ status: "ok", rows: [] });

    var since = cleanString_(params.since);
    var user = cleanString_(params.user);
    var itemsByQuote = _loadQuotationItems_();
    var rowsOut = [];

    for (var i = 1; i < values.length; i++) {
      var row = values[i];
      if (row.every(function (cell) { return cell === ""; })) continue;

      var obj = rowToObject_(values[0], row, false);
      var rowDate = cleanString_(obj["Date"]);
      var rowUser = cleanString_(obj["User"]);

      if (since && rowDate && rowDate < since) continue;
      if (user && user !== "All" && rowUser !== user) continue;

      obj["Items"] = itemsByQuote[cleanString_(obj["Quotation No"])] || [];
      obj["Totals"] = _parseTotalsCell_(obj["Totals"]);
      rowsOut.push(obj);
    }

    return respond({ status: "ok", rows: rowsOut, count: rowsOut.length });
  } catch (err) {
    return errorResponse_(err);
  }
}

function _cellNumber_(value) {
  if (value === null || value === undefined || value === "") return "";
  var n = Number(String(value).replace(/[₹,]/g, "").trim());
  return isNaN(n) ? "" : n;
}

function _parseTotalsCell_(value) {
  var text = cleanString_(value);
  if (!text) return {};
  try {
    var parsed = JSON.parse(text);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (err) {
    return {};
  }
}

function _writeQuotationItems_(quotationNumber, items) {
  var sheet = ensureSheet("QuotationItems", QUOTATION_ITEMS_HEADERS);
  var values = sheet.getDataRange().getValues();

  for (var i = values.length - 1; i >= 1; i--) {
    if (cleanString_(values[i][0]) === quotationNumber) {
      sheet.deleteRow(i + 1);
    }
  }

  var list = Array.isArray(items) ? items : [];
  var now = new Date();
  var rows = [];

  for (var j = 0; j < list.length; j++) {
    var item = list[j] || {};
    var model = cleanString_(item.model);
    if (!model) continue;
    rows.push([
      quotationNumber,
      model,
      cleanString_(item.hsn),
      _cellNumber_(item.qty),
      _cellNumber_(item.price),
      _cellNumber_(item.discount),
      _cellNumber_(item.total),
      now,
      cleanString_(item.disc_mode),
      _cellNumber_(item.raw_discount)
    ]);
  }

  if (!rows.length) return 0;

  sheet
    .getRange(sheet.getLastRow() + 1, 1, rows.length, QUOTATION_ITEMS_HEADERS.length)
    .setValues(rows);
  return rows.length;
}

function _loadQuotationItems_() {
  var ss = getSpreadsheet_();
  var sheet = ss.getSheetByName("QuotationItems");
  var map = {};
  if (!sheet || sheet.getLastRow() < 2) return map;

  var values = sheet.getDataRange().getValues();
  for (var i = 1; i < values.length; i++) {
    var row = values[i];
    if (row.every(function (cell) { return cell === ""; })) continue;
    var qNo = cleanString_(row[0]);
    if (!qNo) continue;
    if (!map[qNo]) map[qNo] = [];
    map[qNo].push({
      model: cleanString_(row[1]),
      hsn: cleanString_(row[2]),
      qty: _cellNumber_(row[3]),
      price: _cellNumber_(row[4]),
      discount: _cellNumber_(row[5]),
      total: _cellNumber_(row[6]),
      disc_mode: cleanString_(row[8]),
      raw_discount: _cellNumber_(row[9])
    });
  }
  return map;
}

function handleDeleteQuotation(data) {
  return withScriptLock_(function () {
    var sheet = ensureSheet("Quotations", QUOTATIONS_HEADERS);
    var quotationNumber = cleanString_(data.quotation_number);
    if (!quotationNumber) {
      throw new Error("quotation_number is required.");
    }

    var values = sheet.getDataRange().getValues();
    var removed = 0;

    // Walk from the bottom so deleting a row does not shift later indices.
    for (var i = values.length - 1; i >= 1; i--) {
      if (cleanString_(values[i][2]) === quotationNumber) {
        sheet.deleteRow(i + 1);
        removed++;
      }
    }

    // Remove the quotation's material rows as well.
    var itemsSheet = getSpreadsheet_().getSheetByName("QuotationItems");
    if (itemsSheet && itemsSheet.getLastRow() > 1) {
      var itemValues = itemsSheet.getDataRange().getValues();
      for (var j = itemValues.length - 1; j >= 1; j--) {
        if (cleanString_(itemValues[j][0]) === quotationNumber) {
          itemsSheet.deleteRow(j + 1);
        }
      }
    }

    return respond({ status: "ok", deleted: removed });
  });
}

function handleUpdateStatus(data) {
  return withScriptLock_(function () {
    var sheet = ensureSheet("Quotations", QUOTATIONS_HEADERS);
    var quotationNumber = cleanString_(data.quotation_number);
    var newStatus = cleanString_(data.status);
    if (!quotationNumber) throw new Error("quotation_number is required.");
    if (!newStatus) throw new Error("status is required.");

    var values = sheet.getDataRange().getValues();
    if (values.length <= 1) {
      return respond({ status: "ok", updated: 0 });
    }

    var headers = values[0];
    var statusCol = headers.indexOf("Status");
    if (statusCol < 0) statusCol = 14;
    var updatedCol = headers.indexOf("Updated");

    var updated = 0;
    for (var i = 1; i < values.length; i++) {
      if (cleanString_(values[i][2]) === quotationNumber) {
        sheet.getRange(i + 1, statusCol + 1).setValue(newStatus);
        if (updatedCol >= 0) {
          sheet.getRange(i + 1, updatedCol + 1).setValue(new Date().toISOString());
        }
        updated++;
      }
    }

    return respond({ status: "ok", updated: updated });
  });
}


// -----------------------------------------------------------------------------
// CUSTOMERS
// -----------------------------------------------------------------------------

function handleCustomer(data) {
  return withScriptLock_(function () {
    var sheet = ensureSheet("Customers", CUSTOMERS_HEADERS);
    var existing = sheet.getDataRange().getValues();

    var name = cleanString_(data.name);
    var company = cleanString_(data.company);
    var phone = cleanString_(data.phone);
    var email = cleanString_(data.email);

    for (var i = 1; i < existing.length; i++) {
      var row = existing[i];
      var sameNameCompany =
        name &&
        cleanString_(row[2]).toLowerCase() === name.toLowerCase() &&
        cleanString_(row[3]).toLowerCase() === company.toLowerCase();
      var samePhone = phone && cleanString_(row[4]) === phone;
      var sameEmail = email &&
        cleanString_(row[5]).toLowerCase() === email.toLowerCase();

      if (sameNameCompany || samePhone || sameEmail) {
        sheet.getRange(i + 1, CUSTOMERS_HEADERS.length).setValue(new Date());
        return respond({ status: "ok", note: "existing" });
      }
    }

    if (!name && !phone && !email) {
      throw new Error("Customer name, phone, or email is required.");
    }

    sheet.appendRow([
      new Date(),
      cleanString_(data.user),
      name,
      company,
      phone,
      email,
      cleanString_(data.address),
      cleanString_(data.city),
      cleanString_(data.state),
      cleanString_(data.pincode),
      cleanString_(data.gstin),
      new Date()
    ]);

    return respond({ status: "ok", note: "new" });
  });
}


function handleCustomersBulk(data) {
  return withScriptLock_(function () {
    var sheet = ensureSheet("Customers", CUSTOMERS_HEADERS);
    var values = sheet.getDataRange().getValues();

    var iName = CUSTOMERS_HEADERS.indexOf("Name");
    var iCompany = CUSTOMERS_HEADERS.indexOf("Company");
    var iPhone = CUSTOMERS_HEADERS.indexOf("Phone");
    var iEmail = CUSTOMERS_HEADERS.indexOf("Email");
    var iAddress = CUSTOMERS_HEADERS.indexOf("Address");
    var iCity = CUSTOMERS_HEADERS.indexOf("City");
    var iState = CUSTOMERS_HEADERS.indexOf("State");
    var iPincode = CUSTOMERS_HEADERS.indexOf("Pincode");
    var iGstin = CUSTOMERS_HEADERS.indexOf("GSTIN");

    function phoneKey_(value) {
      var digits = cleanString_(value).replace(/\D/g, "");
      return digits.length >= 10 ? digits.slice(-10) : digits;
    }
    function pairKey_(name, company) {
      var n = cleanString_(name).toLowerCase().replace(/\s+/g, " ");
      var c = cleanString_(company).toLowerCase().replace(/\s+/g, " ");
      return n && c ? n + "|" + c : "";
    }

    var byPhone = {}, byEmail = {}, byPair = {};
    for (var i = 1; i < values.length; i++) {
      var row = values[i];
      var pk = phoneKey_(row[iPhone]);
      if (pk && !byPhone[pk]) byPhone[pk] = i + 1;
      var ek = cleanString_(row[iEmail]).toLowerCase();
      if (ek && !byEmail[ek]) byEmail[ek] = i + 1;
      var nk = pairKey_(row[iName], row[iCompany]);
      if (nk && !byPair[nk]) byPair[nk] = i + 1;
    }

    var incoming = (data.customers || []).slice(0, 500);
    var user = cleanString_(data.user) || "import";
    var added = 0, updated = 0, skipped = 0;
    var newRows = [];

    for (var j = 0; j < incoming.length; j++) {
      var item = incoming[j] || {};
      var name = cleanString_(item.name);
      var company = cleanString_(item.company);
      var phone = cleanString_(item.phone);
      var email = cleanString_(item.email);
      if (!name && !company && !phone && !email) { skipped++; continue; }

      var pk2 = phoneKey_(phone);
      var ek2 = email.toLowerCase();
      var nk2 = pairKey_(name, company);

      var rowIndex =
        (pk2 && byPhone[pk2]) ||
        (ek2 && byEmail[ek2]) ||
        (nk2 && byPair[nk2]) || 0;

      if (rowIndex) {
        var existing = values[rowIndex - 1];
        var blankFills = [
          [iName, name], [iCompany, company], [iPhone, phone], [iEmail, email],
          [iAddress, item.address], [iCity, item.city], [iState, item.state],
          [iPincode, item.pincode], [iGstin, item.gstin]
        ];
        var changed = false;
        for (var f = 0; f < blankFills.length; f++) {
          var colIdx = blankFills[f][0];
          var value = cleanString_(blankFills[f][1]);
          if (colIdx >= 0 && value && !cleanString_(existing[colIdx])) {
            sheet.getRange(rowIndex, colIdx + 1).setValue(value);
            existing[colIdx] = value;
            changed = true;
          }
        }
        if (changed) updated++; else skipped++;
        continue;
      }

      var now = new Date();
      var newRow = [];
      newRow[0] = now;
      newRow[1] = user;
      newRow[iName] = name;
      newRow[iCompany] = company;
      newRow[iPhone] = phone;
      newRow[iEmail] = email;
      newRow[iAddress] = cleanString_(item.address);
      newRow[iCity] = cleanString_(item.city);
      newRow[iState] = cleanString_(item.state);
      newRow[iPincode] = cleanString_(item.pincode);
      newRow[iGstin] = cleanString_(item.gstin);
      newRow[CUSTOMERS_HEADERS.indexOf("Updated")] = now;
      for (var k = 0; k < CUSTOMERS_HEADERS.length; k++) {
        if (newRow[k] === undefined) newRow[k] = "";
      }
      newRows.push(newRow);
      if (pk2) byPhone[pk2] = -1;
      if (ek2) byEmail[ek2] = -1;
      if (nk2) byPair[nk2] = -1;
      added++;
    }

    if (newRows.length) {
      sheet.getRange(sheet.getLastRow() + 1, 1, newRows.length, CUSTOMERS_HEADERS.length)
        .setValues(newRows);
      SpreadsheetApp.flush();
    }

    return respond({
      status: "ok",
      added: added,
      updated: updated,
      skipped: skipped,
      total: sheet.getLastRow() - 1
    });
  });
}


function handleGetCustomers() {
  try {
    var sheet = ensureSheet("Customers", CUSTOMERS_HEADERS);
    var values = sheet.getDataRange().getValues();
    if (values.length <= 1) return respond({ status: "ok", customers: [] });

    var customers = [];
    for (var i = 1; i < values.length; i++) {
      var row = values[i];
      if (row.every(function (cell) { return cell === ""; })) continue;

      var obj = rowToObject_(values[0], row, true);

      // Formula errors (#ERROR!, #N/A, ...) must not reach the desktop app.
      for (var key in obj) {
        if (typeof obj[key] === "string" && obj[key].charAt(0) === "#") {
          obj[key] = "";
        }
      }

      // Return the exact keys the desktop app expects.
      var customer = {
        id: "",
        name: obj.name || "",
        company: obj.company || "",
        phone: obj.phone || "",
        email: obj.email || "",
        address: obj.address || "",
        city: obj.city || "",
        state: obj.state || "",
        pincode: obj.pincode || "",
        gstin: obj.gstin || "",
        created_at: obj.created || "",
        updated_at: obj.updated || ""
      };

      if (customer.name || customer.company) {
        customers.push(customer);
      }
    }

    return respond({ status: "ok", customers: customers, count: customers.length });
  } catch (err) {
    return errorResponse_(err);
  }
}


// -----------------------------------------------------------------------------
// GOOGLE DRIVE HELPERS
// -----------------------------------------------------------------------------

function _uploadToDrive(base64Data, filename, subfolder, mimeType) {
  if (!base64Data) return "";

  var rawBase64 = String(base64Data).replace(/^data:[^,]*;base64,/, "");
  rawBase64 = rawBase64.replace(/\s/g, "");
  if (!rawBase64) throw new Error("The uploaded file data is empty.");

  var bytes;
  try {
    bytes = Utilities.base64Decode(rawBase64);
  } catch (err) {
    throw new Error("Invalid base64 data for " + filename + ".");
  }

  var safeFilename = String(filename || "upload")
    .replace(/[\\\/:*?"<>|]/g, "_")
    .substring(0, 180);

  var folder = _ensureFolder(subfolder);
  var blob = Utilities.newBlob(bytes, mimeType, safeFilename);
  var file = folder.createFile(blob);

  // Private by default. Public link sharing must be explicitly enabled.
  var sharing = getScriptProperty_("DRIVE_LINK_SHARING", "PRIVATE").toUpperCase();
  if (sharing === "ANYONE") {
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  }

  return "https://drive.google.com/file/d/" + file.getId() + "/view";
}

function _ensureFolder(subfolder) {
  var parentName = getScriptProperty_(
    "BACKUP_FOLDER_NAME",
    DEFAULT_BACKUP_FOLDER_NAME
  );

  var parentIterator = DriveApp.getFoldersByName(parentName);
  var parent = parentIterator.hasNext()
    ? parentIterator.next()
    : DriveApp.createFolder(parentName);

  var subIterator = parent.getFoldersByName(subfolder);
  return subIterator.hasNext()
    ? subIterator.next()
    : parent.createFolder(subfolder);
}


// -----------------------------------------------------------------------------
// WEB APP ENTRY POINTS
// -----------------------------------------------------------------------------

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      throw new Error("POST request body is missing.");
    }

    var data = JSON.parse(e.postData.contents);
    checkApiSecret_(data, null);

    var action = cleanString_(data.action) || "quotation";

    if (action === "customer") return handleCustomer(data);
    if (action === "customers_bulk") return handleCustomersBulk(data);
    if (action === "quotation") return handleQuotation(data);
    if (action === "delete_quotation") return handleDeleteQuotation(data);
    if (action === "update_status") return handleUpdateStatus(data);
    if (action === "user") return handleUser(data);
    if (action === "lead" || action === "lead_update") return handleLead(data);
    if (action === "catalog_bulk") return handleCatalogBulk(data);
    if (action === "login") return handleLogin(data);

    return respond({
      status: "error",
      message: "Unknown action: " + action
    });
  } catch (err) {
    return errorResponse_(err);
  }
}

function doGet(e) {
  try {
    var params = (e && e.parameter) || {};
    checkApiSecret_(null, params);

    var action = cleanString_(params.action);

    if (action === "list") return handleListQuotations(params);
    if (action === "get_leads") return handleGetLeads();
    if (action === "get_users") return handleGetUsers();
    if (action === "get_catalog") return handleGetCatalog();
    if (action === "get_customers") return handleGetCustomers();

    return respond({
      status: "ok",
      message: "ArmaTech Associates cloud sync is alive"
    });
  } catch (err) {
    return errorResponse_(err);
  }
}


// -----------------------------------------------------------------------------
// DAILY LEAD REMINDERS
// Create a time-driven trigger for sendDailyReminders() in Apps Script.
// -----------------------------------------------------------------------------

function sendDailyReminders() {
  var sheet = getSpreadsheet_().getSheetByName("Leads");
  if (!sheet || sheet.getLastRow() < 2) return;

  var rows = sheet.getDataRange().getValues();
  var today = new Date();
  var adminEmail = getScriptProperty_("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL);
  var reminderRows = [];
  var reminderMessages = [];

  for (var i = 1; i < rows.length; i++) {
    var row = rows[i];
    var leadDate = row[0] instanceof Date ? row[0] : new Date(row[0]);
    var status = cleanString_(row[8]);
    var lastReminder = row[9]
      ? (row[9] instanceof Date ? row[9] : new Date(row[9]))
      : null;

    if (isNaN(leadDate.getTime()) || status !== "Pending") continue;

    // Only remind for leads at least 3 days old; future-dated leads are ignored.
    var ageDays = Math.floor((today.getTime() - leadDate.getTime()) / 86400000);
    if (ageDays < 3) continue;

    var reminderDue = !lastReminder ||
      isNaN(lastReminder.getTime()) ||
      (today.getTime() - lastReminder.getTime()) >= 24 * 60 * 60 * 1000;

    if (reminderDue) {
      reminderMessages.push(
        "Customer: " + row[1] +
        " | Company: " + row[2] +
        " | Phone: " + row[3]
      );
      reminderRows.push(i + 1);
    }
  }

  if (reminderMessages.length === 0) return;

  var body =
    "Hello,\n\nPending leads for 3 or more days:\n\n" +
    reminderMessages.join("\n") +
    "\n\nPlease review the leads and update their status.\n\n" +
    "ArmaTech Associates – CRYSTAL / VMM";

  // Update reminder timestamps only after MailApp successfully sends.
  MailApp.sendEmail({
    to: adminEmail,
    subject: "Reminder: Pending Leads",
    body: body
  });

  var now = new Date();
  reminderRows.forEach(function (rowNumber) {
    sheet.getRange(rowNumber, 10).setValue(now);
  });
}


// -----------------------------------------------------------------------------
// OPTIONAL SETUP HELPERS
// -----------------------------------------------------------------------------

function setupSheets() {
  ensureSheet("Quotations", QUOTATIONS_HEADERS);
  ensureSheet("QuotationItems", QUOTATION_ITEMS_HEADERS);
  ensureSheet("Customers", CUSTOMERS_HEADERS);
  ensureSheet("Users", USERS_HEADERS);
  ensureSheet("Leads", LEADS_HEADERS);
  ensureSheet("Logins", LOGINS_HEADERS);
  ensureSheet("Catalog", CATALOG_HEADERS);
}

function createDailyReminderTrigger() {
  // Avoid creating duplicate triggers for the same handler.
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === "sendDailyReminders") {
      return;
    }
  }

  ScriptApp.newTrigger("sendDailyReminders")
    .timeBased()
    .everyDays(1)
    .atHour(9)
    .create();
}
