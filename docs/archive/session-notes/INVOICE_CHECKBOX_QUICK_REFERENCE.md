# Invoice MyData Checkbox - Quick Reference

## What Was Done

Added an **unchecked-by-default checkbox** to invoice creation/update forms that automatically transmits invoices to MyData (Greek tax authority) when checked.

## Quick User Guide

### Create Invoice with MyData
```
1. Go to: /portal/invoices/create/
2. Fill invoice details
3. ☐ Leave "Transmit to MyData" UNCHECKED (default)
   ✓ Click Save → Invoice created, no MyData

   OR

3. ☑ Check "Transmit to MyData"
   ✓ Click Save → Invoice created AND transmitted to MyData
```

### Update Invoice with MyData
```
1. Go to existing invoice
2. Modify fields as needed
3. ☐ To skip: Leave unchecked → Save
   ☑ To transmit: Check checkbox → Save
```

## Technical Summary

### New Files/Changes

| File | What Changed |
|------|--------------|
| `payments/forms.py` | Added `InvoiceForm` with checkbox field |
| `HMS/web_views.py` | Added InvoiceForm import + MyData transmission logic |
| `payments/migrations/0002_add_mydata_fields.py` | Auto-created migration (ready to run) |

### Checkbox Behavior

```python
transmit_to_mydata = forms.BooleanField(
    required=False,      # Unchecked by default ✓
    initial=False,       # Default unchecked ✓
    label='Transmit to MyData (AADE)',
    help_text='If checked, the invoice will be automatically transmitted to the Greek tax authority after creation'
)
```

### Transmission Flow

```
Form Submitted
    ↓
Is checkbox checked?
    ↓
    YES → Validate invoice → Transmit to MyData
    └→ Shows success/error message
    ↓
    NO → Skip MyData
    └→ Normal success message
```

### Validation Before Transmission

If checkbox is checked, the system validates:
- Invoice amount > 0
- Total amount > 0
- Guest has email
- Guest has name
- Dates are valid
- Amount + Tax = Total

If validation fails → Error message, invoice still saved

## Response Messages

| Action | Message |
|--------|---------|
| Create without MyData | "Invoice record created successfully." |
| Create with MyData ✓ | "Invoice created and transmitted to MyData (ID: AADE-...)." |
| Update without MyData | "Invoice record updated successfully." |
| Update with MyData ✓ | "Invoice updated and transmitted to MyData (ID: AADE-...)." |
| Already transmitted | "Invoice already transmitted to MyData." |
| Transmission failed | "Invoice created. MyData transmission failed: [reason]." |
| Validation error | "Invoice created. MyData transmission skipped: [errors]." |

## Database Migration

Status: **Ready to apply**

When database is available:
```bash
python manage.py migrate payments
```

Adds 6 fields:
- `mydata_transmitted` 
- `mydata_transmission_id`
- `mydata_qr_code`
- `mydata_transmission_date`
- `mydata_cancel_mark`
- `mydata_cancel_date`

## Form Styling

Works with Bootstrap:
```html
<div class="form-check">
    <input type="checkbox" 
           class="form-check-input" 
           name="transmit_to_mydata"
           id="id_transmit_to_mydata">
    <label class="form-check-label">
        Transmit to MyData (AADE)
    </label>
</div>
```

## Admin Interface

Admin users can also:
1. See MyData status in invoice list
2. Filter invoices by transmission status
3. Bulk transmit multiple invoices
4. View transmission ID and QR code in detail view

## Testing Checklist

- [ ] Database migration applied
- [ ] Create invoice WITHOUT checking MyData → Verify saved without transmission
- [ ] Create invoice WITH checkbox → Verify MyData transmission attempted
- [ ] Edit invoice → Can transmit via checkbox if not already sent
- [ ] Invalid invoice → Checkbox ignored, shows validation error
- [ ] Check admin invoice list → See MyData status
- [ ] Verify messages display correctly

## Configuration

For MyData to work, set environment variables:

```bash
export HOTEL_TAX_ID=123456789          # Required: Your 9-digit AFM
export MYDATA_SANDBOX_MODE=True        # Optional: Test mode (True by default)
export MYDATA_USERNAME=username        # Optional: AADE username
export MYDATA_PASSWORD=password        # Optional: AADE password
```

## Default Behavior

✅ **Checkbox is UNCHECKED by default**
✅ Invoice can be created WITHOUT MyData transmission
✅ User must explicitly check checkbox to enable transmission
✅ Only takes effect if invoice passes validation
✅ Transmission failure does NOT prevent invoice creation
✅ Clear user feedback for all outcomes

## Code References

### Form Creation
[payments/forms.py#InvoiceForm](payments/forms.py)

### Web View Integration
[HMS/web_views.py#module_crud_page](HMS/web_views.py)

### MyData Service
[payments/mydata_service.py](payments/mydata_service.py)

### Migration
[payments/migrations/0002_add_mydata_fields.py](payments/migrations/0002_add_mydata_fields.py)

## Support

**If checkbox not showing:**
- Verify migration has been applied
- Refresh browser cache (Ctrl+F5)
- Check Django logs

**If MyData transmission fails:**
- Verify guest has valid email
- Check HOTEL_TAX_ID is set
- See MYDATA_INTEGRATION_GUIDE.md for details

---

**Implementation Date**: February 20, 2026  
**Status**: ✅ COMPLETE & READY TO TEST
