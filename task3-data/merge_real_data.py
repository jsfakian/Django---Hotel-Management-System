#!/usr/bin/env python3
"""
NEPHELE Task 3 - Real Data Consolidation & Merger
Merge downloaded real datasets with synthetic data for comprehensive training

This script:
1. Loads Hotel Booking Demand data
2. Extracts pricing patterns from Airbnb (if available)
3. Consolidates booking records from multiple sources
4. Standardizes column names
5. Creates unified training dataset

Usage:
  python3 merge_real_data.py --booking task3-data/real_data/kaggle_booking_demand/ --output merged_bookings.csv
  python3 merge_real_data.py --all --output consolidated_real_data.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse
import warnings

warnings.filterwarnings('ignore')


class RealDataConsolidator:
    """Consolidate and standardize real datasets for training"""
    
    def __init__(self, output_dir="."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def load_booking_demand(self, data_path):
        """Load and process Hotel Booking Demand dataset"""
        print("\n📖 Loading Hotel Booking Demand...")
        
        csv_path = Path(data_path) / "hotel_bookings.csv"
        if not csv_path.exists():
            print(f"   ❌ Not found: {csv_path}")
            return None
        
        try:
            df = pd.read_csv(csv_path)
            print(f"   ✅ Loaded {len(df):,} records")
            
            # Standardize columns
            df = self._standardize_booking_columns(df)
            
            print(f"   📊 Columns: {list(df.columns)[:5]}... ({len(df.columns)} total)")
            print(f"   📅 Date range: {df['check_in_date'].min()} to {df['check_in_date'].max()}")
            print(f"   💰 Price range: ${df['adr'].min():.0f} - ${df['adr'].max():.0f}")
            print(f"   📍 Hotel types: {df['hotel_type'].unique()}")
            print(f"   ✅ Cancellation rate: {df['is_cancelled'].mean()*100:.1f}%")
            
            return df
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def load_airbnb_data(self, data_path):
        """Load and process Airbnb data"""
        print("\n📖 Loading Inside Airbnb Data...")
        
        data_path = Path(data_path)
        listings_files = list(data_path.glob("*listings.csv"))
        
        if not listings_files:
            print("   ❌ No listings.csv files found")
            return None
        
        try:
            dfs = []
            for listing_file in listings_files:
                city = listing_file.name.split('_')[0]
                df = pd.read_csv(listing_file, low_memory=False)
                df['city'] = city
                dfs.append(df)
                print(f"   ✅ Loaded {len(df):,} listings from {city}")
            
            combined = pd.concat(dfs, ignore_index=True)
            print(f"   📊 Total: {len(combined):,} Airbnb listings")
            
            # Extract pricing data
            consolidated = self._extract_airbnb_pricing(combined)
            return consolidated
        except Exception as e:
            print(f"   ⚠️  Note: {e}")
            return None
    
    def load_reviews(self, data_path, source='tripadvisor'):
        """Load review data"""
        print(f"\n📖 Loading {source.title()} Reviews...")
        
        data_path = Path(data_path)
        review_files = list(data_path.glob("*reviews*.csv"))
        
        if not review_files:
            print("   ❌ No review CSV files found")
            return None
        
        try:
            dfs = []
            for review_file in review_files:
                df = pd.read_csv(review_file, nrows=100000)  # Limit for memory
                dfs.append(df)
            
            combined = pd.concat(dfs, ignore_index=True)
            print(f"   ✅ Loaded {len(combined):,} reviews")
            print(f"   📊 Unique hotels: {combined.get('Hotel_ID', combined.get('hotel_id', combined.get('id'))).nunique():,}")
            
            return combined
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            return None
    
    def _standardize_booking_columns(self, df):
        """Standardize Hotel Booking Demand columns"""
        # Create standardized dataframe
        standardized = pd.DataFrame()
        
        # Core booking fields
        standardized['booking_id'] = range(1, len(df) + 1)
        standardized['hotel_type'] = df.get('hotel', df.get('is_type_hotel', 'Unknown'))
        standardized['arrival_date'] = pd.to_datetime(
            df['arrival_date_year'].astype(str) + '-' +
            df['arrival_date_month'].astype(str) + '-' +
            df['arrival_date_day_of_month'].astype(str)
        )
        standardized['check_in_date'] = standardized['arrival_date']
        standardized['stay_nights'] = df.get('stays_in_weekend_nights', 0) + df.get('stays_in_week_nights', 0)
        standardized['check_out_date'] = standardized['check_in_date'] + pd.to_timedelta(standardized['stay_nights'], unit='d')
        
        # Pricing
        standardized['adr'] = df.get('adr', 0).astype(float)
        standardized['total_price'] = standardized['adr'] * standardized['stay_nights']
        
        # Guest info
        standardized['guests_count'] = (
            df.get('adults', 0) + 
            df.get('children', 0).fillna(0) + 
            df.get('babies', 0).fillna(0)
        )
        standardized['country'] = df.get('country', 'Unknown')
        
        # Booking details
        standardized['booking_channel'] = df.get('distribution_channel', 'Unknown')
        standardized['is_cancelled'] = df.get('is_cancelled', False)
        standardized['lead_time_days'] = df.get('lead_time', 0)
        standardized['previous_cancellations'] = df.get('previous_cancellations', 0)
        
        # Additional features
        standardized['meal_type'] = df.get('meal', 'Unknown')
        standardized['customer_type'] = df.get('customer_type', 'Unknown')
        standardized['required_car_parking'] = df.get('required_car_parking_spaces', False)
        standardized['booking_changes'] = df.get('booking_changes', 0)
        
        return standardized.dropna(subset=['check_in_date', 'adr'])
    
    def _extract_airbnb_pricing(self, df):
        """Extract relevant pricing data from Airbnb"""
        # Create standardized pricing records
        pricing = pd.DataFrame()
        
        pricing['property_id'] = df.get('id', range(len(df)))
        pricing['property_name'] = df.get('name', 'Unknown')
        pricing['room_type'] = df.get('room_type', 'Unknown')
        pricing['nightly_price'] = df.get('price', df.get('Price', 0))
        
        # Clean price (remove $ and commas)
        if pricing['nightly_price'].dtype == 'object':
            pricing['nightly_price'] = pricing['nightly_price'].str.replace('$', '').str.replace(',', '').astype(float)
        
        pricing['minimum_nights'] = df.get('minimum_nights', 1)
        pricing['availability_365'] = df.get('availability_365', 0)
        pricing['reviews_per_month'] = df.get('reviews_per_month', 0)
        pricing['review_scores_rating'] = df.get('review_scores_rating', 0)
        pricing['accommodates'] = df.get('accommodates', 2)
        pricing['bedrooms'] = df.get('bedrooms', 1)
        pricing['beds'] = df.get('beds', 1)
        pricing['city'] = df.get('city', 'Unknown')
        
        return pricing.dropna(subset=['nightly_price'])
    
    def merge_booking_and_synthetic(self, booking_df, synthetic_df):
        """Merge real booking data with synthetic data"""
        print("\n🔄 Merging Real & Synthetic Data...")
        
        # Standardize for merging
        booking_df['data_source'] = 'real'
        synthetic_df['data_source'] = 'synthetic'
        
        # Select common columns
        common_cols = [
            'booking_id', 'hotel_type', 'check_in_date', 'stay_nights', 'adr',
            'guests_count', 'country', 'is_cancelled', 'booking_channel'
        ]
        
        booking_subset = booking_df[[c for c in common_cols if c in booking_df.columns]]
        synthetic_subset = synthetic_df[[c for c in common_cols if c in synthetic_df.columns] + ['data_source']]
        
        try:
            merged = pd.concat([booking_subset, synthetic_subset], ignore_index=True, sort=False)
            print(f"   ✅ Merged: {len(merged):,} total records")
            print(f"      Real: {(merged['data_source']=='real').sum():,} | Synthetic: {(merged['data_source']=='synthetic').sum():,}")
            return merged
        except Exception as e:
            print(f"   ⚠️  Error merging: {e}")
            return booking_df
    
    def create_training_split(self, df, output_prefix="training_data"):
        """Create train/val/test splits"""
        print("\n📊 Creating Training Splits...")
        
        df = df.sort_values('check_in_date')
        n = len(df)
        
        # 70/15/15 split
        train_idx = int(n * 0.70)
        val_idx = int(n * 0.85)
        
        train = df.iloc[:train_idx]
        val = df.iloc[train_idx:val_idx]
        test = df.iloc[val_idx:]
        
        # Save
        train.to_csv(self.output_dir / f"{output_prefix}_train.csv", index=False)
        val.to_csv(self.output_dir / f"{output_prefix}_val.csv", index=False)
        test.to_csv(self.output_dir / f"{output_prefix}_test.csv", index=False)
        
        print(f"   ✅ Train: {len(train):,} records ({len(train)/n*100:.1f}%)")
        print(f"   ✅ Val:   {len(val):,} records ({len(val)/n*100:.1f}%)")
        print(f"   ✅ Test:  {len(test):,} records ({len(test)/n*100:.1f}%)")
        
        return train, val, test
    
    def generate_summary(self, df):
        """Generate data quality summary"""
        print("\n📋 Data Quality Summary:")
        print(f"   Records: {len(df):,}")
        print(f"   Columns: {len(df.columns)}")
        print(f"   Missing values: {df.isnull().sum().sum():,}")
        print(f"   Duplicates: {df.duplicated().sum():,}")
        
        if 'adr' in df.columns:
            print(f"   Price range: ${df['adr'].min():.0f} - ${df['adr'].max():.0f}")
            print(f"   Average price: ${df['adr'].mean():.2f}")
        
        if 'is_cancelled' in df.columns:
            cancel_rate = df['is_cancelled'].mean() * 100
            print(f"   Cancellation rate: {cancel_rate:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Consolidate and merge real hotel datasets for NEPHELE Task 3'
    )
    parser.add_argument(
        '--booking',
        help='Path to Hotel Booking Demand dataset'
    )
    parser.add_argument(
        '--airbnb',
        help='Path to Inside Airbnb dataset'
    )
    parser.add_argument(
        '--reviews',
        help='Path to reviews dataset'
    )
    parser.add_argument(
        '--output',
        default='consolidated_data.csv',
        help='Output filename'
    )
    parser.add_argument(
        '--synthetic',
        help='Path to synthetic data to merge'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Consolidate all available real data'
    )
    
    args = parser.parse_args()
    
    consolidator = RealDataConsolidator()
    
    print("\n" + "="*80)
    print("NEPHELE REAL DATA CONSOLIDATION")
    print("="*80)
    
    all_data = []
    
    if args.booking:
        booking_df = consolidator.load_booking_demand(args.booking)
        if booking_df is not None:
            all_data.append(booking_df)
            consolidator.generate_summary(booking_df)
    
    if args.airbnb:
        airbnb_df = consolidator.load_airbnb_data(args.airbnb)
        if airbnb_df is not None:
            consolidator.generate_summary(airbnb_df)
    
    if args.reviews:
        reviews_df = consolidator.load_reviews(args.reviews)
        if reviews_df is not None:
            consolidator.generate_summary(reviews_df)
    
    if all_data:
        consolidated = pd.concat(all_data, ignore_index=True, sort=False)
        consolidated.to_csv(consolidator.output_dir / args.output, index=False)
        print(f"\n✅ Consolidated dataset saved: {consolidator.output_dir / args.output}")
        print(f"   Total records: {len(consolidated):,}")
        print(f"   Columns: {len(consolidated.columns)}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
