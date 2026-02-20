# MyData Integration - Quick API Reference

## Overview
This document provides quick reference for MyData (AADE) integration API endpoints.

## Endpoints

### 1. Transmit Invoice to MyData
**Transmit a single invoice to the Greek tax authority**

```
POST /payments/invoices/{invoice_id}/mydata/transmit/
```

**Authentication**: Required (login or JWT token)  
**Permissions**: Staff OR invoice guest  
**Parameters**: None

**Request:**
```bash
curl -X POST http://localhost:8000/payments/invoices/1/mydata/transmit/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Invoice transmitted to MyData. Transmission ID: AADE-20260220-123456"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Guest email is required for MyData transmission"
}
```

---

### 2. Get MyData Transmission Status
**Check transmission status of an invoice**

```
GET /payments/invoices/{invoice_id}/mydata/status/
```

**Authentication**: Required  
**Permissions**: Staff OR invoice guest  
**Parameters**: None

**Request:**
```bash
curl -X GET http://localhost:8000/payments/invoices/1/mydata/status/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "invoice_number": "INV-20260220-ABC12345",
  "mydata_transmitted": true,
  "transmission_id": "AADE-20260220-123456",
  "transmission_date": "2026-02-20T14:30:00Z",
  "qr_code": "A|123456789|INV-20260220-ABC12345|20260220|23800|5700"
}
```

---

### 3. Export Invoice to MyData Format
**Get invoice in MyData-compatible JSON format**

```
GET /payments/invoices/{invoice_id}/mydata/export/
```

**Authentication**: Required  
**Permissions**: Staff OR invoice guest  
**Parameters**: None

**Request:**
```bash
curl -X GET http://localhost:8000/payments/invoices/1/mydata/export/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "invoice": {
    "mark": "AADE-20260220-123456",
    "invoiceNumber": "INV-20260220-ABC12345",
    "issueDate": "2026-02-20",
    "dueDate": "2026-03-22",
    "currency": "EUR",
    "issuer": {
      "taxId": "123456789"
    },
    "counterpart": {
      "name": "John Guest",
      "email": "john@example.com"
    },
    "lines": [
      {
        "lineNumber": 1,
        "description": "Hotel accommodation",
        "quantity": 1,
        "unitPrice": 150.00,
        "discountPercentage": 0,
        "discount": 0,
        "netAmount": 150.00,
        "vatCategory": "1",
        "vatAmount": 36.00,
        "grossAmount": 186.00
      }
    ],
    "totals": {
      "netAmount": 150.00,
      "vatAmount": 36.00,
      "grossAmount": 186.00,
      "itemsNumber": 1,
      "linesNumber": 1
    },
    "paymentMethods": [
      {
        "type": "1",
        "amount": 186.00
      }
    ],
    "status": "issued",
    "myDataStatus": "TRANSMITTED"
  }
}
```

---

### 4. Bulk Transmit Invoices
**Transmit all pending invoices to MyData at once**

```
GET /payments/invoices/mydata/bulk-transmit/
```

**Authentication**: Required  
**Permissions**: Staff/Admin only  
**Parameters**: 
- `format=json` (optional) - Return JSON instead of redirect

**Request:**
```bash
# With redirect (default)
curl -X GET http://localhost:8000/payments/invoices/mydata/bulk-transmit/ \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Get JSON response
curl -X GET "http://localhost:8000/payments/invoices/mydata/bulk-transmit/?format=json" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response (JSON format):**
```json
{
  "total": 15,
  "successful": 13,
  "failed": 2,
  "transmitted_ids": [
    {
      "invoice_number": "INV-20260220-ABC12345",
      "transmission_id": "AADE-20260220-123456"
    },
    {
      "invoice_number": "INV-20260220-DEF67890",
      "transmission_id": "AADE-20260220-123457"
    }
  ],
  "errors": [
    {
      "invoice_number": "INV-20260219-XYZ99999",
      "errors": ["Guest email is required"]
    },
    {
      "invoice_number": "INV-20260218-OLD12345",
      "error": "Invoice amount is invalid"
    }
  ]
}
```

---

## Common Use Cases

### Create and Transmit Invoice

```bash
# 1. Create invoice via web form or API
POST /portal/invoices/create/
  guest_id=1
  amount=150.00
  tax_amount=36.00
  total_amount=186.00
  description=Hotel room accommodation
  due_date=2026-03-22

# 2. Transmit to MyData
curl -X POST http://localhost:8000/payments/invoices/1/mydata/transmit/

