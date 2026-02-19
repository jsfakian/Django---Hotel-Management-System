#!/usr/bin/env python3
"""
NEPHELE Hotel Management System - Synthetic Dataset Generation
Task 3: Research Completion - AI Training Data

This script generates synthetic datasets for:
1. Dynamic Pricing Algorithm Training
2. Personalization/Recommendation System Training
3. Business Intelligence & Analytics
4. Guest Segmentation Analysis

Generated datasets:
- properties.csv: Hotel property information
- rooms.csv: Room inventory with features
- guests.csv: Guest profiles and preferences
- bookings.csv: Reservation history (20,000+ records)
- guest_preferences.csv: Guest amenity and room preferences
- pricing_history.csv: Historical pricing and occupancy
- competitor_pricing.csv: Competitor pricing data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

# Set random seeds for reproducibility
np.random.seed(42)
random.seed(42)

class SyntheticDataGenerator:
    def __init__(self, output_dir="task3-data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.num_properties = 10
        self.num_rooms_per_property = 30
        self.num_guests = 5000
        self.num_bookings = 25000
        self.start_date = datetime(2022, 1, 1)
        self.end_date = datetime(2024, 12, 31)
        
        # Room types and configurations
        self.room_types = ["Standard", "Deluxe", "Suite", "Family", "Penthouse"]
        self.views = ["City View", "Sea View", "Mountain View", "Garden View", "Standard"]
        self.amenities = [
            "WiFi", "AC", "Heating", "Breakfast Included", "Parking",
            "Gym Access", "Pool Access", "Spa", "Balcony", "Mini Bar",
            "Safe", "Desk", "Bathrobe", "Hairdryer", "Iron", "TV"
        ]
        
        # Customer segments
        self.customer_types = ["Business", "Leisure", "Family", "Couple", "Solo Travel"]
        self.origin_countries = ["Greece", "Germany", "UK", "France", "USA", "China", "Italy", "Spain", "Belgium", "Netherlands"]
        self.booking_channels = ["Direct Website", "Booking.com", "Airbnb", "Expedia", "Hotel.com", "Travel Agency", "Corporate"]
        
        print("Initializing NEPHELE Synthetic Data Generator...")
        
    def generate_properties(self):
        """Generate hotel property data"""
        print("Generating properties...")
        cities = ["Athens", "Thessaloniki", "Mykonos", "Santorini", "Crete", 
                  "Rhodes", "Corfu", "Naxos", "Paros", "Milos"]
        
        properties = []
        for i in range(self.num_properties):
            prop = {
                "property_id": f"PROP{i+1:03d}",
                "name": f"Nephele Hotel {i+1}",
                "city": cities[i % len(cities)],
                "country": "Greece",
                "star_rating": np.random.choice([3, 4, 5], p=[0.3, 0.5, 0.2]),
                "total_rooms": self.num_rooms_per_property,
                "property_type": np.random.choice(["Luxury Resort", "Boutique Hotel", "Business Hotel", "Beach Resort"]),
                "founded_year": random.randint(1990, 2020),
                "manager_email": f"manager{i+1}@nephele.com",
            }
            properties.append(prop)
        
        df = pd.DataFrame(properties)
        df.to_csv(self.output_dir / "properties.csv", index=False)
        print(f"✓ Generated {len(df)} properties")
        return df
    
    def generate_rooms(self, properties_df):
        """Generate room inventory"""
        print("Generating rooms...")
        rooms = []
        
        for _, prop in properties_df.iterrows():
            for room_num in range(self.num_rooms_per_property):
                room = {
                    "room_id": f"{prop['property_id']}_R{room_num+1:04d}",
                    "property_id": prop['property_id'],
                    "room_number": room_num + 1,
                    "room_type": np.random.choice(self.room_types, p=[0.35, 0.35, 0.15, 0.10, 0.05]),
                    "floor": random.randint(1, 5),
                    "capacity": np.random.choice([1, 2, 3, 4]),
                    "view_type": np.random.choice(self.views),
                    "size_sqm": np.random.randint(20, 100),
                    "base_price_per_night": np.random.randint(50, 500),
                    "amenities": "|".join(random.sample(self.amenities, k=random.randint(5, 12))),
                    "last_renovation": random.randint(2015, 2024),
                }
                rooms.append(room)
        
        df = pd.DataFrame(rooms)
        df.to_csv(self.output_dir / "rooms.csv", index=False)
        print(f"✓ Generated {len(df)} rooms")
        return df
    
    def generate_guests(self):
        """Generate guest profiles"""
        print("Generating guests...")
        first_names = ["John", "Maria", "Ahmed", "Sophie", "Klaus", "Yuki", "Francesca", "Emma", "Marco", "Lucia"]
        last_names = ["Smith", "Johnson", "Mueller", "Garcia", "Brown", "Schmidt", "Zhang", "Rossi", "Martin", "Weber"]
        
        guests = []
        for i in range(self.num_guests):
            guest = {
                "guest_id": f"GUEST{i+1:06d}",
                "first_name": random.choice(first_names),
                "last_name": random.choice(last_names),
                "email": f"guest{i+1:06d}@email.com",
                "customer_type": np.random.choice(self.customer_types, p=[0.25, 0.35, 0.15, 0.15, 0.10]),
                "origin_country": np.random.choice(self.origin_countries),
                "preferred_room_type": np.random.choice(self.room_types),
                "loyalty_member": np.random.choice([True, False], p=[0.3, 0.7]),
                "registered_date": self.start_date + timedelta(days=random.randint(0, 1000)),
                "total_stays": np.random.exponential(3) + 1,
                "average_rating": np.random.normal(4.2, 0.5),
            }
            guests.append(guest)
        
        df = pd.DataFrame(guests)
        df["total_stays"] = df["total_stays"].astype(int)
        df["average_rating"] = df["average_rating"].clip(1, 5).round(1)
        df.to_csv(self.output_dir / "guests.csv", index=False)
        print(f"✓ Generated {len(df)} guests")
        return df
    
    def generate_bookings(self, properties_df, rooms_df, guests_df):
        """Generate booking history"""
        print("Generating bookings...")
        bookings = []
        property_ids = properties_df["property_id"].tolist()
        guest_ids = guests_df["guest_id"].tolist()
        
        for b in range(self.num_bookings):
            prop_id = random.choice(property_ids)
            guest_id = random.choice(guest_ids)
            
            # Weighted distribution towards higher occupancy periods
            booking_date = self.start_date + timedelta(days=random.randint(0, (self.end_date - self.start_date).days))
            
            # Check-in between 1-60 days after booking
            nights = int(np.random.choice([1, 2, 3, 4, 5, 7, 10, 14], p=[0.15, 0.20, 0.20, 0.15, 0.12, 0.10, 0.05, 0.03]))
            check_in = booking_date + timedelta(days=random.randint(1, 60))
            check_out = check_in + timedelta(days=nights)
            
            if check_out > self.end_date:
                continue
            
            # Room selection
            prop_rooms = rooms_df[rooms_df["property_id"] == prop_id]
            room = prop_rooms.sample(1).iloc[0]
            
            # Price with seasonality and adjustments
            base_price = room["base_price_per_night"]
            
            # Seasonal multiplier
            month = check_in.month
            if month in [6, 7, 8]:  # Summer peak
                seasonal_mult = 1.4
            elif month in [12, 1]:  # Winter holidays
                seasonal_mult = 1.3
            elif month in [4, 5, 9, 10]:  # Shoulder seasons
                seasonal_mult = 1.1
            else:  # Off-season
                seasonal_mult = 0.85
            
            # Lead time discount
            lead_time = (check_in - booking_date).days
            lead_time_mult = 0.9 if lead_time < 7 else (1.05 if lead_time > 30 else 1.0)
            
            nightly_rate = base_price * seasonal_mult * lead_time_mult * np.random.normal(1, 0.05)
            total_price = nightly_rate * nights
            
            booking = {
                "booking_id": f"BK{b+1:08d}",
                "guest_id": guest_id,
                "property_id": prop_id,
                "room_id": room["room_id"],
                "booking_date": booking_date.strftime("%Y-%m-%d"),
                "check_in_date": check_in.strftime("%Y-%m-%d"),
                "check_out_date": check_out.strftime("%Y-%m-%d"),
                "number_of_nights": nights,
                "booking_channel": np.random.choice(self.booking_channels),
                "nightly_rate": round(nightly_rate, 2),
                "total_price": round(total_price, 2),
                "status": np.random.choice(["Completed", "Completed", "Completed", "Cancelled", "No-Show"], p=[0.80, 0.10, 0.05, 0.03, 0.02]),
                "payment_method": np.random.choice(["Credit Card", "PayPal", "Bank Transfer", "Cash"]),
                "guests_count": random.randint(1, 4),
            }
            bookings.append(booking)
        
        df = pd.DataFrame(bookings)
        df = df[df["check_out_date"] <= self.end_date.strftime("%Y-%m-%d")]
        df.to_csv(self.output_dir / "bookings.csv", index=False)
        print(f"✓ Generated {len(df)} bookings")
        return df
    
    def generate_guest_preferences(self, guests_df, rooms_df):
        """Generate guest preferences for recommendations"""
        print("Generating guest preferences...")
        preferences = []
        room_ids = rooms_df["room_id"].tolist()
        
        for _, guest in guests_df.iterrows():
            # Each guest has multiple preference records
            num_prefs = random.randint(2, 8)
            for _ in range(num_prefs):
                room_id = random.choice(room_ids)
                room = rooms_df[rooms_df["room_id"] == room_id].iloc[0]
                
                pref = {
                    "guest_id": guest["guest_id"],
                    "room_id": room_id,
                    "room_type": room["room_type"],
                    "preferred_floor": random.randint(1, 5),
                    "wants_breakfast": np.random.choice([True, False], p=[0.6, 0.4]),
                    "wants_parking": np.random.choice([True, False], p=[0.5, 0.5]),
                    "needs_accessibility": np.random.choice([True, False], p=[0.1, 0.9]),
                    "preferred_view": np.random.choice(self.views),
                    "min_room_size_sqm": random.randint(15, 50),
                    "willing_to_pay_extra": np.random.choice([True, False], p=[0.4, 0.6]),
                    "rating": np.random.choice([3, 4, 4, 5, 5, 5]),  # Weighted towards higher ratings
                }
                preferences.append(pref)
        
        df = pd.DataFrame(preferences)
        df.to_csv(self.output_dir / "guest_preferences.csv", index=False)
        print(f"✓ Generated {len(df)} guest preference records")
        return df
    
    def generate_pricing_history(self, properties_df, rooms_df):
        """Generate pricing and occupancy history for dynamic pricing models"""
        print("Generating pricing history...")
        pricing_history = []
        
        current_date = self.start_date
        while current_date <= self.end_date:
            for _, prop in properties_df.iterrows():
                prop_rooms = rooms_df[rooms_df["property_id"] == prop["property_id"]]
                
                # Daily property-level metrics
                occupancy_rate = np.random.beta(7, 3)  # Beta distribution, skewed towards higher occupancy
                
                # Seasonal adjustment
                month = current_date.month
                if month in [6, 7, 8]:
                    occupancy_rate = min(occupancy_rate * 1.3, 0.95)
                elif month in [1, 2, 11, 12]:
                    occupancy_rate = max(occupancy_rate * 0.7, 0.1)
                
                day_of_week = current_date.weekday()
                
                # Weekend premium
                if day_of_week >= 4:  # Fri-Sun
                    occupancy_rate = min(occupancy_rate * 1.15, 0.95)
                
                record = {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "property_id": prop["property_id"],
                    "occupancy_rate": round(occupancy_rate, 3),
                    "available_rooms": int(prop["total_rooms"] * (1 - occupancy_rate)),
                    "occupied_rooms": int(prop["total_rooms"] * occupancy_rate),
                    "average_nightly_rate": round(prop_rooms["base_price_per_night"].mean() * 
                                                 (1.2 if month in [6,7,8] else 0.9 if month in [1,2,11,12] else 1.0), 2),
                    "day_of_week": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_of_week],
                    "season": self._get_season(month),
                    "is_holiday": self._is_holiday(current_date),
                }
                pricing_history.append(record)
            
            current_date += timedelta(days=1)
        
        df = pd.DataFrame(pricing_history)
        df.to_csv(self.output_dir / "pricing_history.csv", index=False)
        print(f"✓ Generated {len(df)} pricing history records")
        return df
    
    def generate_competitor_pricing(self, properties_df):
        """Generate competitor pricing data"""
        print("Generating competitor pricing...")
        competitor_data = []
        
        current_date = self.start_date
        while current_date <= self.end_date:
            for _, prop in properties_df.iterrows():
                # 3-5 competitors per property
                num_competitors = random.randint(3, 5)
                
                for comp_idx in range(num_competitors):
                    comp = {
                        "date": current_date.strftime("%Y-%m-%d"),
                        "property_id": prop["property_id"],
                        "competitor_id": f"COMP_{comp_idx+1}",
                        "competitor_name": f"Competitor Hotel {comp_idx+1}",
                        "competitor_price": round(np.random.normal(100, 30), 2),
                        "competitor_available_rooms": random.randint(0, 50),
                        "competitor_rating": round(np.random.normal(4.0, 0.5), 1),
                    }
                    competitor_data.append(comp)
            
            current_date += timedelta(days=1)
        
        df = pd.DataFrame(competitor_data)
        df.to_csv(self.output_dir / "competitor_pricing.csv", index=False)
        print(f"✓ Generated {len(df)} competitor pricing records")
        return df
    
    def _get_season(self, month):
        """Determine season from month"""
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Fall"
    
    def _is_holiday(self, date):
        """Check if date is a holiday"""
        holidays = [
            (1, 1),   # New Year
            (3, 25),  # Greek Independence Day
            (5, 1),   # Labor Day
            (8, 15),  # Assumption of Mary
            (10, 28), # Ochi Day
            (12, 25), # Christmas
            (12, 26), # Boxing Day equivalent
        ]
        return (date.month, date.day) in holidays or date.weekday() >= 5
    
    def generate_all(self):
        """Generate all datasets"""
        print("\n" + "="*70)
        print("NEPHELE - SYNTHETIC DATA GENERATION")
        print("="*70 + "\n")
        
        properties = self.generate_properties()
        rooms = self.generate_rooms(properties)
        guests = self.generate_guests()
        bookings = self.generate_bookings(properties, rooms, guests)
        preferences = self.generate_guest_preferences(guests, rooms)
        pricing = self.generate_pricing_history(properties, rooms)
        competitors = self.generate_competitor_pricing(properties)
        
        print("\n" + "="*70)
        print("✓ ALL DATASETS GENERATED SUCCESSFULLY")
        print("="*70)
        print(f"\nOutput directory: {self.output_dir.absolute()}\n")
        print("Generated files:")
        print("  • properties.csv - Hotel property information")
        print("  • rooms.csv - Room inventory with features")
        print("  • guests.csv - Guest profiles (5,000 guests)")
        print("  • bookings.csv - Reservation history (25,000+ bookings)")
        print("  • guest_preferences.csv - Guest amenity preferences")
        print("  • pricing_history.csv - Historical pricing and occupancy")
        print("  • competitor_pricing.csv - Competitor pricing data")
        print("\nDatasets cover: 2022-01-01 to 2024-12-31 (24 months)")
        print("="*70 + "\n")


if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    generator.generate_all()
