#!/usr/bin/env bash
# Task 3 Real Data Acquisition Guide
# Download and prepare free public datasets for NEPHELE AI training

cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║         NEPHELE TASK 3 - REAL DATA ACQUISITION GUIDE                         ║
║            Free Public Datasets for Hotel Management AI Training             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📊 AVAILABLE FREE REAL DATASETS
═══════════════════════════════════════════════════════════════════════════════

The following real, freely-available datasets have been identified for your project:

┌─ TIER 1: HIGHLY RECOMMENDED (Complete & production-ready)
│
├─ 1. Hotel Booking Demand (Kaggle)
│  ├─ Records: 119,390 bookings with 32 fields
│  ├─ Time: July 2015 - August 2017
│  ├─ Features: Cancellations, ADR, stay length, demographics, channels
│  ├─ License: CC BY 4.0 (Free, Public)
│  ├─ Size: 16.86 MB
│  ├─ URL: https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand
│  ├─ Direct CSV: 
│  │  - hotel_bookings.csv (main file)
│  └─ Best For: Predictive modeling, cancellation prediction, revenue analysis
│
├─ 2. Inside Airbnb - Multiple Cities (60+ locations)
│  ├─ Records: Thousands of listings per city, quarterly updates
│  ├─ Time: Updated quarterly (latest Dec 2025)
│  ├─ Features: Prices, availability, reviews, ratings, amenities
│  ├─ License: CC BY 4.0 (Free, Public)
│  ├─ Available Cities: NYC, London, Paris, Barcelona, Tokyo, Amsterdam, Sydney, etc.
│  ├─ URL: https://insideairbnb.com/get-the-data/
│  ├─ Files per city:
│  │  - listings.csv (10-100 MB depending on city)
│  │  - calendar.csv (availability & price by date)
│  │  - reviews.csv (review history)
│  └─ Best For: Price modeling, demand patterns, market analysis
│
├─ 3. TripAdvisor Hotel Reviews
│  ├─ Records: 878,561 reviews across 4,333 hotels
│  ├─ Features: Review text, ratings, hotel metadata, dates
│  ├─ License: ODbL 1.0 (Open, Free)
│  ├─ Size: 2.17 GB
│  ├─ URL: https://www.kaggle.com/datasets/joebeachcapital/hotel-reviews
│  └─ Best For: Sentiment analysis, review classification, rating prediction
│
└─ TIER 2: SUPPLEMENTARY (Specialized data)
   │
   ├─ 4. World Bank Tourism Statistics (API + Downloads)
   │  └─ Global indicators, 200+ countries, 1960-2024+ data
   │     URL: https://data.worldbank.org/
   │     Best For: Macro-level forecasting
   │
   ├─ 5. Hostelworld Reviews (100K+ reviews)
   │  └─ Budget accommodation focus
   │     URL: https://www.kaggle.com/datasets/felipejardimf/hotel-reviews-hostelworld
   │
   └─ 6. OpenStreetMap Hotels (Global, millions of records via API)
      └─ Geographic data and amenities
         URL: https://overpass-api.de/

═══════════════════════════════════════════════════════════════════════════════

🔧 HOW TO DOWNLOAD & PREPARE
═══════════════════════════════════════════════════════════════════════════════

OPTION A: Manual Download (Easiest for Kaggle datasets)
─────────────────────────────────────────────────────────

1. Create API Token for Kaggle:
   a) Go to: https://www.kaggle.com/account
   b) Click "Create New Token"
   c) Download kaggle.json to ~/.kaggle/kaggle.json
   d) Run: chmod 600 ~/.kaggle/kaggle.json

2. Install Kaggle CLI:
   pip3 install kaggle

3. Download Hotel Booking Demand:
   kaggle datasets download -d jessemostipak/hotel-booking-demand
   unzip hotel-booking-demand.zip -d task3-data/real_data/

4. Download Hostelworld:
   kaggle datasets download -d felipejardimf/hotel-reviews-hostelworld
   unzip hotel-reviews-hostelworld.zip -d task3-data/real_data/

─────────────────────────────────────────────────────────

OPTION B: Direct Download (Manual)
─────────────────────────────────────────────────────────

1. Hotel Booking Demand:
   - Visit: https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand
   - Click "Download" button (requires Kaggle login)
   - Extract: unzip hotel-booking-demand.zip -d task3-data/real_data/

2. Inside Airbnb (Pick any city):
   - Visit: https://insideairbnb.com/get-the-data/
   - Select city (e.g., New York City)
   - Download CSV files (listings, calendar, reviews)
   - Put in: task3-data/real_data/airbnb_[CITY]/

3. TripAdvisor Reviews:
   - Visit: https://www.kaggle.com/datasets/joebeachcapital/hotel-reviews
   - Download (large, 2.17 GB)
   - Extract to: task3-data/real_data/tripadvisor/

─────────────────────────────────────────────────────────

OPTION C: Automated Script (Recommended)
─────────────────────────────────────────────────────────

See: download_real_data.py in this directory
Usage:
    python3 task3-data/download_real_data.py --dataset booking --dataset airbnb

═══════════════════════════════════════════════════════════════════════════════

📁 DIRECTORY STRUCTURE (After downloads)
═══════════════════════════════════════════════════════════════════════════════

