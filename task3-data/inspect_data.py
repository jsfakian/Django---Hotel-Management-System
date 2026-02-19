#!/usr/bin/env python3
"""
Quick data inspection script - Shows sample rows from all datasets
Usage: python3 inspect_data.py
"""

import pandas as pd
from pathlib import Path

def inspect_datasets():
    """Display sample rows from all CSV files"""
    data_dir = Path(__file__).parent
    
    datasets = {
        'properties.csv': 'Hotel Properties (Master Data)',
        'rooms.csv': 'Room Inventory (Features)',
        'guests.csv': 'Guest Profiles (5,000 Guests)',
        'bookings.csv': 'Booking History (24,260+ Records)',
        'pricing_history.csv': 'Daily Pricing & Occupancy (1,095 Days × 10 Hotels)',
        'guest_preferences.csv': 'Guest Preferences (25,188 Records)',
        'competitor_pricing.csv': 'Competitor Pricing Intelligence (43,739 Records)',
    }
    
    print("\n" + "="*80)
    print("NEPHELE HOTEL MANAGEMENT SYSTEM - TASK 3 DATA INSPECTION")
    print("="*80 + "\n")
    
    for filename, description in datasets.items():
        filepath = data_dir / filename
        
        if not filepath.exists():
            print(f"❌ {filename} - NOT FOUND")
            continue
        
        df = pd.read_csv(filepath)
        file_size = filepath.stat().st_size / (1024 * 1024)  # MB
        
        print(f"\n{'='*80}")
        print(f"📄 {filename}")
        print(f"   Description: {description}")
        print(f"   Rows: {len(df):,}  |  Columns: {len(df.columns)}  |  Size: {file_size:.1f} MB")
        print(f"{'='*80}")
        
        print("\n✓ Column Names & Types:")
        for col, dtype in zip(df.columns, df.dtypes):
            print(f"   • {col:<25} {str(dtype):<15}")
        
        print("\n✓ Sample Data (First 3 rows):")
        print(df.head(3).to_string())
        
        print("\n✓ Data Summary:")
        print(f"   • Missing values: {df.isnull().sum().sum()}")
        print(f"   • Duplicate rows: {df.duplicated().sum()}")
        if len(df) > 0:
            print(f"   • Memory usage: {df.memory_usage(deep=True).sum() / (1024*1024):.1f} MB")

if __name__ == "__main__":
    inspect_datasets()
    print("\n" + "="*80)
    print("✓ Data inspection complete")
    print("="*80 + "\n")
