# Phase 1: API Testing Quick Start

## Quick Reference - Test the Pricing APIs

The backend is ready! Here's what you can test:

### 1. Get AI Price Recommendation
```bash
# Get pricing recommendation for a room on a specific date
curl -X GET "http://localhost:8000/api/v1/bookings/pricing/predict/?room_id=1&date=2026-03-15&occupancy_rate=75&season=peak"

# Expected Response (200 OK):
{
  "room_id": 1,
  "room_number": "101",
  "date": "2026-03-15",
  "ensemble_prediction": 125.50,
  "confidence": 0.92,
  "all_predictions": {
    "ensemble": 125.50,
    "gradient_boosting": 124.20,
    "neural_network": 126.80,
    "linear_regression": 122.50,
    "seasonal_pricing": 123.00
  },
  "factors": {
    "base_price": 100,
    "occupancy_impact_dollars": 15.00,
    "occupancy_impact_percent": 15.00,
    "season_impact_dollars": 30.00,
    "season_impact_percent": 30.00,
    "demand_impact_dollars": 10.00,
    "demand_impact_percent": 10.00,
    "competitor_impact_dollars": -5.00,
    "competitor_impact_percent": -5.00,
    "total_impact_dollars": 50.00
  },
  "competitor_price": 115.00,
  "market_range": {
    "min": 100,
    "max": 135,
    "average": 120
  }
}
```

### 2. Get 30-Day Pricing History
```bash
curl -X GET "http://localhost:8000/api/v1/bookings/pricing/history/?room_id=1&days=30"

# Expected Response (200 OK):
{
  "room_id": 1,
  "room_number": "101",
  "date_range": {
    "from": "2026-01-20",
    "to": "2026-02-20"
  },
  "history": [
    {
      "date": "2026-02-20",
      "base_price": 100,
      "dynamic_price": 125,
      "competitor_price": 115,
      "occupancy_rate": 75.00,
      "demand_score": 85.00,
      "season": "peak"
    },
    ...
  ],
  "statistics": {
    "count": 30,
    "min": 108,
    "max": 139,
    "average": 121.50,
    "std_dev": 7.50
  }
}
```

### 3. What-If Scenario Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/bookings/pricing/scenario/" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "date": "2026-03-15",
    "occupancy_rate": 95,
    "season": "peak",
    "competitor_price": 130
  }'

# Expected Response (200 OK):
{
  ...all fields from predict...
  "price_change": 17.00,
  "price_change_percent": 15.50,
  "revenue_impact_per_night": 17.00,
  "revenue_impact_per_3night_stay": 51.00
}
```

### 4. Available Models Info
```bash
curl -X GET "http://localhost:8000/api/v1/bookings/pricing/models/"

# Expected Response (200 OK):
{
  "models": [
    {
      "name": "ensemble",
      "accuracy": 0.88,
      "status": "available"
    },
    {
      "name": "gradient_boosting",
      "accuracy": 0.87,
      "status": "available"
    },
    {
      "name": "neural_network",
      "accuracy": 0.76,
      "status": "available"
    },
    {
      "name": "linear_regression",
      "accuracy": 0.71,
      "status": "available"
    },
    {
      "name": "seasonal_pricing",
      "accuracy": 0.74,
      "status": "available"
    }
  ],
  "default_model": "ensemble",
  "last_training": "2026-02-20",
  "model_version": "v2.3"
}
```

## Error Handling

### Invalid Room ID
```bash
curl -X GET "http://localhost:8000/api/v1/bookings/pricing/predict/?room_id=999&date=2026-03-15"

# Response (404 Not Found):
{"error": "Room 999 not found"}
```

### Invalid Date Format
```bash
curl -X GET "http://localhost:8000/api/v1/bookings/pricing/predict/?room_id=1&date=invalid"

# Response (400 Bad Request):
{"error": "Invalid date format: invalid. Use YYYY-MM-DD"}
```

### Missing Required Parameters
```bash
curl -X GET "http://localhost:8000/api/v1/bookings/pricing/predict/?room_id=1"

# Response (400 Bad Request):
{"error": "date parameter required (YYYY-MM-DD)"}
```

## Using Postman

1. **Import Collection:**
   - Create new HTTP Request
   - Method: GET
   - URL: http://localhost:8000/api/v1/bookings/pricing/predict/
   - Params:
     - room_id: 1
     - date: 2026-03-15
     - occupancy_rate: 75 (optional)
     - season: peak (optional)
   - Click Send

2. **Test POST (Scenario Analysis):**
   - Method: POST
   - URL: http://localhost:8000/api/v1/bookings/pricing/scenario/
   - Headers: Content-Type: application/json
   - Body (raw JSON):
   ```json
   {
     "room_id": 1,
     "date": "2026-03-15",
     "occupancy_rate": 95,
     "season": "peak",
     "competitor_price": 130
   }
   ```

## What the Data Means

### Ensemble Prediction
- The **recommended price** from all 5 models combined
- Use this as the starting point for pricing decisions
- Range: Usually ±10% of base price

### Confidence Score
- **0.92** = 92% confidence in prediction
- Based on historical pricing data consistency
- Values range 0.0 (no confidence) to 1.0 (maximum confidence)

### Factors Breakdown
- **Occupancy Impact:** How room bookings affect price
  - 75% occupancy = +15% upcharge
  - 100% occupancy = +20% upcharge
  
- **Seasonal Impact:** Season multiplier
  - Low season: 0.90x (10% discount)
  - Peak season: 1.35x (35% premium)
  
- **Demand Impact:** Recent booking activity (last 7 days)
  - More bookings = higher demand = higher price
  
- **Competitor Impact:** Market positioning
  - If competitors higher: Move up to capture value
  - If competitors lower: Discount to stay competitive

### Market Range
- **min:** Lowest price in market (last 30 days)
- **max:** Highest price in market (last 30 days)
- **average:** Your typical price

## Database Fields Used

**PricingHistory Table:**
- base_price (base nightly rate)
- dynamic_price (AI recommended)
- competitor_price (market comparison)
- occupancy_rate (0-100%)
- demand_score (0-100)
- season (qualitative: low/medium/high/peak)
- confidence_score (0-1)
- model_version (which model version)

**New Fields (Just Added):**
- ensemble_prediction
- gradient_boosting_prediction
- neural_network_prediction
- linear_regression_prediction
- occupancy_impact_percentage
- seasonal_impact_percentage
- demand_impact_percentage
- competitor_impact_percentage
- ai_recommended_price
- price_override_reason
- override_by_user (FK to User)

## Next: Frontend Components

These APIs power the frontend UI components that users will see:

1. **Pricing Status Card** - Shows current price + AI recommendation
2. **Model Comparison Card** - Shows all 5 models ranked by confidence
3. **Pricing Factors Chart** - Visual breakdown of what influences price
4. **Competitor Analysis** - Market positioning widget
5. **Historical Trend** - 30-day price chart
6. **Price Decision Form** - Accept/override UI
7. **Scenario Analyzer** - What-if calculator
8. **Audit Trail** - History of price changes

---

## Ready to Build Frontend?

All API endpoints are ready for frontend integration! 

Next steps:
1. ✅ Backend API complete (done!)
2. ⬜ Vue.js components (Phase 2)
3. ⬜ Template integration (Phase 2)
4. ⬜ Celery automation (Phase 3)
5. ⬜ Admin features (Phase 3)

See: **PHASE1_COMPLETION_SUMMARY.md** for full details!
