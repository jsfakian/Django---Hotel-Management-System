# NEPHELE Hotel Management System - Task 3 Training Data
## AI Functionality Datasets

**Generated:** February 19, 2026  
**Coverage Period:** January 1, 2022 - December 31, 2024 (24 months)  
**Data Type:** Synthetic (GDPR-compliant, business logic-validated)

---

## 📊 Overview

This directory contains comprehensive synthetic datasets generated to train and validate the core AI functionality of the NEPHELE Hotel Management System:

1. **Dynamic Pricing Algorithm** - Revenue optimization and competitive pricing
2. **Personalization/Recommendation System** - Guest preference predictions
3. **Business Intelligence & Analytics** - Performance dashboards and insights
4. **Guest Segmentation** - Customer clustering and behavior analysis

### Dataset Statistics

| Dataset | Records | Purpose | Size |
|---------|---------|---------|------|
| `bookings.csv` | 24,260 | Training dynamic pricing & recommendations | ~8 MB |
| `pricing_history.csv` | 10,960 | Daily occupancy & rate history | ~600 KB |
| `guest_preferences.csv` | 25,188 | Preference learning for recommendations | ~2.5 MB |
| `competitor_pricing.csv` | 43,738 | Market intelligence & pricing optimization | ~3.5 MB |
| `guests.csv` | 5,000 | Guest profiles & segmentation | ~400 KB |
| `rooms.csv` | 300 | Room inventory & features | ~250 KB |
| `properties.csv` | 10 | Hotel properties metadata | ~2 KB |

**Total Records:** 109,356  
**Coverage:** 10 properties, 300 rooms, 5,000 unique guests

---

## 📁 File Descriptions

### 1. **bookings.csv** - Reservation History
Core dataset for dynamic pricing and revenue analysis.

**Columns:**
- `booking_id` - Unique booking identifier
- `guest_id` - Guest reference
- `property_id` - Property reference
- `room_id` - Specific room booked
- `booking_date` - When reservation was made
- `check_in_date` - Arrival date
- `check_out_date` - Departure date
- `number_of_nights` - Length of stay
- `booking_channel` - How booked (Booking.com, Direct, etc.)
- `nightly_rate` - Price per night (EUR)
- `total_price` - Total booking price (EUR)
- `status` - Completed, Cancelled, or No-Show
- `payment_method` - Payment type used
- `guests_count` - Number of guests

**Key Features for ML:**
- **Seasonality**: Summer peak (June-Aug), Holiday surges (Dec-Jan)
- **Lead Time Effects**: Min 1-60 days advance booking, with pricing adjustments
- **Cancellation Patterns**: 5% cancellation, 2% no-show rates
- **Channel Distribution**: Mix of OTA, direct, and corporate bookings
- **Pricing Variability**: Base prices adjusted for seasonality, lead time, demand

**Use Cases:**
- Dynamic pricing model training (predict optimal price given conditions)
- Demand forecasting (predict occupancy)
- Revenue optimization (maximize total revenue)
- Guest behavior analysis (booking patterns, cancellations)

---

### 2. **pricing_history.csv** - Daily Financial & Occupancy Metrics
Time-series data for pricing optimization and forecasting.

**Columns:**
- `date` - Date of the record
- `property_id` - Hotel property
- `occupancy_rate` - Percentage of rooms occupied (0-1.0)
- `available_rooms` - Count of empty rooms
- `occupied_rooms` - Count of occupied rooms
- `average_nightly_rate` - Mean price per night (EUR)
- `day_of_week` - Monday-Sunday
- `season` - Winter, Spring, Summer, Fall
- `is_holiday` - Boolean flag for holidays

**Key Patterns:**
- **Occupancy Seasonality**: ~65% winter, ~85% summer
- **Weekend Premium**: +15% occupancy on weekends
- **Holiday Spikes**: +30% occupancy during Greek holidays
- **Pricing Multipliers**: 1.4x summer, 0.85x off-season

**Use Cases:**
- Time-series forecasting (predict future occupancy)
- Seasonal trend analysis
- Optimal pricing schedule generation
- Business intelligence dashboards
- Demand planning and inventory management

---

### 3. **guest_preferences.csv** - Individual Guest Amenity Preferences
Foundation for the recommendation system and personalization engine.

