# MyData (AADE) Integration Guide

## Overview

This guide explains how to integrate the NEPHELE Hotel Management System with **MyData** (AADE - Ανεξάρτητη Δημοσιονομική Αρχή), the Greek tax authority's electronic invoicing system.

MyData is mandatory for Greek businesses to electronically transmit invoices and tax information to the tax authorities. This integration enables automatic invoice transmission without manual AADE platform access.

## Configuration

### Prerequisites

1. **AADE Account**: You must have an active AADE account and credentials
2. **AFM (Α.Φ.Μ.) - Tax Number**: Your hotel's 9-digit Greek tax identification number
3. **API Credentials**: MyData API username/password or API key from AADE

### Environment Variables

Set the following environment variables in your `.env` file or Docker environment:

```bash
# MyData API Configuration
MYDATA_USERNAME=your_aade_username
MYDATA_PASSWORD=your_aade_password
MYDATA_API_KEY=your_api_key  # Optional, alternative authentication

# Hotel Tax Information
HOTEL_TAX_ID=123456789  # Your AFM (9-digit number)

# MyData Settings
MYDATA_API_BASE=https://www1.mydata.aade.gr/api  # Production URL
MYDATA_TIMEOUT=30  # API request timeout in seconds
MYDATA_SANDBOX_MODE=True  # Set to False for production
MYDATA_AUTO_TRANSMISSION=False  # Manual transmission by default
MYDATA_TRANSMISSION_RETRIES=3  # Number of retry attempts
```

### Django Settings

Update `HMS/settings.py` with your configuration. Default values are shown below:

```python
# MyData (AADE) Integration
MYDATA_API_BASE = 'https://www1.mydata.aade.gr/api'
MYDATA_USERNAME = ''  # Configure via environment
MYDATA_PASSWORD = ''  # Configure via environment
MYDATA_API_KEY = ''   # Configure via environment
HOTEL_TAX_ID = ''     # Configure via environment
MYDATA_AUTO_TRANSMISSION = False  # Manual mode recommended
MYDATA_SANDBOX_MODE = True  # Test before production
```

## Usage

### Invoice Creation with MyData Support

When creating invoices in the system, all invoices are automatically prepared for MyData transmission:

1. Navigate to **Portal → Invoices → Create**
2. Fill in required fields:
   - Guest information
   - Amount (before VAT)
   - Tax amount (VAT)
   - Description
   - Due date
3. The system calculates total amount and generates an invoice number
4. Submit the form

### Transmitting Individual Invoices

#### Via Web Interface

1. Go to **Portal → Invoices → Read** (View all invoices)
2. Select an invoice to view details
3. Click **"Transmit to MyData"** button
4. System will:
   - Validate invoice completeness
   - Generate transmission ID
   - Create QR code
   - Mark as transmitted

#### Via API

```bash
# Transmit a single invoice
curl -X POST http://localhost:8000/payments/invoices/1/mydata/transmit/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get transmission status
curl -X GET http://localhost:8000/payments/invoices/1/mydata/status/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Export invoice in MyData format
curl -X GET http://localhost:8000/payments/invoices/1/mydata/export/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Bulk Transmission

Transmit multiple invoices at once:

#### Via Web Interface

1. Go to **Admin → Payments → Invoices**
2. Select invoices to transmit (checkbox)
3. Choose **"Transmit selected invoices to MyData"** from Actions dropdown
4. Click **"Go"**

#### Via API/Management Command

```bash
# Bulk transmit all pending invoices
curl -X GET http://localhost:8000/payments/invoices/mydata/bulk-transmit/ \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Get JSON response with results
curl -X GET "http://localhost:8000/payments/invoices/mydata/bulk-transmit/?format=json" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

Response example:
```json
{
  "total": 15,
  "successful": 13,
  "failed": 2,
  "transmitted_ids": [
    {"invoice_number": "INV-20260220-ABC12345", "transmission_id": "AADE-20260220-123456"},
    ...
  ],
  "errors": [
    {"invoice_number": "INV-20260219-XYZ99999", "errors": ["Guest email is required"]},
    ...
  ]
}
```

## Invoice Workflow

### States

```
Draft → Issued → MyData Transmission → Paid/Cancelled
```

1. **Draft**: Invoice created but not finalized
2. **Issued**: Invoice finalized and ready for transmission
3. **Transmitted**: Invoice sent to MyData (marked with transmission ID + QR code)
4. **Paid**: Payment received
5. **Cancelled**: Invoice cancelled with cancellation mark

### MyData Fields

Each invoice tracks these MyData-specific fields:

| Field | Description |
|-------|-------------|
| `mydata_transmitted` | Boolean: Has invoice been transmitted? |
| `mydata_transmission_id` | String: MyData transmission reference ID |
| `mydata_qr_code` | String: QR code data for compliance |
| `mydata_transmission_date` | DateTime: When transmitted |
| `mydata_cancel_mark` | String: Cancellation mark (if cancelled) |
| `mydata_cancel_date` | DateTime: When cancelled |

