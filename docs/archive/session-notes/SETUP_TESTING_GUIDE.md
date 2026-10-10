# Channel Integration & Inventory System - Setup & Testing Guide

**Date:** February 20, 2026

## Quick Start

### 1. Database Setup

```bash
# Navigate to Django project
cd HMS

# Create migrations (already done)
python manage.py makemigrations channels inventory

# Apply migrations
python manage.py migrate channels inventory
```

### 2. Create Django Admin Account (if needed)

```bash
python manage.py createsuperuser
# Follow prompts to create admin user
```

### 3. Access Admin Interface

Navigate to: `http://localhost:8000/admin/`

## Testing Workflow

### Test 1: Create a Channel Configuration

1. Log in to Django Admin
2. Navigate to **Channels > Channels**
3. Click **Add Channel**
4. Fill in:
   - **Property:** Select a property
   - **Channel Name:** Select "trivago" from dropdown
   - **Channel Type:** OTA
   - **Account ID:** test_trivago_123
   - **API Key:** test_api_key_abc123
   - **API Secret:** test_secret_xyz789
   - **Room Mappings:**
     ```json
     {
       "room_mappings": {
         "1": "trivago_room_001",
         "2": "trivago_room_002"
       }
     }
     ```
5. Click **Save**

### Test 2: Initialize Room Availability

```python
# Django shell
python manage.py shell

from room.models import Room
from inventory.models import RoomAvailability
from datetime import date, timedelta

# Get a room
room = Room.objects.first()

# Create availability for next 30 days
start_date = date.today()
for i in range(30):
    check_date = start_date + timedelta(days=i)
    RoomAvailability.objects.get_or_create(
        room=room,
        date=check_date,
        defaults={
            'total_units': 1,
            'available_units': 1,
            'booked_units': 0,
            'blocked_units': 0,
            'base_price': 150.00
        }
    )

print("Availability initialized for 30 days")
```

### Test 3: Test Webhook Signature Generation

```python
# Generate test signature for webhook testing
import hmac
import hashlib
import json

api_secret = "test_secret_xyz789"
payload = json.dumps({
    "channel_booking_id": "TEST-001",
    "timestamp": 1645195200,
    "event": "booking_created",
    "guest_first_name": "Test",
    "guest_last_name": "Guest",
    "guest_email": "test@example.com",
    "guest_phone": "+1-555-0000",
    "room_id": 1,
    "check_in": "2026-03-15",
    "check_out": "2026-03-18",
    "number_of_guests": 2,
    "special_requests": "",
    "total_price": 450.00,
    "currency": "USD"
})

signature = hmac.new(
    api_secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

print(f"Signature: {signature}")
print(f"Payload:\n{payload}")
```

### Test 4: Send Test Booking Webhook

```bash
# Get channel ID from admin (assume it's 1)
CHANNEL_ID=1
SIGNATURE="<generated_signature_from_above>"

# Send webhook
curl -X POST http://localhost:8000/api/v1/channels/$CHANNEL_ID/bookings/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=$SIGNATURE" \
  -d '{
    "channel_booking_id": "TEST-001",
    "timestamp": 1645195200,
    "event": "booking_created",
    "guest_first_name": "Test",
    "guest_last_name": "Guest",
    "guest_email": "test@example.com",
    "guest_phone": "+1-555-0000",
    "room_id": 1,
    "check_in": "2026-03-15",
    "check_out": "2026-03-18",
    "number_of_guests": 2,
    "special_requests": "extra_pillows",
    "total_price": 450.00,
    "currency": "USD"
  }'
```

**Expected Response (201):**
```json
{
  "booking_id": 123,
  "status": "confirmed",
  "confirmation_number": "BKNG-123",
  "booking_created_at": "2026-02-20T12:00:00Z"
}
```

### Test 5: Check Channel Booking Was Created

```python
# Django shell
from channels.models import ChannelBooking

# View the created channel booking
cb = ChannelBooking.objects.last()
print(f"Channel Booking ID: {cb.id}")
print(f"Channel: {cb.channel}")
print(f"Channel Booking ID: {cb.channel_booking_id}")
print(f"NEPHELE Booking ID: {cb.nephele_booking_id}")
print(f"Status: {cb.sync_status}")
```

### Test 6: Check Availability Was Updated

