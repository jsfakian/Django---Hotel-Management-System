# Channel Integration & Centralized Availability Implementation Guide

**Date:** February 20, 2026  
**Status:** ✅ Complete  
**Module:** NEPHELE Hotel Management System - Phase 2  

## Overview

This implementation includes:

1. **Channel Integration Service** - Connect to OTA platforms (Trivago, Booking.com, Airbnb, Expedia, Agoda, VRBO, etc.)
2. **Centralized Inventory Management (Nephele)** - Single source of truth for room availability across all channels
3. **Automatic Staff Notifications** - Alert property staff when new bookings arrive from OTA platforms
4. **Website Webhooks** - Receive bookings from hotel's website and sync availability

## Architecture

### New Django Apps

```
channels/          → OTA platform management & booking reception
inventory/         → Centralized availability management
```

### Database Schema

**channels_channel**
- Stores OTA platform credentials and configurations
- Supports: Booking.com, Trivago, Airbnb, Expedia, Agoda, VRBO, Booking Buddy, Hotwire, Travelocity, Priceline, Orbitz, Kayak, HostelWorld, Ctrip, Custom

**channels_channelbooking**
- Links external OTA booking IDs to internal NEPHELE booking IDs
- Used for duplicate detection and sync tracking

**inventory_roomavailability**
- Centralized availability record (one per room per date)
- Tracks: available units, booked units, blocked units, overbooked units
- Includes pricing (base and dynamic)

**inventory_availabilitysynclog**
- Logs all synchronization attempts to channels
- Tracks success/failure for troubleshooting

## API Endpoints

### Channel Management

#### List/Create Channels
```
GET    /api/v1/channels/
POST   /api/v1/channels/
```

**Create Channel Request:**
```json
POST /api/v1/channels/
Content-Type: application/json

{
  "property": 1,
  "channel_name": "booking_com",
  "channel_type": "ota",
  "account_id": "12345",
  "api_key": "your_api_key_here",
  "api_secret": "optional_secret",
  "mapping_config": {
    "room_mappings": {
      "123": "channel_room_123",
      "124": "channel_room_124"
    }
  }
}
```

#### Get Channel Details
```
GET    /api/v1/channels/{id}/
PUT    /api/v1/channels/{id}/
DELETE /api/v1/channels/{id}/
```

### Webhook: Receive Bookings from OTA Platforms

#### Receive Booking Webhook
```
POST   /api/v1/channels/{channel_id}/bookings/
Content-Type: application/json
X-Webhook-Signature: sha256=<hmac_digest>

{
  "channel_booking_id": "BKG123456",
  "timestamp": 1645195200,
  "event": "booking_created",
  "guest_first_name": "John",
  "guest_last_name": "Smith",
  "guest_email": "john@example.com",
  "guest_phone": "+1-555-123-4567",
  "room_id": 123,
  "check_in": "2026-03-15",
  "check_out": "2026-03-20",
  "number_of_guests": 2,
  "special_requests": "high_floor",
  "total_price": 450.00,
  "currency": "USD"
}
```

**Success Response (201):**
```json
{
  "booking_id": 567,
  "status": "confirmed",
  "confirmation_number": "BKNG-567",
  "booking_created_at": "2026-02-20T10:30:00Z"
}
```

**Automatic Actions on Booking Receipt:**
- ✅ Creates booking in NEPHELE system
- ✅ Updates availability (decrements available_units)
- ✅ Sends high-priority email to all property staff
- ✅ Queues availability sync to all other connected channels
- ✅ Sets booking_source to channel name (e.g., 'booking_com')

### Availability Synchronization

#### Trigger Availability Sync
```
POST   /api/v1/channels/{channel_id}/availability/sync/

{
  "sync_type": "full_sync|incremental_sync|date_range",
  "date_from": "2026-03-15",
  "date_to": "2026-03-31"
}
```

**Response (202 Accepted):**
```json
{
  "sync_id": "celery_task_id",
  "status": "queued",
  "message": "Availability sync queued for processing"
}
```

#### Check Sync Status
```
GET    /api/v1/channels/{channel_id}/availability/status/
```

**Response:**
```json
{
  "channel_name": "Trivago",
  "property_id": 1,
  "is_active": true,
  "sync_enabled": true,
  "last_sync_at": "2026-02-20T15:30:00Z",
  "sync_status": "Success",
  "rooms_synced": 25,
  "pending_sync_count": 0,
  "last_error": null,
  "error_count": 0
}
```

### Inventory Management (Nephele)

#### Get Property Availability
```
GET    /api/v1/inventory/availability/{property_id}/?date_from=2026-03-15&date_to=2026-03-31
```

**Response:**
```json
{
  "property_id": 1,
  "date_range": {
    "from": "2026-03-15",
    "to": "2026-03-31"
  },
  "rooms": [
    {
      "room_id": 123,
      "room_number": "215",
      "room_type": "double",
      "availability_by_date": [
        {
          "date": "2026-03-15",
          "total": 1,
          "available": 1,
          "booked": 0,
          "blocked": 0,
          "overbooked": 0
        }
      ]
    }
  ]
}
```

#### Update Room Availability (Staff Override)
```
PUT    /api/v1/inventory/rooms/{room_id}/availability/

{
  "date_from": "2026-03-15",
  "date_to": "2026-03-20",
  "available_units": 2,
  "blocked_units": 0,
  "notes": "Maintenance scheduled"
}
```

#### Create Overbooking
```
POST   /api/v1/inventory/overbook/

{
  "room_id": 123,
  "date_from": "2026-03-15",
  "date_to": "2026-03-20",
  "overbook_units": 2,
  "reason": "group_booking"
}
```

