# Demo Data - Quick Reference

## Three Simple Commands

```bash
# 1. After initial setup
make load-demo-data

# 2. Replace all demo data
make load-demo-data-fresh

# 3. Full fresh deployment
make clean && make setup && make load-demo-data
```

## What Gets Loaded

| Entity | Count | Details |
|--------|-------|---------|
| Properties | 4 | Hotels in Athens, Mykonos, Crete, Thessaloniki |
| Rooms | 14 | Single, double, suite, deluxe, luxury rooms |
| Guests | 8 | International guests from 7 countries |
| Bookings | 8 | Mixed statuses: past, current, future, confirmed |
| Pricing Records | 15 | Dynamic pricing with seasonal variations |
| Analytics Metrics | 12 | Executive dashboards, trends, YoY comparisons |
| Travel Agencies | 4 | Partners with commission rates 12.5%-18% |

## Features Demonstrated

✅ **Bookings**: Past, current, confirmed, pending statuses  
✅ **BI/Analytics**: Revenue, ADR, RevPAR, occupancy, trends, YoY growth  
✅ **Dynamic Pricing**: Room prices from €90-€700, demand scoring  
✅ **Forecasting**: 30-day trends, seasonal patterns, demand predictions  
✅ **Travel Agencies**: Booking attribution, commission management  
✅ **Guest Profiles**: International guests, booking history, preferences  

## Verify It Worked

```bash
# Via Admin Interface
http://localhost:8000/admin/

# Via API
curl http://localhost:8000/api/v1/properties/
curl http://localhost:8000/api/v1/bookings/
curl http://localhost:8000/api/v1/analytics/executive-metrics/
```

## File Locations

| File | Purpose |
|------|---------|
| `HMS/fixtures/demo_data.json` | Data storage (reusable, version-controllable) |
| `HMS/bookings/management/commands/load_demo_data.py` | Loading command |
| `DEMO_DATA_SETUP.md` | Comprehensive guide |
| `DEMO_DATA_IMPLEMENTATION.md` | Implementation details |
| `Makefile` | Updated with 3 new targets |

## Customization

Edit `HMS/fixtures/demo_data.json` and add:
- More properties, rooms, guests
- Additional bookings with different statuses
- More pricing history for longer trends
- New travel agencies

Then reload: `make load-demo-data-fresh`

## Troubleshooting

```bash
# Validate JSON syntax
python -m json.tool HMS/fixtures/demo_data.json

# Check file exists
ls -la HMS/fixtures/demo_data.json

# View full logs
docker compose exec -T django python manage.py load_demo_data --clear
```

## Demo Data Properties

### Acropolis Palace (Athens)
- ⭐⭐⭐⭐⭐ 5-star, 120 rooms
- €120-€500/night
- Premium location, city views

### Mykonos Beachfront Resort (Mykonos)
- ⭐⭐⭐⭐⭐ 5-star, 85 rooms  
- €250-€700/night
- Peak season pricing, 98% occupancy
- 35% YoY revenue growth

### Crete Mountain Lodge (Rethymno)
- ⭐⭐⭐⭐ 4-star, 60 rooms
- €100-€250/night
- Lower price point, medium demand

### Thessaloniki Harbor View (Thessaloniki)
- ⭐⭐⭐⭐ 4-star, 95 rooms
- €90-€250/night
- Business location, consistent demand

## For Demonstrations

Perfect for showcasing:
- 📊 BI dashboards (revenue trends, occupancy analysis)
- 💰 Pricing strategies (seasonal, competitor-aware)
- 📈 Forecasting accuracy (30-day trends)
- 📅 Booking management (multiple statuses)
- 🌍 Multi-property operations
- 🤝 Travel agency integration

## Quick Links

- [Full Setup Guide](DEMO_DATA_SETUP.md)
- [Implementation Details](DEMO_DATA_IMPLEMENTATION.md)
- [API Reference](API_QUICK_REFERENCE.md)
- [Admin Interface](http://localhost:8000/admin)

---

**Ready to demo!** Run `make load-demo-data` and start showcasing nephele's features.
