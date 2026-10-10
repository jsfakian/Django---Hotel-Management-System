# Travel Agent Access Control - Testing Guide

## System Overview

This guide covers testing the travel agent booking system with contract-based property access control and automated staff notifications.

## Test Data Setup

### Pre-configured Test User
- **Username:** `travel_agent_john`
- **Password:** `agent123`
- **Agency:** Global Travel Ltd
- **Can Book:** Grand Hotel (via active contract)
- **Contract Period:** 2026-02-20 to 2027-02-20

## Manual Testing Scenarios

### Scenario 1: Travel Agent Portal Access

**Steps:**
1. Login to the portal with `travel_agent_john` / `agent123`
2. Navigate to the Bookings module

**Expected Results:**
- ✅ User is logged in successfully
- ✅ "Bookings" module is accessible from sidebar
- ✅ User's role shows as "Travel Agent"
- ✅ Can only see bookings from "Grand Hotel" property

**Why it works:**
- User has `travel_agent` group membership
- TravelAgentProfile links user to Global Travel Ltd agency
- Active contract exists between agency and Grand Hotel

---

### Scenario 2: Filtered Booking List for Travel Agent

**Steps:**
1. Login as travel_agent_john
2. Go to Bookings > Portal View
3. Observe the booking list

**Expected Results:**
- ✅ Only bookings for "Grand Hotel" are displayed
- ✅ No bookings from other properties visible
- ✅ Query filters by contract-accessible properties

**Code Reference:**
```python
# In web_views.py module_portal()
property_ids = agent_profile.get_accessible_properties()
queryset = queryset.filter(room__property_id__in=property_ids)
```

---

### Scenario 3: Create New Booking (Happy Path)

**Steps:**
1. Login as travel_agent_john
2. Go to Bookings > Add New
3. Fill in booking details:
   - Guest Name: "John Doe"
   - Room: Select "1010 - double"
   - Check-in: 2026-03-01
   - Check-out: 2026-03-05
   - Purpose: "Business"
   - Booking Source: "travel_agency"
   - Travel Agency: [Should auto-populate with "Global Travel Ltd"]
4. Click "Save" or submit form

**Expected Results:**
- ✅ Booking is created successfully
- ✅ `travel_agency` field auto-filled with "Global Travel Ltd"
- ✅ `booking_source` is "travel_agency"
- ✅ No validation errors
- ✅ Booking shows in list view immediately

**What happens internally:**
1. System identifies user as travel agent
2. Validates travel agent can access Grand Hotel (via contract)
3. Auto-assigns `travel_agency` = Global Travel Ltd
4. Creates notification for all active staff at Grand Hotel
5. Sets notification priority = 'high'
6. Includes travel agency name in notification message

---

### Scenario 4: Unauthorized Property Access Prevention

**Steps:**
1. Login as travel_agent_john
2. Go to Bookings > Add New
3. Attempt to select a room from a different property (e.g., if one exists)
4. Try to submit the form

**Expected Results:**
- ❌ Validation error: "You don't have access to this property"
- ❌ Booking is NOT created
- ❌ Form submission blocked before database write

**Security Check:**
```python
# In module_crud_page()
if not _can_access_property(request.user, room.property):
    return JsonResponse({'errors': {'non_field_errors': 
        "You don't have access to this property"
    }}, status=400)
```

---

### Scenario 5: Travel Agency Field Quick Link

**Steps:**
1. Login as travel_agent_john
2. Go to Bookings > Add New
3. Look for the `travel_agency` input field
4. Notice the "🌐 Agencies" button next to it
5. Click the button

**Expected Results:**
- ✅ Button displays next to travel_agency field
- ✅ Clicking opens Travel Agencies module in new panel
- ✅ Can quickly view/search agencies without losing booking form

**UI Template:**
```html
<!-- In module-crud.html -->
{% if field.name == 'travel_agency' and module_key == 'bookings' %}
    <a href="/portal/travel-agencies/" class="btn btn-sm btn-outline-secondary">
        <i class="fas fa-globe"></i> Agencies
    </a>
{% endif %}
```

---

### Scenario 6: Contract Date Validation

**Steps:**
1. Manually test contract date validation (no UI for this):

```python
# Test in Django shell
from django.contrib.auth.models import User
from accounts.models import TravelAgentProfile
from datetime import date

user = User.objects.get(username='travel_agent_john')
profile = TravelAgentProfile.objects.get(user=user)
accessible_ids = profile.get_accessible_properties()

# Check the contract date range
contract = profile.travel_agency.contract_set.first()
print(f"Contract valid: {contract.start_date} to {contract.end_date}")
print(f"Active today: {contract.is_active()}")
```

**Expected Results:**
- ✅ Only properties with active contracts (status='active' AND dates valid) appear
- ✅ Expired contracts prevent property access
- ✅ Future contracts (start_date > today) prevent property access

---

## Automated Testing Checklist

### Access Control Tests
- [ ] Travel agent can see own agency's contracts
- [ ] Travel agent cannot see contracts from other agencies  
- [ ] Travel agent can only access properties with active contracts
- [ ] Hotel manager can access all properties
- [ ] Other staff can access all properties in their property
- [ ] Non-staff users cannot access booking creation