task3-data/
├── synthetic_data/          (Our generated synthetic datasets)
│   ├── bookings.csv
│   ├── guest_preferences.csv
│   └── ... (other CSV files)
│
└── real_data/               (Real public datasets - you download these)
    ├── kaggle_booking_demand/
    │   ├── hotel_bookings.csv (119,390 records)
    │   ├── README.md
    │   └── ...
    │
    ├── airbnb_combined/
    │   ├── listings_consolidated.csv
    │   ├── calendar_consolidated.csv
    │   ├── reviews_consolidated.csv
    │   └── [city_specific_folders]/
    │
    ├── tripadvisor/
    │   ├── reviews.csv (878K+ records)
    │   └── hotels.csv (4,333 hotels)
    │
    ├── world_bank_tourism/
    │   └── tourism_indicators.csv
    │
    └── README_REAL_DATA.md   (Merge instructions)

═══════════════════════════════════════════════════════════════════════════════

🔄 DATA PREPARATION & MERGING
═══════════════════════════════════════════════════════════════════════════════

Once you download real datasets, use our consolidation script:

    python3 task3-data/merge_real_data.py \\
        --source task3-data/real_data/ \\
        --output task3-data/consolidated_real_data.csv

This will:
1. Load Hotel Booking Demand data
2. Extract Airbnb pricing dynamics (if available)
3. Merge review data (if available)
4. Standardize column names
5. Handle date normalization
6. Create unified training dataset

═══════════════════════════════════════════════════════════════════════════════

📊 DATASET COMPARISON: Real vs Synthetic
═══════════════════════════════════════════════════════════════════════════════

METRIC                  | SYNTHETIC                | REAL (RECOMMENDED)
────────────────────────┼──────────────────────────┼─────────────────────
Booking Records         | 24,260 (Greek hotels)    | 119,390 (Europe/Global)
Time Period             | 24 months (2022-2024)    | 32+ months (2015-2017+)
Hotel Types             | All types mixed          | Split: City + Resort
Price Range             | €30-€1,200               | €0-€5,000+
Guest Demographics      | 10 countries             | 180+ countries
Cancellation Data       | Synthetic pattern        | Real cancellations
Review Data             | None                     | 878K+ real reviews
Amenity Details         | Generic                  | Detailed lists
Geographic Data         | No coordinates           | GPS available (Airbnb)
Reviews & Ratings       | None                     | Real user feedback

RECOMMENDATION: Use BOTH!
- Start with synthetic data for quick model development
- Validate with real data for production deployment
- Combine both for robust training (augmentation strategy)

═══════════════════════════════════════════════════════════════════════════════

✅ QUICK REFERENCE: What to Download First
═══════════════════════════════════════════════════════════════════════════════

FOR DYNAMIC PRICING:
  ✓ Hotel Booking Demand (essential) - ADR, cancellations, lead time
  ✓ Inside Airbnb NYC (recommended) - Real pricing time series
  ✓ World Bank Tourism (useful) - Seasonal demand indicators

FOR RECOMMENDATIONS:
  ✓ TripAdvisor Reviews - Review text, ratings, hotel metadata
  ✓ Inside Airbnb - Listing descriptions, amenities
  ✓ Hostelworld - Additional review data

FOR BI & ANALYTICS:
  ✓ Hotel Booking Demand - Complete booking history
  ✓ Inside Airbnb - Availability and booking velocity
  ✓ World Bank - Macro trends

FOR COMPLETE TRAINING:
  → Download ALL Tier 1 datasets + World Bank

═══════════════════════════════════════════════════════════════════════════════

🔗 DIRECT DOWNLOAD LINKS
═══════════════════════════════════════════════════════════════════════════════

1. Hotel Booking Demand
   Kaggle: https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand

2. Inside Airbnb (Choose cities)
   Main: https://insideairbnb.com/get-the-data/
   NYC: http://data.insideairbnb.com/united-states/ny/new-york-city/2025-12-04/data/listings.csv.gz
   London: http://data.insideairbnb.com/united-kingdom/england/london/2025-09-14/data/listings.csv.gz
   Paris: http://data.insideairbnb.com/france/île-de-france/paris/2025-09-12/data/listings.csv.gz

3. TripAdvisor Reviews
   Kaggle: https://www.kaggle.com/datasets/joebeachcapital/hotel-reviews

4. World Bank Tourism Data
   API: https://api.worldbank.org/
   Data: https://data.worldbank.org/topic/19

5. Hostelworld Reviews
   Kaggle: https://www.kaggle.com/datasets/felipejardimf/hotel-reviews-hostelworld

═══════════════════════════════════════════════════════════════════════════════

🎓 RECOMMENDED WORKFLOW
═══════════════════════════════════════════════════════════════════════════════

Phase 1: Development (Week 1-2)
  → Use synthetic data (already have it)
  → Fast iteration, no download needed

Phase 2: Validation (Week 3)
  → Download Hotel Booking Demand
  → Compare synthetic vs real patterns
  → Validate model performance

Phase 3: Production (Week 4+)
  → Download Inside Airbnb + TripAdvisor
  → Merge all data sources
  → Train final production models
  → Deploy with real data validation

═══════════════════════════════════════════════════════════════════════════════

📝 NOTES
═══════════════════════════════════════════════════════════════════════════════

• All datasets listed are 100% free and publicly available
• Kaggle requires free account (no payment needed)
• Inside Airbnb is completely open, no login required
• TripAdvisor is licensed under ODbL (open data)
• All can be used for commercial AI/ML training
• Check individual licenses for attribution requirements

═══════════════════════════════════════════════════════════════════════════════
EOF

echo ""
echo "For automated download, see: download_real_data.py"
echo "For data consolidation, see: merge_real_data.py"