**Columns:**
- `guest_id` - Guest reference
- `room_id` - Room rated/preferred
- `room_type` - Room category (Standard, Deluxe, Suite, Family, Penthouse)
- `preferred_floor` - Desired floor (1-5)
- `wants_breakfast` - Boolean (breakfast preference)
- `wants_parking` - Boolean (parking preference)
- `needs_accessibility` - Boolean (accessibility requirement)
- `preferred_view` - View type preference
- `min_room_size_sqm` - Minimum acceptable room size
- `willing_to_pay_extra` - Willingness for upgrades
- `rating` - Satisfaction rating (3-5 stars)

**Profile Data:**
- **25,188 preference records** from 5,000 guests
- **Average 5 preferences per guest** (training signal strength)
- **Weighted ratings distribution** (skewed towards 5-star satisfaction)

**Use Cases:**
- Content-based filtering (room similarity recommendations)
- Collaborative filtering (find similar guests)
- Upsell opportunity identification (high-value, willing to pay)
- Accessibility compliance tracking
- Guest satisfaction insights

---

### 4. **competitor_pricing.csv** - Market Intelligence Data
Competitor benchmarking and market position analysis.

**Columns:**
- `date` - Date of price snapshot
- `property_id` - Reference hotel
- `competitor_id` - Competitor identifier (COMP_1, COMP_2, etc.)
- `competitor_name` - Competitor hotel name
- `competitor_price` - Competitor's nightly rate (EUR)
- `competitor_available_rooms` - Inventory at that date
- `competitor_rating` - Guest satisfaction score (3-5)

**Market Insights:**
- **3-5 competitors** tracked per property
- **Daily pricing snapshots** (1,095 dates × 10 properties)
- **Price distribution**: Mean ~€100, StdDev ~€30
- **Rating alignment**: 3.5-4.5 star average

**Use Cases:**
- Price elasticity analysis (price sensitivity estimation)
- Competitive positioning strategies
- Market share tracking
- Price adjustment algorithms
- Demand forecasting (market saturation indicators)

---

### 5. **guests.csv** - Guest Master Data
Customer profiles for segmentation and personalization.

**Columns:**
- `guest_id` - Unique identifier
- `first_name` - Guest first name
- `last_name` - Guest surname
- `email` - Contact email
- `customer_type` - Business, Leisure, Family, Couple, Solo (25% business, 35% leisure)
- `origin_country` - Home country (10 countries represented)
- `preferred_room_type` - Room category preference
- `loyalty_member` - Boolean (loyalty program participation, 30% enrolled)
- `registered_date` - Account creation date
- `total_stays` - Historical stay count
- `average_rating` - Guest satisfaction score

**Segmentation Data:**
- **5,000 unique guests** (realistic sample size)
- **Geographic diversity**: Germany, UK, China, USA, Italy, etc.
- **Loyalty distribution**: 30% loyalty members
- **Rating distribution**: Mean 4.2/5.0, StdDev 0.5

**Use Cases:**
- Customer segmentation (RFM analysis - Recency, Frequency, Monetary)
- Personalization targeting
- Churn prediction
- Lifetime value estimation
- Marketing campaign targeting
- VIP/loyalty tier identification

---

### 6. **rooms.csv** - Room Inventory & Features
Product master data for recommendation and pricing systems.

**Columns:**
- `room_id` - Unique identifier (PROP001_R0001 format)
- `property_id` - Property reference
- `room_number` - Room number in property
- `room_type` - Category (Standard 35%, Deluxe 35%, Suite 15%, Family 10%, Penthouse 5%)
- `floor` - Building floor (1-5)
- `capacity` - Guest capacity (1-4 people)
- `view_type` - View category (City, Sea, Mountain, Garden, Standard)
- `size_sqm` - Room size (20-100 sqm)
- `base_price_per_night` - Base rate in EUR
- `amenities` - Pipe-separated amenity list (WiFi, AC, Breakfast, Parking, Pool, Gym, Spa, Balcony, Mini Bar, Safe, Desk, Bathrobe, Hairdryer, Iron, TV)
- `last_renovation` - Year of last renovation

**Inventory Profile:**
- **300 rooms** across 10 properties
- **30 rooms per property** (realistic boutique/mid-range hotel)
- **13 amenity types** with varied availability
- **Price range**: €50-500 per night base rate

**Use Cases:**
- Room similarity calculations (for recommendations)
- Feature engineering (amenity-based pricing)
- Inventory availability tracking
- Room quality assessment
- Maintenance scheduling
- Upgrade suggestions

---

### 7. **properties.csv** - Hotel Properties Metadata
Master data for multi-property management.

