#!/usr/bin/env python3
"""
NEPHELE Task 3 - Model Prediction & Inference
Load trained models and make predictions for pricing and recommendations
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class PricingPredictor:
    """Load and use trained pricing models"""
    
    def __init__(self, model_dir="./models/pricing"):
        self.model_dir = Path(model_dir)
        self.models = {}
        self.feature_columns = None
        self.preprocessing_objects = None
        self.load_models()
    
    def load_models(self):
        """Load all trained pricing models"""
        print(f"📦 Loading pricing models from {self.model_dir}...")
        
        # Load feature columns
        features_file = self.model_dir / "pricing_feature_columns.pkl"
        if features_file.exists():
            self.feature_columns = joblib.load(features_file)
            print(f"  ✓ Loaded {len(self.feature_columns)} feature columns")
        
        # Load preprocessing objects
        preprocessing_file = self.model_dir / "pricing_preprocessing.pkl"
        if preprocessing_file.exists():
            self.preprocessing_objects = joblib.load(preprocessing_file)
            print(f"  ✓ Loaded preprocessing objects")
        
        # Load model files
        for model_file in self.model_dir.glob("pricing_*.pkl"):
            if "feature_columns" in model_file.name or "preprocessing" in model_file.name:
                continue
            
            try:
                model = joblib.load(model_file)
                model_name = model_file.stem.replace("pricing_", "").replace("_", " ")
                self.models[model_name] = model
                print(f"  ✓ Loaded {model_name}")
            except Exception as e:
                print(f"  ⚠️  Could not load {model_file.name}: {str(e)}")
        
        print(f"\n✅ Total models loaded: {len(self.models)}")
        return len(self.models) > 0
    
    def predict_price(self, booking_data, model_name="ensemble"):
        """Predict price for a booking
        
        Args:
            booking_data: dict with features (day_of_week, month, season, room_type, etc.)
            model_name: which model to use (default: ensemble)
        
        Returns:
            float: predicted price
        """
        
        if model_name not in self.models:
            print(f"⚠️  Model {model_name} not found. Using available model.")
            model_name = list(self.models.keys())[0]
        
        # Convert input to DataFrame with correct columns
        try:
            df = pd.DataFrame([booking_data])
            
            # Encode categorical variables if needed
            if self.preprocessing_objects:
                label_encoders = self.preprocessing_objects.get('label_encoders', {})
                for col, encoder in label_encoders.items():
                    if col in df.columns:
                        df[col + '_encoded'] = encoder.transform(df[col].astype(str))
            
            # Select features in correct order
            X = df[self.feature_columns].fillna(0)
            
            # Make prediction
            model = self.models[model_name]
            price = model.predict(X)[0]
            
            return max(20.0, float(price))  # Ensure minimum price
        
        except Exception as e:
            print(f"⚠️  Prediction error: {str(e)}")
            return None
    
    def predict_batch(self, bookings_df, model_name="ensemble"):
        """Predict prices for multiple bookings"""
        prices = []
        
        for _, row in bookings_df.iterrows():
            price = self.predict_price(row.to_dict(), model_name)
            if price:
                prices.append(price)
        
        return prices
    
    def get_available_models(self):
        """List available models"""
        return list(self.models.keys())


class RecommendationPredictor:
    """Load and use trained recommendation models"""
    
    def __init__(self, model_dir="./models/recommendations"):
        self.model_dir = Path(model_dir)
        self.models = {}
        self.item_features = None
        self.interactions = None
        self.load_models()
    
    def load_models(self):
        """Load all trained recommendation models"""
        print(f"📦 Loading recommendation models from {self.model_dir}...")
        
        # Load supporting data
        item_features_file = self.model_dir / "item_features.pkl"
        if item_features_file.exists():
            self.item_features = joblib.load(item_features_file)
            print(f"  ✓ Loaded {len(self.item_features)} item features")
        
        interactions_file = self.model_dir / "interactions.pkl"
        if interactions_file.exists():
            self.interactions = joblib.load(interactions_file)
            print(f"  ✓ Loaded {len(self.interactions)} interactions")
        
        # Load model files
        for model_file in self.model_dir.glob("recommendation_*.pkl"):
            if "item_features" in model_file.name or "interactions" in model_file.name:
                continue
            
            try:
                model = joblib.load(model_file)
                model_name = model_file.stem.replace("recommendation_", "").replace("_", " ")
                self.models[model_name] = model
                print(f"  ✓ Loaded {model_name}")
            except Exception as e:
                print(f"  ⚠️  Could not load {model_file.name}: {str(e)}")
        
        print(f"\n✅ Total models loaded: {len(self.models)}")
        return len(self.models) > 0
    
    def recommend(self, user_id, n_items=5, model_name="hybrid recommender"):
        """Get recommendations for a user
        
        Args:
            user_id: user identifier
            n_items: number of items to recommend
            model_name: which model to use (default: hybrid)
        
        Returns:
            list: recommended item IDs
        """
        
        if model_name not in self.models:
            print(f"⚠️  Model {model_name} not found. Using available model.")
            model_name = list(self.models.keys())[0]
        
        try:
            model = self.models[model_name]
            recommendations = model.recommend(user_id, n_items=n_items)
            
            items = [item for item, score in recommendations]
            return items
        
        except Exception as e:
            print(f"⚠️  Recommendation error: {str(e)}")
            return []
    
    def recommend_similar(self, item_id, n_items=5, model_name="content-based filtering"):
        """Recommend items similar to a given item
        
        Args:
            item_id: item identifier
            n_items: number of similar items to recommend
            model_name: which model to use
        
        Returns:
            list: similar item IDs
        """
        
        if model_name not in self.models:
            model_name = "content-based filtering"
        
        try:
            model = self.models[model_name]
            recommendations = model.recommend(item_id, n_items=n_items)
            
            items = [item for item, score in recommendations]
            return items
        
        except Exception as e:
            print(f"⚠️  Recommendation error: {str(e)}")
            return []
    
    def get_available_models(self):
        """List available models"""
        return list(self.models.keys())
    
    def get_item_details(self, item_id):
        """Get details for an item"""
        if self.item_features is None:
            return None
        
        try:
            item = self.item_features[self.item_features['id'] == item_id].iloc[0]
            return item.to_dict()
        except:
            return None


def demo():
    """Demo prediction usage"""
    
    print("\n" + "=" * 80)
    print("🧪 MODEL PREDICTION DEMO")
    print("=" * 80)
    
    # Pricing predictor
    print("\n💰 PRICING PREDICTIONS")
    print("-" * 80)
    
    try:
        pricer = PricingPredictor()
        
        # Sample booking
        sample_booking = {
            'day_of_week': 4,  # Friday
            'month': 7,  # July
            'review_scores_rating': 4.8,
            'accommodates': 2,
            'bedrooms': 1,
            'beds': 1,
            'available_binary': 1,
            'season': 'summer',
            'room_type': 'Entire home/apt',
            'city': 'london',
            'season_encoded': 2,
            'room_type_encoded': 0,
            'city_encoded': 1
        }
        
        print(f"Sample booking: {sample_booking}")
        
        for model_name in pricer.get_available_models()[:3]:
            price = pricer.predict_price(sample_booking, model_name)
            print(f"  {model_name}: ${price:.2f}")
    
    except Exception as e:
        print(f"⚠️  Pricing demo error: {str(e)}")
    
    # Recommendation predictor
    print("\n\n🎯 RECOMMENDATION PREDICTIONS")
    print("-" * 80)
    
    try:
        recommender = RecommendationPredictor()
        
        # Sample user (get from interactions if available)
        if recommender.interactions is not None and len(recommender.interactions) > 0:
            sample_user = recommender.interactions['reviewer_id'].iloc[0]
            
            print(f"Sample user: {sample_user}")
            
            for model_name in recommender.get_available_models()[:3]:
                items = recommender.recommend(sample_user, n_items=3, model_name=model_name)
                print(f"  {model_name}: {items}")
    
    except Exception as e:
        print(f"⚠️  Recommendation demo error: {str(e)}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo()
