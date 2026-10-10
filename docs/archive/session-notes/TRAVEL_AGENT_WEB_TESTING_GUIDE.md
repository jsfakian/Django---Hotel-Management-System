# Travel Agent System - Manual Web Testing Guide

## Getting Started

### Step 1: Access the Portal
1. Open your browser and navigate to `http://localhost:8000/portal/` (or your Django server URL)
2. You should see the login page

### Step 2: Login as Travel Agent
- **Username:** `travel_agent_john`
- **Password:** `agent123`
- Click "Login"

**Expected Result:**
- You're logged in
- You see the portal dashboard
- In the sidebar, you can see menu items for: Bookings, Rooms, Properties, Travel Agencies, Payments, etc.

---

## Test Scenario 1: View Bookings (Property Filtering)

### Steps:
1. After logging in, click **"Bookings"** in the left sidebar
2. Observe the booking list

### Expected Results:
✅ You see a list of bookings  
✅ ALL bookings displayed are for **"Grand Hotel"** property only  
✅ No bookings from other properties appear  
✅ Table columns show: Guest, Room, Check-in, Check-out, Status, etc.

### Why This Works:
- As a travel agent, your access is restricted via the contract
- The contract links Global Travel Ltd (your agency) to Grand Hotel
- The backend query filters: `Booking.objects.filter(room__property__name="Grand Hotel")`

### Troubleshooting:
- **No bookings appear?** → That's OK! It means no bookings exist for Grand Hotel yet (we'll create one next)
- **Bookings from other hotels visible?** → Contact admin - access control not working
- **Error message?** → Check browser console (F12) for JavaScript errors

---

## Test Scenario 2: Create a New Booking

### Steps:
1. Click **"+ Add New"** button (usually top-right of the Bookings panel)
2. A form panel should appear: "Create Booking"
3. Fill in the form:

**Required Fields:**
- **Guest:** Click dropdown or start typing a guest name
  - If no guests exist, you may need to create one first:
    - Navigate to **Users** module
    - Add a new "Guest" type user
    - Use name like "John Doe" with email "john@example.com"
- **Room:** Select `1010 - Double Room` (or any available room)
- **Check-in Date:** `2026-03-15` (pick any future date)
- **Check-out Date:** `2026-03-20` (5 days later)
- **Number of Guests:** `2`
- **Booking Source:** Select `"Travel Agency"` from dropdown
- **Travel Agency:** Should auto-populate with `"Global Travel Ltd"` ← **KEY: This should be automatic**

**Optional Fields:**
- Special Requests: `"Non-smoking room"`
- Notes: `"Test booking for travel agent system"`

4. Scroll down and click **"Save"** button (or "Create")

### Expected Results:
✅ Form submits successfully  
✅ New booking appears in the list immediately  
✅ Booking shows:
   - Guest name
   - Room: 1010
   - Travel Agency: "Global Travel Ltd"
   - Booking Source: "Travel Agency"
   - Status: "Pending" (default)

✅ **IMPORTANT:** Travel agency auto-filled without you selecting it manually

### Why This Works:
```python
# In web_views.py module_crud_page():
if _is_travel_agent(request.user):
    agent_profile = _get_travel_agent_profile(request.user)
    instance.travel_agency = agent_profile.travel_agency  # Auto-assign!
    instance.save()
    _create_booking_notification(instance, created_by_travel_agent=True)
```

### Troubleshooting:
- **Error: "You don't have access to this property"?**
  - Check that you selected a room from Grand Hotel
  - Travel agents can ONLY book rooms at properties with active contracts
  
- **Travel Agency field not auto-filled?**
  - Ensure you're logged in as travel_agent_john
  - Check that user has 'travel_agent' group
  - See `/admin/` to verify group assignment
  
- **Form won't submit?**
  - Check all required fields are filled (marked with *)
  - Look for validation messages in red text
  - Check browser console (F12 → Console tab) for JavaScript errors

---

## Test Scenario 3: Verify Unauthorized Property Access Prevention

**Goal:** Confirm that travel agents CANNOT book rooms from properties without contracts