### Booking Creation Tests
- [ ] Booking created by travel agent saves `booking_source = 'travel_agency'`
- [ ] `travel_agency` field auto-populated from TravelAgentProfile
- [ ] Booking creation triggers notification creation
- [ ] Booking for unauthorized property shows validation error
- [ ] Booking date/time validation still works

### Notification Tests
- [ ] Notification created only when travel agent creates booking
- [ ] Notification goes to all active staff (status='active') at property
- [ ] Notification includes travel agency name
- [ ] Notification priority set to 'high'
- [ ] Notification text references the booking

---

## Database Queries for Verification

### Check Travel Agent Profile
```python
from accounts.models import TravelAgentProfile
from django.contrib.auth.models import User

user = User.objects.get(username='travel_agent_john')
profile = TravelAgentProfile.objects.get(user=user)
print(f"User: {user.username}")
print(f"Agency: {profile.travel_agency.name}")
print(f"Position: {profile.position}")
print(f"Active: {profile.is_active}")
```

### Check Contract Status
```python
from contracts.models import Contract
from properties.models import TravelAgency, Property

agency = TravelAgency.objects.get(name='Global Travel Ltd')
contracts = Contract.objects.filter(travel_agency=agency, status='active')

for contract in contracts:
    print(f"Property: {contract.property.name}")
    print(f"Status: {contract.status}")
    print(f"Valid Period: {contract.start_date} to {contract.end_date}")
    print(f"Is Active: {contract.is_active()}\n")
```

### Check Notifications Created
```python
from notifications.models import Notification
from django.contrib.auth.models import User

# Get all notifications created for staff at Grand Hotel
notifications = Notification.objects.filter(
    recipient__employee__property__name='Grand Hotel'
).order_by('-created_at')[:10]

for notif in notifications:
    print(f"To: {notif.recipient.username}")
    print(f"Message: {notif.message}")
    print(f"Priority: {notif.priority}")
    print(f"Created: {notif.created_at}\n")
```

---

## Access Control Matrix

| User Type | Bookings View | Create Booking | Can See Other Properties | Auto-assign Agency |
|-----------|---------------|----------------|-------------------------|-------------------|
| Travel Agent | ✅ (filtered) | ✅ (if contract) | ❌ | ✅ (required) |
| Hotel Manager | ✅ (all) | ✅ (all) | ✅ | ❌ (optional) |
| Staff | ✅ (own property) | ⚠️ (own property) | ❌ | ❌ (optional) |
| Admin | ✅ (all) | ✅ (all) | ✅ | ❌ (optional) |

---

## Troubleshooting

### Problem: Travel agent sees no bookings
**Check:**
1. User has 'travel_agent' group: `User.groups.filter(name='travel_agent').exists()`
2. TravelAgentProfile exists: `TravelAgentProfile.objects.filter(user=user).exists()`
3. Contract exists and is active: `Contract.objects.filter(..., status='active').exists()`
4. Contract dates are valid: Check `start_date <= today <= end_date`

### Problem: Travel agent can access unauthorized property
**Check:**
1. Confirm property has NO active contract with agent's agency
2. Verify contract status is 'active' (not 'pending' or 'expired')
3. Check `_can_access_property()` function in web_views.py
4. Ensure access validation runs on form submission

### Problem: Notifications not created
**Check:**
1. Booking was created by a travel agent (not manual creation)
2. Property has active staff (Employee with status='active')
3. Check Notification table: `Notification.objects.all()`
4. Verify notification creation function is called:
   - See `_create_booking_notification()` in web_views.py

### Problem: Travel agency auto-assignment not working
**Check:**
1. User is in 'travel_agent' group
2. TravelAgentProfile.is_active = True
3. Form includes travel_agency field in model_fields
4. Check code at line 755+ in web_views.py

---

## Key Implementation Files

- **Models:** [HMS/accounts/models.py](HMS/accounts/models.py#L229-L280) - TravelAgentProfile
- **Views:** [HMS/HMS/web_views.py](HMS/HMS/web_views.py#L18-L761) - Access control functions
- **Templates:** [HMS/templates/module-crud.html](HMS/templates/module-crud.html#L67-L71) - Agency quick link
- **Navigation:** [HMS/templates/incs/nav.html](HMS/templates/incs/nav.html) - Menu item

---

## Performance Notes

### Database Indexes
The TravelAgentProfile model includes optimization:
```python
class Meta:
    indexes = [
        models.Index(fields=['travel_agency', 'is_active']),
    ]
    unique_together = [['user', 'travel_agency']]
```

### Query Optimization
Access control filtering uses:
```python
# Efficient: Returns property IDs only
values_list('property_id', flat=True)

# Then filter bookings
queryset.filter(room__property_id__in=property_ids)
```

---

## Future Enhancements

1. **Admin Interface**: Auto-configure admin for TravelAgentProfile CRUD
2. **Bulk Allocation**: Allow agents to see bulk-allocated rooms
3. **Template Customization**: Customize notification messages per property
4. **Audit Logging**: Track all travel agent bookings for compliance
5. **Rate Limiting**: Prevent abuse of quick booking creation
6. **Multi-Agency Support**: Allow users with multiple agency profiles

---

**Last Updated:** 2026-02-20  
**System Status:** ✅ Ready for Testing  
**Test User:** `travel_agent_john` / `agent123`
