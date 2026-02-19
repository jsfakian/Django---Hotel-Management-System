#!/usr/bin/env python3
"""
NEPHELE Task 3 - Data Loader
Load and preprocess real Airbnb data for algorithm training

Data sources: Inside Airbnb (NYC, London, Barcelona)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class AirbnbDataLoader:
    """Load and preprocess Airbnb listings, calendar, and review data"""
    
    def __init__(self, data_dir="../task3-data/real-data/airbnb_combined"):
        self.data_dir = Path(data_dir)
        self.listings_data = {}
        self.calendar_data = {}
        self.reviews_data = {}
        self.cities = ['new-york-city', 'london', 'barcelona']
    
    def load_all_cities(self):
        """Load data from all cities"""
        print("📊 Loading Airbnb data from all cities...\n")
        
        for city in self.cities:
            print(f"  Loading {city}...")
            self.load_city_data(city)
        
        print(f"\n✅ Loaded data from {len(self.cities)} cities")
        return self.listings_data, self.calendar_data, self.reviews_data
    
    def load_city_data(self, city):
        """Load listings, calendar, and reviews for a city"""
        try:
            # Load listings
            listings_file = self.data_dir / f"{city}_listings.csv"
            if listings_file.exists():
                self.listings_data[city] = pd.read_csv(listings_file)
                print(f"    ✓ Listings: {len(self.listings_data[city]):,} records")
            
            # Load calendar
            calendar_file = self.data_dir / f"{city}_calendar.csv"
            if calendar_file.exists():
                self.calendar_data[city] = pd.read_csv(calendar_file)
                print(f"    ✓ Calendar: {len(self.calendar_data[city]):,} records")
            
            # Load reviews
            reviews_file = self.data_dir / f"{city}_reviews.csv"
            if reviews_file.exists():
                self.reviews_data[city] = pd.read_csv(reviews_file)
                print(f"    ✓ Reviews: {len(self.reviews_data[city]):,} records")
        
        except Exception as e:
            print(f"    ⚠️  Error loading {city}: {str(e)}")
    
    def prepare_pricing_data(self, sample_size=10000):
        """Prepare data for pricing algorithms using listings data
        
        Returns:
            df: DataFrame with features and target price
        """
        print("\n📈 Preparing pricing training data...")
        
        frames = []
        
        for city in self.cities:
            if city not in self.listings_data:
                continue
            
            print(f"  Processing {city}...")
            
            list_df = self.listings_data[city].copy()
            
            # Get price column (handle different column names)
            price_col = None
            if 'price' in list_df.columns:
                price_col = 'price'
            elif 'listing_price' in list_df.columns:
                price_col = 'listing_price'
            else:
                print(f"    ⚠️  No price column found in {city}")
                continue
            
            # Clean price column - remove $ and commas
            list_df['price'] = list_df[price_col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            list_df['price'] = pd.to_numeric(list_df['price'], errors='coerce')
            
            # Convert date
            if 'date' in list_df.columns:
                list_df['date'] = pd.to_datetime(list_df['date'], errors='coerce')
            else:
                # Use last_scraped if available
                list_df['date'] = pd.to_datetime(list_df.get('last_scraped'), errors='coerce')
            
            # Remove nulls
            list_df = list_df.dropna(subset=['price'])
            
            # Filter outliers (keep prices between $10-$1000)
            list_df = list_df[(list_df['price'] > 10) & (list_df['price'] < 1000)]
            
            if len(list_df) == 0:
                print(f"    ⚠️  No valid pricing data in {city}")
                continue
            
            # Extract time features
            if 'date' in list_df.columns:
                list_df['month'] = list_df['date'].dt.month
                list_df['day_of_week'] = list_df['date'].dt.dayofweek
                list_df['season'] = list_df['month'].apply(self._get_season)
            else:
                list_df['month'] = np.random.randint(1, 13, len(list_df))
                list_df['day_of_week'] = np.random.randint(0, 7, len(list_df))
                list_df['season'] = list_df['month'].apply(self._get_season)
            
            # Handle missing values
            list_df['review_scores_rating'] = pd.to_numeric(list_df.get('review_scores_rating', 4.5), errors='coerce').fillna(4.5)
            list_df['accommodates'] = pd.to_numeric(list_df.get('accommodates', 2), errors='coerce').fillna(2)
            list_df['bedrooms'] = pd.to_numeric(list_df.get('bedrooms', 1), errors='coerce').fillna(1)
            list_df['beds'] = pd.to_numeric(list_df.get('beds', 1), errors='coerce').fillna(1)

            # Availability signal used by pricing trainer
            if 'available' in list_df.columns:
                list_df['available_binary'] = (
                    list_df['available']
                    .astype(str)
                    .str.lower()
                    .isin(['t', 'true', '1', 'yes'])
                    .astype(int)
                )
            elif 'availability_365' in list_df.columns:
                list_df['available_binary'] = (pd.to_numeric(list_df['availability_365'], errors='coerce').fillna(0) > 0).astype(int)
            else:
                list_df['available_binary'] = 1
            
            # Get room type if available
            if 'room_type' not in list_df.columns:
                list_df['room_type'] = list_df.get('property_type', 'Entire home/apt')
            
            # Add city feature
            list_df['city'] = city
            
            # Select relevant columns
            cols_to_keep = [
                'price', 'day_of_week', 'month', 'season', 'room_type',
                'accommodates', 'bedrooms', 'beds', 'review_scores_rating',
                'available_binary', 'city'
            ]
            list_df_subset = list_df[[c for c in cols_to_keep if c in list_df.columns]].copy()
            
            if len(list_df_subset) > 0:
                frames.append(list_df_subset)
                print(f"    ✓ {len(list_df_subset):,} records from {city}")
        
        if not frames:
            print("  ⚠️  No pricing data could be extracted")
            return pd.DataFrame()
        
        # Combine all cities
        df = pd.concat(frames, ignore_index=True)
        
        # Sample if too large
        if len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
        
        print(f"  ✓ Prepared {len(df):,} pricing records")
        return df
    
    def prepare_recommendation_data(self, min_reviews=3):
        """Prepare data for recommendation algorithms
        
        Returns:
            interaction_df: User-item interaction matrix
            item_features_df: Item features
        """
        print("\n🔍 Preparing recommendation training data...")
        
        interaction_frames = []
        features_frames = []
        
        for city in self.cities:
            if city not in self.reviews_data or city not in self.listings_data:
                continue
            
            print(f"  Processing {city}...")
            
            reviews_df = self.reviews_data[city].copy()
            listings_df = self.listings_data[city].copy()
            
            # Create user-listing interactions from reviews
            if len(reviews_df) > 0:
                reviews_df['reviewer_id'] = pd.factorize(reviews_df['reviewer_id'])[0]
                reviews_df['rating'] = 4.5  # Default if no explicit rating
                reviews_df['date'] = pd.to_datetime(reviews_df['date'], errors='coerce')
                
                interactions = reviews_df[['reviewer_id', 'listing_id', 'rating']].copy()
                interactions['city'] = city
                interaction_frames.append(interactions)
            
            # Extract listing features for content-based filtering
            if len(listings_df) > 0:
                features_df = listings_df[[
                    'id', 'room_type', 'accommodates', 'bedrooms', 'beds',
                    'review_scores_rating', 'price'
                ]].copy()
                
                # Clean price
                features_df['price'] = features_df['price'].astype(str).str.replace('$', '').str.replace(',', '')
                features_df['price'] = pd.to_numeric(features_df['price'], errors='coerce')
                
                # Handle missing values
                features_df['review_scores_rating'] = features_df['review_scores_rating'].fillna(4.5)
                features_df['accommodates'] = features_df['accommodates'].fillna(2)
                features_df['bedrooms'] = features_df['bedrooms'].fillna(1)
                features_df['price'] = features_df['price'].fillna(features_df['price'].median())
                
                features_df['city'] = city
                features_frames.append(features_df)
        
        # Combine data
        interactions_df = pd.concat(interaction_frames, ignore_index=True) if interaction_frames else pd.DataFrame()
        features_df = pd.concat(features_frames, ignore_index=True) if features_frames else pd.DataFrame()
        
        print(f"  ✓ Prepared {len(interactions_df):,} interactions")
        print(f"  ✓ Prepared {len(features_df):,} items")
        
        return interactions_df, features_df
    
    def get_synthetic_data(self, data_dir="../task3-data"):
        """Load synthetic data as fallback/supplementary data"""
        print("\n📁 Loading synthetic data...")
        
        try:
            bookings = pd.read_csv(Path(data_dir) / "bookings.csv")
            preferences = pd.read_csv(Path(data_dir) / "guest_preferences.csv")
            pricing_history = pd.read_csv(Path(data_dir) / "pricing_history.csv")
            
            print(f"  ✓ Bookings: {len(bookings):,} records")
            print(f"  ✓ Preferences: {len(preferences):,} records")
            print(f"  ✓ Pricing History: {len(pricing_history):,} records")
            
            return bookings, preferences, pricing_history
        except Exception as e:
            print(f"  ⚠️  Could not load synthetic data: {str(e)}")
            return None, None, None
    
    @staticmethod
    def _get_season(month):
        """Map month to season"""
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'
    
    def get_statistics(self):
        """Print data statistics"""
        print("\n📊 DATA STATISTICS")
        print("=" * 80)
        
        for city in self.cities:
            if city in self.listings_data:
                print(f"\n{city.upper()}")
                print(f"  Listings: {len(self.listings_data[city]):,}")
            if city in self.calendar_data:
                print(f"  Calendar records: {len(self.calendar_data[city]):,}")
            if city in self.reviews_data:
                print(f"  Reviews: {len(self.reviews_data[city]):,}")
        
        print("\n" + "=" * 80)


def main():
    """Test data loader"""
    loader = AirbnbDataLoader()
    
    # Load all data
    listings, calendar, reviews = loader.load_all_cities()
    
    # Get statistics
    loader.get_statistics()
    
    # Prepare pricing data
    pricing_df = loader.prepare_pricing_data(sample_size=50000)
    print("\nPricing data sample:")
    print(pricing_df.head())
    print(pricing_df.info())
    
    # Prepare recommendation data
    interactions_df, features_df = loader.prepare_recommendation_data()
    print("\nInteractions data sample:")
    print(interactions_df.head())
    print("\nFeatures data sample:")
    print(features_df.head())


if __name__ == "__main__":
    main()