### Setup (if you have another property):
1. Check if other properties exist in the system
2. If not, skip this test (Single property system)

### Steps:
IF other properties exist:

1. Click **"Bookings"** → **"+ Add New"**
2. Try to select a room from a DIFFERENT property (not Grand Hotel)
3. Fill in other required fields
4. Click **"Save"**

### Expected Results:
❌ Form submission fails  
❌ Error message appears: `"You don't have access to this property"`  
❌ Booking is NOT created  
❌ You're still on the form (not redirected away)

### Why This Works:
```python
# Access control in module_crud_page():
if not _can_access_property(request.user, room.property):
    return JsonResponse({
        'errors': {'non_field_errors': "You don't have access to this property"}
    }, status=400)
```

### Troubleshooting:
- **No error appears / booking is created?**
  - Access control is NOT working properly
  - Contact IT to debug web_views.py functions
  - Check: Is user in 'travel_agent' group? Does TravelAgentProfile exist?

---

## Test Scenario 4: Travel Agency Quick Link

### Steps:
1. Click **"Bookings"** → **"+ Add New"**
2. Look for the **"travel_agency"** input field in the form
3. Next to it, you should see a button: **🌐 Agencies**
4. Click the **Agencies** button

### Expected Results:
✅ "Travel Agencies" module opens in a new panel (AJAX loaded)  
✅ Shows a list of travel agencies  
✅ You can see "Global Travel Ltd" in the list  
✅ Clicking "Edit" shows agency details (commission %, allocation %, etc.)  
✅ You can close this panel and return to booking creation

### Why This Works:
Travel agencies link is placed next to the travel_agency input field in the form template:
```html
{% if field.name == 'travel_agency' and module_key == 'bookings' %}
    <a href="/portal/travel-agencies/" class="btn btn-sm btn-outline-secondary">
        <i class="fas fa-globe"></i> Agencies
    </a>
{% endif %}
```

### Troubleshooting:
- **No Agencies button visible?**
  - Check that you're in Bookings module
  - Scroll down in the form to see all fields
  - Refresh the page
  
- **Clicking button causes page reload (not AJAX)?**
  - Something is wrong with the AJAX implementation
  - Should open panel dynamically without page reload

---

## Test Scenario 5: Check Notification System Setup

**Note:** This test verifies notifications WOULD be created. Actual delivery depends on staff setup.

### Steps:
1. In Django admin (`/admin/`), login with a manager account
2. Navigate to: **Notifications** → **Notification**
3. Check the list of recent notifications

OR use Python shell:
```python
python manage.py shell

from notifications.models import Notification
from django.contrib.auth.models import User

# Get all notifications in the system
all_notifs = Notification.objects.all().order_by('-created_at')
print(f"Total notifications: {all_notifs.count()}")

# Get most recent
for notif in all_notifs[:5]:
    print(f"To: {notif.user.username}")
    print(f"Message: {notif.message}")
    print(f"Priority: {notif.priority}")
    print("---")
```

### Expected Results:
✅ When you created a booking in Scenario 2, notifications were created  
✅ IF property has active staff (Employee records):
   - Each staff member should have a notification
   - Title mentions "Travel Agent"
   - Message mentions the agency: "Global Travel Ltd"
   - Priority is "high"
   
⚠️ IF property has NO staff:
   - No notifications created (expected behavior)
   - Message: "No active staff at property"

---

## Test Scenario 6: Verify Booking Source Tracking

### Steps:
1. Create a booking as described in Scenario 2
2. After booking is saved, click to view/edit it
3. Check the `booking_source` field value

### Expected Results:
✅ Field shows: `"Travel Agency"`  
✅ This is automatically set when a travel agent creates a booking  
✅ Helps distinguish bookings by source (useful for analytics)

### Database Verification:
```python
from room.models import Booking

# Check the booking you just created
latest_booking = Booking.objects.all().order_by('-id').first()
print(f"Booking Source: {latest_booking.booking_source}")
print(f"Travel Agency: {latest_booking.travel_agency}")

# Should output:
# Booking Source: travel_agency
# Travel Agency: Global Travel Ltd
```