```python
# Django shell
from inventory.models import RoomAvailability
from room.models import Room
from datetime import date

room = Room.objects.first()
avail = RoomAvailability.objects.filter(
    room=room,
    date__gte=date(2026, 3, 15),
    date__lt=date(2026, 3, 18)
).first()

print(f"Room: {avail.room.room_number}")
print(f"Date: {avail.date}")
print(f"Total Units: {avail.total_units}")
print(f"Available Units: {avail.available_units}")
print(f"Booked Units: {avail.booked_units}")
```

### Test 7: Trigger Availability Sync

```bash
# Get channel ID (assume 1)
CHANNEL_ID=1
TOKEN="your_jwt_token"

curl -X POST http://localhost:8000/api/v1/channels/$CHANNEL_ID/availability/sync/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sync_type": "full_sync",
    "date_from": "2026-03-15",
    "date_to": "2026-03-31"
  }'
```

**Expected Response (202):**
```json
{
  "sync_id": "celery_task_uuid",
  "status": "queued",
  "message": "Availability sync queued for processing"
}
```

### Test 8: Update Room Availability

```bash
TOKEN="your_jwt_token"
ROOM_ID=1

curl -X PUT http://localhost:8000/api/v1/inventory/rooms/$ROOM_ID/availability/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2026-03-20",
    "date_to": "2026-03-25",
    "available_units": 0,
    "blocked_units": 1,
    "notes": "Maintenance and cleaning"
  }'
```

**Expected Response (200):**
```json
{
  "room_id": 1,
  "dates_updated": 5,
  "override_applied": true
}
```

### Test 9: View Sync Logs

```bash
PROPERTY_ID=1
TOKEN="your_jwt_token"

curl "http://localhost:8000/api/v1/inventory/sync-log/$PROPERTY_ID/?status=success&days=7" \
  -H "Authorization: Bearer $TOKEN"
```

## API Testing with Postman

### Import Collection

1. Create new Postman collection: "NEPHELE Channel Integration"
2. Add requests:

**Request 1: Get JWT Token**
```
POST http://localhost:8000/api/v1/auth/login/
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "your_password"
}
```

**Request 2: List Channels**
```
GET http://localhost:8000/api/v1/channels/
Authorization: Bearer {{token}}
```

**Request 3: Get Availability**
```
GET http://localhost:8000/api/v1/inventory/availability/1/?date_from=2026-03-15&date_to=2026-03-31
Authorization: Bearer {{token}}
```

## Expected Features Post-Implementation

### ✅ Completed

- [x] Channel model with support for 15+ platforms
- [x] Room availability centralized management
- [x] Webhook endpoint for receiving OTA bookings
- [x] Automatic availability synchronization
- [x] Staff notification system (via Celery)
- [x] Sync logging and monitoring
- [x] Admin interface for all models
- [x] API endpoints with proper authentication
- [x] Error tracking and retry logic

### 🔄 In Progress / Pending

- [ ] Integrate with actual OTA APIs (Trivago, Booking.com, etc.)
- [ ] Implement channel-specific sync formats
- [ ] Add website webhook integration
- [ ] Build staff UI for availability management
- [ ] Implement automatic pricing syncs
- [ ] Add analytics for booking sources

## Troubleshooting

### Issue: "Channel not found"
- Check channel ID matches what you created
- Verify channel is_active is True

### Issue: "Room not found"
- Ensure room_id matches room in property
- Check room exists in database

### Issue: "Duplicate booking"
- Webhook was likely processed twice
- Check sync logs for details
- Use different channel_booking_id for retry

### Issue: Email not sent
- Configure EMAIL_BACKEND in settings
- Check notifications.tasks.send_channel_booking_alert logs
- Verify SMTP credentials

### Issue: No rooms synced
- Check sync logs in Django admin
- Verify mapping_config room_mappings are set
- Check channel.sync_enabled is True

## Next Tasks

1. **Implement OTA APIs** - Add actual API integrations for each channel
2. **Website Integration** - Build website widget and notification endpoints
3. **Staff UI** - Create availability management interface
4. **Analytics** - Build reports by booking source
5. **Mobile App** - Add notifications to mobile

---

**Setup Time:** ~15-20 minutes  
**Testing Time:** ~30 minutes  
**Difficulty:** Medium  