**Columns:**
- `property_id` - Unique identifier
- `name` - Hotel name
- `city` - Location city
- `country` - Country (Greece)
- `star_rating` - Classification (3, 4, or 5 stars)
- `total_rooms` - Room count
- `property_type` - Category (Luxury Resort, Boutique, Business, Beach Resort)
- `founded_year` - Establishment year
- `manager_email` - Contact email

**Property Distribution:**
- **10 properties** across popular Greek cities (Athens, Crete, Mykonos, Santorini, etc.)
- **Star rating mix**: 30% 3-star, 50% 4-star, 20% 5-star
- **Property types**: Diverse (4 types represented)

**Use Cases:**
- Multi-property aggregation and comparison
- Benchmarking across locations
- Portfolio performance analysis
- Management hierarchy

---

## 🔬 AI Model Training Guide

### Dynamic Pricing Model

**Objective:** Predict optimal room price given conditions

**Features to Use:**
```python
temporal_features = ['day_of_week', 'season', 'month', 'is_holiday', 'advance_booking_days']
demand_features = ['occupancy_rate', 'occupied_rooms', 'available_rooms', 'date_within_season']
competitor_features = ['avg_competitor_price', 'price_gap', 'competitor_available_rooms']
guest_features = ['customer_type', 'origin_country', 'loyalty_member']
room_features = ['room_type', 'size_sqm', 'view_type', 'amenity_count']
```

**Target Variable:** `nightly_rate` (continuous, EUR)

**Algorithm Recommendations:**
1. **Gradient Boosting** (XGBoost, LightGBM) - Primary choice
2. **Random Forest** - Good baseline
3. **Neural Networks** - For feature interaction modeling
4. **Ensemble** - Combine models for robustness

**Data Preparation:**
```python
# Use 70% of bookings for training
# Include both seasonal patterns (24 months ensures coverage)
# Normalize prices by property and room type
# Handle multi-collinearity in competitor features
```

**Expected Performance:**
- RMSE: €15-30 per night (75-85% accuracy)
- R² Score: 0.75-0.85
- MAE: €8-15 per night

---

### Recommendation System

**Objective:** Recommend rooms to guests

**Data Sources:**
- Primary: `guest_preferences.csv` (25,188 preference records)
- Supporting: `bookings.csv` (implicit feedback)
- Features: `rooms.csv` features

**Approaches:**

**1. Content-Based Filtering:**
```python
# Features: room_type, floor, view_type, amenities, capacity, size_sqm
# Algorithm: Cosine similarity on normalized feature vectors
# For each guest, find rooms most similar to their preferences
```

**2. Collaborative Filtering:**
```python
# Matrix: Guests × Rooms (ratings from preferences)
# Missing values: Implicit feedback from bookings
# Algorithms: SVD, NMF, KNN
# Better for cross-property recommendations
```

**3. Hybrid (Recommended):**
```python
score = 0.4 * content_similarity + 0.4 * collaborative_score + 0.2 * business_score
# business_score: margin optimization, high-value upsells
```

**Evaluation Metrics:**
- Precision@5: >40% (of top 5, % actually chosen)
- Recall@5: >25% (of actual choices, % in top 5)
- NDCG: Normalized Discounted Cumulative Gain
- Coverage: >80% of inventory recommendable

---

### Business Intelligence & Analytics

**Key Dashboards to Build:**

**1. Revenue Analysis**
```python
# Metrics: ADR (Average Daily Rate), RevPAR (Revenue per Available Room)
# Dimensions: By date, property, room_type, customer_type
# Data: pricing_history.csv, bookings.csv
```

**2. Occupancy Trends**
```python
# Metrics: Occupancy %, Available rooms, Booking velocity
# Dimensions: By season, day_of_week, property
# Data: pricing_history.csv
```

**3. Guest Segmentation**
```python
# RFM Analysis: Recency, Frequency, Monetary
# Dimensions: customer_type, origin_country, loyalty_status
# Data: guests.csv, bookings.csv
```

**4. Forecasting**
```python
# Time series: Prophet, ARIMA, or ML-based
# Variables: Occupancy, ADR, Bookings
# Data: pricing_history.csv (daily granularity)
```

---

## 🔄 Data Workflow Integration

### For Django Models

**Recommended Django app structure:**