---

## Test Scenario 7: Contract Validation (Advanced)

**Goal:** Understand how contracts control access

### Background Info:
A contract is created between a travel agency and a property. It has:
- Status: active/pending/expired
- Start date: When contract begins
- End date: When contract expires

Travel agents can ONLY access properties where:
- Contract `status = 'active'` AND
- Contract `start_date ≤ today ≤ end_date`

### Check Your Contract:
**In Python shell:**
```python
from contracts.models import Contract
from properties.models import TravelAgency
from datetime import date

# Find the contract for your agency
agency = TravelAgency.objects.get(name='Global Travel Ltd')
contract = Contract.objects.filter(travel_agency=agency).first()

if contract:
    print(f"Property: {contract.property.name}")
    print(f"Status: {contract.status}")
    print(f"Valid Period: {contract.start_date} to {contract.end_date}")
    print(f"Active Today: {contract.is_active()}")
    
    # Check if today is within range
    today = date.today()
    in_range = contract.start_date <= today <= contract.end_date
    print(f"Today ({today}) in range: {in_range}")
```

### Expected Output:
```
Property: Grand Hotel
Status: active
Valid Period: 2026-02-20 to 2027-02-20
Active Today: True
Today (2026-02-20) in range: True
```

---

## Browser Developer Tools Testing

### Checking Network Requests:
1. Open Browser DevTools: **F12** or **Right-click → Inspect**
2. Go to **Network** tab
3. Create a new booking (as in Scenario 2)
4. Watch the requests:
   - Should see POST request to `/portal/module/bookings/` with status **200 OK**
   - Response should include the new booking data
   - Should see AJAX requests, not full page reload

### Checking Console Errors:
1. Open Browser DevTools: **F12**
2. Go to **Console** tab
3. Look for any red error messages
4. JavaScript errors would appear here

### Checking Local Storage:
1. In DevTools, go to **Application** or **Storage** tab
2. Check **Local Storage** / **Session Storage**
3. Look for any authorization tokens or session data

---

## Troubleshooting Guide

### Problem: Can't login
- **Check:** Username is exactly `travel_agent_john` (case-sensitive)
- **Check:** Password is `agent123`
- **Try:** Clear browser cache (Ctrl+Shift+Delete) and try again
- **Check:** User exists in Django admin (`/admin/auth/user/`)

### Problem: No bookings visible
- **Check:** Is at least one booking supposed to exist?
- **Try:** Create a new booking first
- **Check:** You're in correct property scope (you should only see Grand Hotel bookings)

### Problem: Can create booking for unauthorized property
- **Critical Issue:** Contact admin immediately
- **Debug:** Check `/admin/` → Accounts → Travel Agent Profiles
  - Verify your profile exists
  - Verify correct agency assigned
  - Verify is_active = True
- **Debug:** Check Contracts
  - Verify contract exists between agency and property
  - Verify status = "active"
  - Verify dates are valid

### Problem: Can't see form fields
- **Try:** Scroll down in the form
- **Try:** Refresh the page (F5)
- **Check:** Browser zoom level (Ctrl+0 to reset)
- **Check:** Mobile responsiveness (resize window)

### Problem: Form won't save
- **Check:** All required fields (* asterisk) are filled
- **Check:** No error messages (look for validation errors in red)
- **Browser Console (F12):** Any JavaScript errors?
- **Try:** Fresh page reload and retry

### Problem: Notification not appearing in admin
- **Check:** Did you actually create a booking?
- **Check:** Are there active staff at the property?
  - In admin: Properties → Grand Hotel → Edit
  - Check if any employees are assigned
  - Check if their status = "active"
- **Check:** Notification model in admin
  - Navigate to `/admin/notifications/notification/`
  - Recent notifications should appear at top
  - Filter by recipient username if needed

---

## Advanced Testing: Direct Database Inspection

