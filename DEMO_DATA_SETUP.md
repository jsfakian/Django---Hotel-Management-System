# Demo Data Setup Guide

## Overview

This guide explains how to load and manage comprehensive demo data in the NEPHELE Hotel Management System for testing, demonstrations, and training purposes.

The demo data includes:
- **4 Properties** (hotels in Athens, Mykonos, Crete, and Thessaloniki)
- **14 Rooms** with various types and price points
- **8 Guests** from different countries
- **8 Bookings** with various statuses (past, current, future, cancelled)
- **4 Travel Agencies** for channel distribution testing
- **20+ Pricing History Records** for BI analysis and forecasting
- **12+ Analytics Metrics** for dashboard demonstrations

## Features Demonstrated

### 1. **Dynamic Pricing & Forecasting**
- Pricing history with seasonal variations
- Competitor pricing data
- Demand scores and occupancy rates
- ML model prediction data

### 2. **Business Intelligence (BI)**
- Executive metrics (revenue, ADR, occupancy, RevPAR)
- Operational status tracking
- Revenue trends (30-day trends)
- Year-over-year (YoY) comparisons
- Occupancy and forecasting metrics

### 3. **Booking Management**
- Multiple booking statuses (pending, confirmed, checked_in, checked_out)
- Booking sources (direct, OTA, travel agency)
- Special requests and preferences
- Guest profiles with booking history

### 4. **Travel Agency Integration**
- Agency partnerships with commission rates
- Booking attribution by agency
- Agency contact management

## Quick Start

### Option 1: Load Demo Data After Initial Setup

```bash
# 1. Start the system
make setup

# 2. In another terminal, load demo data
make load-demo-data
```

### Option 2: Fresh Setup with Demo Data

```bash
# Clean slate and load fresh demo data
make clean
make setup
make load-demo-data
```

### Option 3: Replace Existing Demo Data

```bash
# Clear old demo data and load new data
make load-demo-data-fresh
```

## Management Commands

### Load Demo Data
```bash
# Standard load (creates new records, skips existing)
python manage.py load_demo_data

# Clear existing demo data first
python manage.py load_demo_data --clear

# Specify custom fixtures directory
python manage.py load_demo_data --fixtures-dir=/path/to/fixtures
```

### Commands via Docker

```bash
# Inside container or via docker compose
docker compose exec django python manage.py load_demo_data
docker compose exec django python manage.py load_demo_data --clear
```

## Data File Structure

### Location
`HMS/fixtures/demo_data.json`

### Schema

```json
{
  "properties": [...],
  "guests": [...],
  "rooms": [...],
  "travel_agencies": [...],
  "bookings": [...],
  "pricing_history": [...],
  "analytics": [...]
}
```

### Date Handling

Demo data supports flexible date specifications:
- **Relative dates**: `"-5"` (5 days ago), `"+3"` (3 days from today)
- **Absolute dates**: `"2024-01-15"`, `"01/15/2024"`, `"15/01/2024"`

Examples:
```json
{
  "check_in_date": "-5",        // 5 days ago
  "check_out_date": "-2",        // 2 days ago
  "date_of_reservation": "+10"   // 10 days from today
}
```

## Customizing Demo Data

### 1. Edit the Fixture File
`HMS/fixtures/demo_data.json`

- Add more properties, rooms, guests, bookings
- Adjust prices, rates, and occupancy percentages
- Modify seasons and demand patterns
- Update event descriptions

### 2. Add More Bookings
Create bookings with various statuses for testing:

```json
{
  "room_number": "AP-102",
  "guest_email": "demo_guest@example.com",
  "check_in_date": "-10",
  "check_out_date": "-5",
  "date_of_reservation": "-20",
  "number_of_guests": 2,
  "status": "checked_out",
  "base_price": "220.00",
  "actual_price": "220.00",
  "booking_source": "direct_website",
  "special_requests": "High floor preferred"
}
```

### 3. Enhance Pricing History
Add more pricing records for better BI trends:

```json
{
  "room_number": "AP-102",
  "date": "-30",
  "base_price": "180.00",
  "dynamic_price": "185.00",
  "competitor_price": "188.00",
  "occupancy_rate": "45.00",
  "demand_score": "40.00",
  "bookings_count": 2,
  "season": "low"
}
```

### 4. Add Analytics Metrics
Create metrics for dashboard demonstrations:

```json
{
  "property": "Acropolis Palace",
  "metric_date": "-7",
  "total_revenue": "8450.00",
  "avg_daily_rate": "185.50",
  "occupancy_rate": "82.00",
  "revpar": "152.11",
  "booking_count": 12,
  "yoy_revenue_change": "15.50",
  "yoy_occupancy_change": "8.25"
}
```

## Demo Data Properties

### Properties Included