# 3. Check status
curl -X GET http://localhost:8000/payments/invoices/1/mydata/status/
```

### Bulk Process

```bash
# Get all invoices that need transmission
curl -X GET http://localhost:8000/payments/invoices/ \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Transmit all pending
curl -X GET "http://localhost:8000/payments/invoices/mydata/bulk-transmit/?format=json" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Export for Record

```bash
# Export invoice to JSON
curl -X GET http://localhost:8000/payments/invoices/1/mydata/export/ > invoice_export.json

# Export to CSV/XML (via report export feature)
curl -X GET http://localhost:8000/portal/business-intelligence/create/ \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## Error Codes & Solutions

| Status | Error | Solution |
|--------|-------|----------|
| 400 | Guest email is required | Add email to guest profile |
| 400 | Invalid invoice amount | Ensure amount > 0 |
| 400 | Amount calculation mismatch | Check amount + tax = total |
| 403 | Unauthorized | Login or provide valid token |
| 404 | Invoice not found | Check invoice ID |
| 500 | HOTEL_TAX_ID not configured | Set environment variable |

---

## Python SDK Usage

If extending the system, use the MyDataService:

```python
from payments.mydata_service import get_mydata_service
from payments.models import Invoice

# Get service singleton
mydata = get_mydata_service()

# Get invoice
invoice = Invoice.objects.get(pk=1)

# Validate
is_valid, errors = mydata.validate_invoice_for_transmission(invoice)
if not is_valid:
    print(f"Validation errors: {errors}")

# Export
export_data = mydata.export_invoice(invoice)
print(export_data)

# Transmit
success, result = mydata.transmit_invoice(invoice)
if success:
    print(f"Transmitted: {result}")
else:
    print(f"Error: {result}")

# Get QR code
qr_data = mydata.get_mydata_qr_data(invoice)
print(f"QR Code: {qr_data}")

# Bulk transmit
results = mydata.bulk_transmit_invoices()
print(f"Success: {results['successful']}, Failed: {results['failed']}")
```

---

## Configuration Reference

Set in Django settings or environment:

```python
# API Configuration
MYDATA_API_BASE = 'https://www1.mydata.aade.gr/api'  # AADE API endpoint
MYDATA_USERNAME = ''  # AADE username
MYDATA_PASSWORD = ''  # AADE password
MYDATA_API_KEY = ''   # Alternative: API key

# Hotel Information
HOTEL_TAX_ID = ''     # 9-digit AFM (tax number)

# Behavior
MYDATA_AUTO_TRANSMISSION = False  # Auto-send on invoice creation
MYDATA_SANDBOX_MODE = True        # Test before production
MYDATA_TRANSMISSION_RETRIES = 3   # Retry count
MYDATA_TIMEOUT = 30               # API timeout (seconds)
```

---

## QR Code Format

Generated QR codes follow VIES (VAT Information Exchange System) format:

```
A|TAX_ID|INVOICE_NUMBER|ISSUE_DATE|GROSS_AMOUNT|VAT_AMOUNT

Example:
A|123456789|INV-20260220-ABC12345|20260220|23800|5700
  ↑ ↑         ↑                    ↑        ↑      ↑
  | |         |                    |        |      └─ VAT amount (cents)
  | |         |                    |        └──────── Gross (cents)
  | |         |                    └───────────────── Issue date (YYYYMMDD)
  | |         └──────────────────────────────────── Invoice number
  | └──────────────────────────────────────────── Hotel tax ID (AFM)
  └────────────────────────────────────────────── Invoice type (A=regular)
```

Print this QR code on invoices for tax authority scanning.

---

## Support & Troubleshooting

### Check Logs
```bash
# View error logs
tail -f HMS/logs/errors.log | grep -i mydata

# View transaction logs
tail -f HMS/logs/transaction.log
```

### Test Configuration
```bash
# Test MyData connectivity
curl -X GET https://www1.mydata.aade.gr/api/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Debug Invoice
```bash
# Use Django shell
python manage.py shell

>>> from payments.models import Invoice
>>> from payments.mydata_service import get_mydata_service
>>> 
>>> invoice = Invoice.objects.get(pk=1)
>>> mydata = get_mydata_service()
>>> is_valid, errors = mydata.validate_invoice_for_transmission(invoice)
>>> print(errors)
```

---

## Rate Limits

- **Per Invoice**: No limit
- **Bulk Transmission**: Process up to 100 invoices at once
- **API Calls**: Subject to AADE rate limiting (typically 10 req/sec)

---

## Version Info

- **MyData Service Version**: 1.0
- **AADE API Version**: Compatible with current MyData API
- **Django Version**: 4.2.7
- **Python Version**: 3.10+

---

*Last Updated: February 20, 2026*