### Check Travel Agent Profile:
```python
python manage.py shell

from django.contrib.auth.models import User
from accounts.models import TravelAgentProfile

user = User.objects.get(username='travel_agent_john')
profile = user.travel_agent_profile

print(f"Username: {user.username}")
print(f"Groups: {list(user.groups.values_list('name', flat=True))}")
print(f"Agency: {profile.travel_agency.name}")
print(f"Position: {profile.position}")
print(f"Active: {profile.is_active}")

# Get accessible properties
prop_ids = profile.get_accessible_properties()
properties = Property.objects.filter(id__in=prop_ids)
for prop in properties:
    print(f"  → Can access: {prop.name}")
```

### Check Contract Status:
```python
from contracts.models import Contract
from properties.models import TravelAgency
from datetime import date

agency = TravelAgency.objects.get(name='Global Travel Ltd')
contracts = Contract.objects.filter(travel_agency=agency)

for contract in contracts:
    today = date.today()
    in_range = contract.start_date <= today <= contract.end_date
    print(f"{contract.property.name}:")
    print(f"  Status: {contract.status}")
    print(f"  Period: {contract.start_date} → {contract.end_date}")
    print(f"  Active: {contract.is_active()}")
    print(f"  In Range: {in_range}")
```

### Check Notifications Created:
```python
from notifications.models import Notification
from django.contrib.auth.models import User

# Get notifications for all staff members
staff_notifications = Notification.objects.filter(
    user__employee__isnull=False
).order_by('-created_at')

for notif in staff_notifications[:10]:
    print(f"To: {notif.user.username}")
    print(f"Title: {notif.title}")
    print(f"Message: {notif.message}")
    print(f"Priority: {notif.priority}")
    print(f"Created: {notif.created_at}")
    print("---")
```

---

## Performance Notes

### Expected Load Times:
- **Login:** < 1 second
- **View bookings list:** < 500ms (with 100+ bookings)
- **Create booking form:** < 200ms
- **Save booking:** 1-2 seconds (creates notifications)
- **Notification creation:** < 100ms per staff member

### If Things Are Slow:
1. Check Django logs for slow queries
2. Use Django Debug Toolbar (`django-debug-toolbar`)
3. Verify database connection
4. Check server resources (CPU, RAM, disk)

---

## Summary Checklist

### ✅ Basic Functionality
- [ ] Can login as travel_agent_john
- [ ] Dashboard loads without errors
- [ ] Menu items visible in sidebar

### ✅ Access Control
- [ ] Bookings list shows only Grand Hotel
- [ ] Can view/edit bookings
- [ ] Cannot see bookings from other properties

### ✅ Booking Creation
- [ ] Can create new booking
- [ ] Travel agency auto-fills (no manual selection needed)
- [ ] Booking source shows "Travel Agency"
- [ ] Booking appears in list immediately

### ✅ Security
- [ ] Cannot access unauthorized properties
- [ ] Get validation error if trying different property
- [ ] Booking not created on validation failure

### ✅ Features
- [ ] Agencies quick link button works
- [ ] Can click button to view agency details
- [ ] Can return to booking form

### ✅ Notifications
- [ ] Notifications table populated (if staff exists)
- [ ] Recent notifications appear
- [ ] Can see booking-related messages

---

## Next Steps

If all tests pass:
1. ✅ System is working correctly
2. ✅ Ready for production use
3. 📊 Consider enabling booking analytics
4. 📧 Set up email notifications to staff
5. 🔔 Configure SMS notifications for urgent bookings

If tests fail:
1. Check the **Troubleshooting Guide** section above
2. Verify test data setup (See TRAVEL_AGENT_IMPLEMENTATION_SUMMARY.md)
3. Review Django logs for errors
4. Contact development team with specific error messages

---

**Happy Testing!** 🎉

For technical questions, see:
- [TRAVEL_AGENT_IMPLEMENTATION_SUMMARY.md](TRAVEL_AGENT_IMPLEMENTATION_SUMMARY.md) - Architecture details
- [TRAVEL_AGENT_TESTING_GUIDE.md](TRAVEL_AGENT_TESTING_GUIDE.md) - Comprehensive test scenarios