| Name | City | Country | Rooms | Star Rating |
|------|------|---------|-------|------------|
| Acropolis Palace | Athens | Greece | 120 | ⭐⭐⭐⭐⭐ |
| Mykonos Beachfront Resort | Mykonos | Greece | 85 | ⭐⭐⭐⭐⭐ |
| Crete Mountain Lodge | Rethymno | Greece | 60 | ⭐⭐⭐⭐ |
| Thessaloniki Harbor View | Thessaloniki | Greece | 95 | ⭐⭐⭐⭐ |

### Room Types

- **Economic**: Budget rooms (not in demo)
- **Single**: 1 guest, basic amenities
- **Double**: 2 guests, standard amenities
- **Deluxe**: 2 guests, premium amenities
- **Suite**: 4 guests, luxury amenities + living room
- **Luxury**: Top-tier suite with concierge service

### Booking Statuses

- `pending`: Awaiting confirmation
- `confirmed`: Confirmed reservation
- `checked_in`: Guest has checked in
- `checked_out`: Stay completed
- `cancelled`: Reservation cancelled
- `no_show`: Guest didn't show up

## Testing Scenarios

### Scenario 1: Peak Season Pricing
Mykonos Beachfront Resort shows:
- High occupancy (95-98%)
- Peak pricing ($475-$550)
- High demand scores (94-98)
- Year-over-year growth of 35%

### Scenario 2: Off-Season Performance
Notice the variation in:
- Lower occupancy rates (55-78%)
- Reduced pricing ($185-$250)
- Lower demand scores (52-75%)
- Different seasonal patterns

### Scenario 3: Travel Agency Bookings
Verify travel agency commission calculations:
- Mediterranean Tours: 12.5% commission
- European Discoveries: 15% commission
- Luxury Travel Concierge: 18% commission

### Scenario 4: Guest Preferences
Test guest profile tracking:
- Previous booking history
- Special requests processing
- Preference-based room selection

## Verification

### Check Loaded Data
```bash
# Via Django admin
http://localhost:8000/admin

# Via API
curl http://localhost:8000/api/v1/properties/
curl http://localhost:8000/api/v1/rooms/
curl http://localhost:8000/api/v1/bookings/
curl http://localhost:8000/api/v1/analytics/executive-metrics/
```

### Database Verification
```bash
# Access database
docker compose exec postgres psql -U hms -d hms

# Count records
SELECT COUNT(*) FROM properties_property;
SELECT COUNT(*) FROM room_room;
SELECT COUNT(*) FROM accounts_guest;
SELECT COUNT(*) FROM room_booking;
SELECT COUNT(*) FROM bookings_pricinghistory;
SELECT COUNT(*) FROM analytics.dashboard_executive_metrics;
```

## Troubleshooting

### Error: "Demo data file not found"
Ensure the file exists at: `HMS/fixtures/demo_data.json`

```bash
# Check file
ls -la HMS/fixtures/demo_data.json

# Verify JSON syntax
python -m json.tool HMS/fixtures/demo_data.json
```

### Error: "Property does not exist"
Ensure properties are created before loading rooms and bookings.
Load order is automatically: Properties → Guests → Rooms → Agencies → Bookings → Pricing → Analytics

### Error: "Guest email already exists"
Use the `--clear` flag to remove old demo data first:
```bash
make load-demo-data-fresh
```

### Partial Data Loaded
Check the output messages for specific entity counts and any error messages.

## Advanced Customization

### Create Season-Specific Data
Generate pricing data for different seasons:

```python
# Example: Winter peak season (Dec-Jan)
dates = ["2024-12-20", "2024-12-25", "2024-12-30", "2025-01-01"]
for date in dates:
    # Create high-demand, peak-season pricing
```

### Simulate Real Booking Patterns
Match actual hotel data:
- Weekend demand variations
- Holiday surges
- Last-minute bookings
- Long-stay discounts

### Generate Competitor Analysis
Track competitor pricing over time for competitive intelligence features.

## Performance Considerations

The demo data is sized for:
- **Development**: Full functionality testing
- **Demonstrations**: Comprehensive feature showcase
- **Training**: Realistic user scenarios

Current scale:
- 4 properties
- 14 rooms
- 8 guests
- 8 active bookings
- 20+ pricing records per room type
- 12+ analytics records

For production-scale testing, expand the JSON file accordingly.

## Backup & Recovery

### Backup Demo Data
```bash
# Export current demo data
docker compose exec django python manage.py dumpdata > demo_backup.json
```

### Create Snapshots
```bash
# Create database snapshot
docker compose exec postgres pg_dump hms > demo_backup.sql
```

## Documentation Files

- See [QUICK_START.md](../QUICK_START.md) for general setup
- Check [API_QUICK_REFERENCE.md](../API_QUICK_REFERENCE.md) for API examples
- Review model documentation in the respective app folders

---

**Last Updated**: February 2026
**Version**: 1.0
**Status**: Production Ready