#### View Sync Logs
```
GET    /api/v1/inventory/sync-log/{property_id}/?status=failed&days=7
```

## Authentication & Authorization

### API Authentication
- JWT tokens required for all endpoints (except webhook with signature)
- Use: `Authorization: Bearer <your_jwt_token>`

### Webhook Signature Verification
- Channels can sign payloads with HMAC-SHA256
- Set `api_secret` in channel configuration
- Header: `X-Webhook-Signature: sha256=<hex_digest>`
- Verification automatically handled by views

### Role-Based Access
- **Admin/Manager:** Full access to all channels and inventory
- **Staff:** View channels and availability for their property
- **Travel Agents:** Cannot access (separate access control)

## Celery Tasks

### send_channel_booking_alert
Triggered automatically when booking received from OTA platform.
- Sends email to ALL active staff at property
- Includes: guest details, room, dates, price, special requests
- Subject: "New Booking from {CHANNEL} - Room {NUMBER}, {DATES}"

### sync_availability_to_channel
Synchronizes availability to specific channel asynchronously.
- Supports full, incremental, and date-range syncs
- Implements retry logic (exponential backoff)
- Logs all attempts in AvailabilitySyncLog

### sync_availability_to_channels
Syncs availability to all active channels for a property.
- Triggered after booking creation/cancellation
- Queues individual sync_availability_to_channel tasks

## Usage Examples

### Example 1: Connect Trivago Channel

```bash
curl -X POST http://localhost:8000/api/v1/channels/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "property": 1,
    "channel_name": "trivago",
    "account_id": "trivago_hotel_123",
    "api_key": "trivago_api_key_abc123",
    "api_secret": "trivago_secret_xyz789",
    "mapping_config": {
      "room_mappings": {"123": "TR-ROOM-456"}
    }
  }'
```

### Example 2: Receive Booking from Trivago

```bash
curl -X POST http://localhost:8000/api/v1/channels/1/bookings/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: sha256=abc123def456..." \
  -d '{
    "channel_booking_id": "TRV-2026-001",
    "timestamp": 1645195200,
    "event": "booking_created",
    "guest_first_name": "John",
    "guest_last_name": "Smith",
    "guest_email": "john@example.com",
    "guest_phone": "+1-555-123-4567",
    "room_id": 123,
    "check_in": "2026-03-15",
    "check_out": "2026-03-20",
    "number_of_guests": 2,
    "special_requests": "high_floor",
    "total_price": 450.00,
    "currency": "USD"
  }'
```

### Example 3: Update Room Availability (Block for Maintenance)

```bash
curl -X PUT http://localhost:8000/api/v1/inventory/rooms/123/availability/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2026-03-15",
    "date_to": "2026-03-20",
    "available_units": 0,
    "blocked_units": 1,
    "notes": "Maintenance scheduled - plumbing work"
  }'
```

### Example 4: Trigger Availability Sync to All Channels

```bash
curl -X POST http://localhost:8000/api/v1/channels/1/availability/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sync_type": "full_sync",
    "date_from": "2026-03-15",
    "date_to": "2026-03-31"
  }'
```

## Staff Notification Email

When a booking is received from Trivago, all property staff receive:

```
From: nephele-alerts@nephele.io
To: [all staff at property]
Subject: New Booking from Trivago - Room 215, Mar 15-20

Hi,

A new booking has been received from Trivago

Booking Details:
• Guest: John Smith (john@example.com)
• Phone: +1-555-123-4567
• Room: 215 (Double Deluxe)
• Check-in: March 15, 2026 at 3:00 PM
• Check-out: March 20, 2026 at 11:00 AM
• Nights: 5
• Guests: 2 adults
• Total Price: $450.00 USD
• Special Requests: High floor, late check-in (9 PM)

[View in NEPHELE]

Best regards,
NEPHELE
```

## Admin Interface

### Django Admin
- `/admin/channels/channel/` - Manage channel configurations
- `/admin/channels/channelbooking/` - View channel booking references
- `/admin/inventory/roomavailability/` - Manage room availability
- `/admin/inventory/availabilitysynclog/` - Monitor sync logs

## Monitoring & Troubleshooting

### Check Sync Status
```bash
curl http://localhost:8000/api/v1/channels/1/availability/status/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### View Sync Logs
```bash
curl http://localhost:8000/api/v1/inventory/sync-log/1/?status=failed&days=7 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Error Handling
- Channels track error count and last error message
- Automatic retry for failed syncs (exponential backoff)
- Admin notified after 3+ consecutive failures
- Circuit breaker pauses syncs if channel API consistently fails

## Configuration

### Settings
All configuration is stored in the Django admin:
1. Navigate to Admin > Channels > Channel
2. Add new channel with platform-specific credentials
3. Configure room mappings
4. Enable/disable synchronization

### Environment Variables (Optional)
```bash
# Email notifications
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=YOUR_SENDGRID_API_KEY

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Next Steps

1. **Test Channels:** Set up test channels for Trivago and Booking.com
2. **Configure Webhooks:** Update OTA platform settings with webhook URLs
3. **Set Room Mappings:** Map NEPHELE room IDs to channel room IDs
4. **Monitor Syncs:** Watch sync logs for any issues
5. **Train Staff:** Show property staff how to use availability management

## Support

For issues or questions:
1. Check Django admin > Inventory > Availability Sync Logs
2. Review channel error messages in Channel details
3. Check application logs for Celery task errors
4. Contact development team with sync log details

---

**Document Version:** 1.0  
**Last Updated:** February 20, 2026  
**Author:** Development Team  