```
hms/
├── ml_models/
│   ├── pricing/
│   │   ├── models.py (ML model classes)
│   │   ├── training.py (Dataset loading & training)
│   │   └── prediction.py (Inference API)
│   ├── recommendations/
│   │   ├── models.py
│   │   ├── algorithms.py
│   │   └── cache.py
│   └── analytics/
│       ├── dashboards.py
│       └── reports.py
├── data_pipeline/
│   ├── importers.py (CSV → Database)
│   ├── feature_engineering.py
│   └── data_validation.py
```

### CSV Import Workflow

```python
# 1. Load CSV files
import pandas as pd

properties = pd.read_csv('task3-data/properties.csv')
rooms = pd.read_csv('task3-data/rooms.csv')
guests = pd.read_csv('task3-data/guests.csv')
bookings = pd.read_csv('task3-data/bookings.csv')
pricing = pd.read_csv('task3-data/pricing_history.csv')
preferences = pd.read_csv('task3-data/guest_preferences.csv')
competitors = pd.read_csv('task3-data/competitor_pricing.csv')

# 2. Data validation & cleaning
# - Check for nulls, duplicates
# - Validate date ranges
# - Ensure referential integrity

# 3. Feature engineering
# - Extract temporal features (season, day_of_week, etc.)
# - Calculate lead time from booking_date vs check_in_date
# - Aggregate competitor pricing by date & property

# 4. Train models
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 5. Monitor predictions vs actuals
# Update models periodically as new booking data arrives
```

---

## 📈 Data Quality & Validation

### Synthetic Data Validation Checks

✅ **Referential Integrity:**
- All booking.guest_id exist in guests.csv
- All booking.room_id exist in rooms.csv
- All room.property_id exist in properties.csv

✅ **Business Logic:**
- Occupancy rate (0-1.0 range)
- Nightly rates > 0
- Check-out > check-in dates
- Seasonal pricing multipliers applied correctly

✅ **Statistical Properties:**
- Occupancy distribution: Beta(7,3) (realistic peak+off-season)
- Price distribution: Lognormal-like with seasonality
- Cancellation rate: ~5% (typical industry standard)
- Lead time: Exponential distribution (more last-minute bookings)

✅ **Coverage:**
- 24 months of data (seasonality capture)
- 10 properties (portfolio scaling)
- 5,000 unique guests (sufficient sample)
- 300 rooms (diverse room types/prices)
- 40+ competitors tracked

---

## 🚀 Next Steps

### Phase 1: Immediate (Week 1)
1. ✅ Generate synthetic datasets (COMPLETED)
2. Load data into development database
3. Perform exploratory data analysis (EDA)
4. Document data dictionary in Django

### Phase 2: Model Development (Weeks 2-4)
1. Create dynamic pricing baseline model
2. Implement content-based recommendation engine
3. Build BI dashboards
4. Validate model performance

### Phase 3: Integration (Weeks 5-8)
1. Integrate pricing API into booking system
2. Deploy recommendation widget on booking page
3. Create admin analytics dashboards
4. Set up monitoring & retraining pipeline

---

## 📝 Data Dictionary

### Categorical Variables
- **customer_type**: [Business, Leisure, Family, Couple, Solo Travel]
- **room_type**: [Standard, Deluxe, Suite, Family, Penthouse]
- **view_type**: [City View, Sea View, Mountain View, Garden View, Standard]
- **booking_channel**: [Direct Website, Booking.com, Airbnb, Expedia, Hotel.com, Travel Agency, Corporate]
- **origin_country**: [Greece, Germany, UK, France, USA, China, Italy, Spain, Belgium, Netherlands]
- **status**: [Completed, Cancelled, No-Show]
- **payment_method**: [Credit Card, PayPal, Bank Transfer, Cash]
- **season**: [Winter, Spring, Summer, Fall]
- **day_of_week**: [Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]

### Numeric Ranges
- **star_rating**: 3-5
- **occupancy_rate**: 0.0-1.0
- **capacity**: 1-4 guests
- **size_sqm**: 20-100
- **base_price_per_night**: €50-€500
- **nightly_rate**: €30-€1,200
- **total_stays**: 1-30+
- **average_rating**: 1.0-5.0 (guest ratings)

---

## 📞 Support & Documentation

For integration questions, refer to:
- [DELIVERABLES-Task3-ResearchCompletion.md](../DELIVERABLES-Task3-ResearchCompletion.md) - Full research documentation
- [generate_synthetic_data.py](./generate_synthetic_data.py) - Data generation source code
- Django apps: `ml_models/`, `bookings/`, `properties/`

---

**Generated:** February 19, 2026  
**Last Updated:** 2026-02-19  
**Status:** Production-Ready for Development Phase