## Validation Rules

Before transmission, invoices must meet these requirements:

✓ Invoice number is present
✓ Amount > 0
✓ Total amount > 0  
✓ Issue date is set
✓ Due date is set and after issue date
✓ Guest email is provided
✓ Guest first and last names provided
✓ Amount + Tax = Total (calculation check)

## QR Code Generation

The system generates a compliance QR code in MyData format:

```
Format: A|TAX_ID|INVOICE_NUMBER|ISSUE_DATE|GROSS_AMOUNT|VAT_AMOUNT

Example: A|123456789|INV-20260220-ABC12345|20260220|23800|5700
```

This QR code can be printed on invoices for easy scanning by tax authorities.

## Troubleshooting

### Issue: "HOTEL_TAX_ID must be configured"

**Solution**: Set environment variable `HOTEL_TAX_ID` with your 9-digit AFM number:
```bash
export HOTEL_TAX_ID=123456789
```

### Issue: "Guest email is required"

**Solution**: Ensure guest profile is complete with email address before transmitting:
1. Go to **Portal → Guests → Edit**
2. Add email address
3. Save and retry transmission

### Issue: "Invalid invoice amount"

**Solution**: Verify invoice has:
- Valid amount > 0
- Valid tax amount ≥ 0
- Total = amount + tax

### Issue: MyData API timeout

**Solution**: Increase timeout in settings:
```bash
export MYDATA_TIMEOUT=60  # Increase to 60 seconds
```

### Issue: "Transmit" button not visible

**Possible causes**:
- Invoice already transmitted (check `mydata_transmitted` field)
- User is not staff/admin (check permissions)
- Invoice status is not "issued" (change status first)

## Testing

### With Sandbox Mode (Recommended)

Before going live, test with MyData sandbox:

```bash
MYDATA_SANDBOX_MODE=True
MYDATA_API_BASE=https://test.mydata.aade.gr/api
```

Use test credentials from AADE.

### Manual Testing

1. Create test invoices via web interface
2. Validate invoice data in Admin → Invoices
3. Use API endpoint to test transmission without GUI
4. Check MyData transmission ID in invoice record

## API Reference

### GET /payments/invoices/

List all invoices with MyData status

### POST /payments/invoices/{id}/mydata/transmit/

Transmit invoice to MyData

**Response:**
```json
{
  "success": true,
  "message": "Invoice transmitted to MyData. Transmission ID: AADE-..."
}
```

### GET /payments/invoices/{id}/mydata/status/

Get MyData transmission status

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

### GET /payments/invoices/{id}/mydata/export/

Export invoice in MyData JSON format

### GET /payments/invoices/mydata/bulk-transmit/

Bulk transmit all pending invoices

## Database Schema

### Invoice Model New Fields

```python
class Invoice(models.Model):
    # ... existing fields ...
    
    # MyData Integration
    mydata_transmitted = BooleanField(default=False)
    mydata_transmission_id = CharField(max_length=100, blank=True)
    mydata_qr_code = TextField(blank=True)
    mydata_transmission_date = DateTimeField(null=True, blank=True)
    mydata_cancel_mark = CharField(max_length=100, blank=True)
    mydata_cancel_date = DateTimeField(null=True, blank=True)
```

## Security Considerations

1. **Credentials**: Store API credentials only in environment variables, never in code
2. **SSL/TLS**: All MyData API calls use HTTPS
3. **Rate Limiting**: AADE may apply rate limits - implement exponential backoff
4. **Data Privacy**: Invoices contain guest personal data - follow GDPR requirements
5. **Audit Trail**: All transmissions are logged for compliance

## Future Enhancements

Planned features for Phase 3:

- [ ] Automatic transmission on invoice issuance
- [ ] Real-time AADE compliance checking
- [ ] Invoice cancellation/adjustment support
- [ ] Multi-currency handling (EUR, USD, GBP)
- [ ] Webhook support for AADE notifications
- [ ] Advanced reporting dashboard
- [ ] Integration with accounting software (Wave, Wave Accounting)

## References

- **AADE MyData**: https://www.aade.gr/mydata
- **AADE API Documentation**: https://www1.mydata.aade.gr/docs
- **Invoice Format Specs**: ISO 20022 (UBL 2.1)
- **QR Code Format**: VIES (VAT Information Exchange System)

## Support

For issues or questions about MyData integration:

1. Check this guide's Troubleshooting section
2. Review Django logs: `HMS/logs/errors.log`
3. Contact AADE support: https://www.aade.gr/contact
4. Open an issue on the project repository

## Changelog

### v1.0 (2026-02-20)
- Initial MyData integration
- Invoice transmission support
- QR code generation
- Bulk transmission API
- Admin integration
