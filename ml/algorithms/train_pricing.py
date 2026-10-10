#!/usr/bin/env python3
"""
NEPHELE Task 3 - Train All Pricing Algorithms
Loads real Airbnb data and trains multiple pricing models
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import AirbnbDataLoader
from pricing_algorithms import (
    LinearRegressionPricer,
    GradientBoostingPricer,
    NeuralNetworkPricer,
    SeasonalPricer,
    EnsemblePricer,
    compare_pricing_algorithms
)


class PricingTrainer:
    """Training pipeline for pricing algorithms"""
    
    def __init__(self, output_dir="./models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.models = {}
        self.preprocessing_objects = {}
    
    def prepare_features(self, df):
        """Prepare features for training"""

        df = df.copy()
        default_numeric_features = {
            'day_of_week': 0,
            'month': 1,
            'review_scores_rating': 4.5,
            'accommodates': 2,
            'bedrooms': 1,
            'beds': 1,
            'available_binary': 1,
            'lead_time': 7,
            'weekend_nights': 1,
            'week_nights': 2,
            'adults': 2,
            'children': 0,
            'changes': 0,
            'repeat_guest': 0,
            'cancellations': 0,
        }
        for feature_name, default_value in default_numeric_features.items():
            if feature_name not in df.columns:
                df[feature_name] = default_value
        
        # Available features based on data source
        feature_cols = []
        
        # Try to use available columns
        for col in ['day_of_week', 'month', 'review_scores_rating', 'accommodates', 'bedrooms', 'beds', 'available_binary',
                   'lead_time', 'weekend_nights', 'week_nights', 'adults', 'children', 'changes', 'repeat_guest', 'cancellations']:
            if col in df.columns:
                feature_cols.append(col)
        
        # Ensure at least some numeric features
        if len(feature_cols) < 3:
            feature_cols = [c for c in df.columns if c != 'price'][:5]
        
        # Handle categorical features
        categorical_cols = [col for col in ['season', 'room_type', 'city', 'booking_status'] if col in df.columns]
        
        # Create a copy for processing
        df_processed = df.copy()
        
        # Encode categorical variables
        label_encoders = {}
        for col in categorical_cols:
            try:
                le = LabelEncoder()
                df_processed[col + '_encoded'] = le.fit_transform(df_processed[col].astype(str))
                label_encoders[col] = le
                feature_cols.append(col + '_encoded')
            except:
                pass
        
        # Save encoders
        self.preprocessing_objects['label_encoders'] = label_encoders
        
        # Handle missing values
        for col in feature_cols:
            if col in df_processed.columns:
                df_processed[col] = df_processed[col].fillna(df_processed[col].median())
        
        # Ensure all feature columns exist
        feature_cols = [c for c in feature_cols if c in df_processed.columns]
        
        if len(feature_cols) == 0:
            print("  ⚠️  No valid features found, using random subset")
            feature_cols = [c for c in df_processed.columns if c != 'price'][:5]
        
        print(f"  ✓ Using features: {feature_cols}")
        
        X = df_processed[feature_cols]
        y = df_processed['price']
        
        return X, y, feature_cols
    
    def train_all_models(self, pricing_df):
        """Train all pricing models"""
        
        print("\n" + "=" * 80)
        print("📊 PRICING MODEL TRAINING PIPELINE")
        print("=" * 80)
        print(f"\nDataset size: {len(pricing_df):,} records")
        print(f"Price range: ${pricing_df['price'].min():.2f} - ${pricing_df['price'].max():.2f}")
        print(f"Mean price: ${pricing_df['price'].mean():.2f}")
        
        # Prepare features
        print("\n🔧 Preparing features...")
        X, y, feature_cols = self.prepare_features(pricing_df)
        print(f"  ✓ Features: {len(feature_cols)}")
        
        # Split data
        print("\n✂️  Splitting data...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        print(f"  ✓ Training: {len(X_train):,} records")
        print(f"  ✓ Testing: {len(X_test):,} records")
        
        # Train models
        algorithms, results = compare_pricing_algorithms(X_train, X_test, y_train, y_test)
        
        # Save results
        print("\n💾 Saving models...")
        for name, algo in algorithms.items():
            try:
                model_path = self.output_dir / f"pricing_{name.lower().replace(' ', '_')}.pkl"
                algo.save(model_path)
                self.models[name] = algo
            except Exception as e:
                print(f"  ⚠️  Could not save {name}: {str(e)}")
        
        # Save feature names and encoders
        joblib.dump(feature_cols, self.output_dir / "pricing_feature_columns.pkl")
        joblib.dump(self.preprocessing_objects, self.output_dir / "pricing_preprocessing.pkl")
        print(f"  ✓ Preprocessing objects saved")
        
        return algorithms, results, X_train, X_test, y_train, y_test
    
    def print_summary(self, results):
        """Print training summary"""
        print("\n" + "=" * 80)
        print("📈 PRICING MODEL PERFORMANCE SUMMARY")
        print("=" * 80)
        
        summary_data = []
        for model_name, metrics in results.items():
            summary_data.append({
                'Model': model_name,
                'MAE': f"${metrics['MAE']:.2f}",
                'RMSE': f"${metrics['RMSE']:.2f}",
                'R²': f"{metrics['R²']:.4f}",
                'MAPE': f"{metrics['MAPE']:.2f}%"
            })
        
        summary_df = pd.DataFrame(summary_data)
        print("\n" + summary_df.to_string(index=False))
        
        # Find best model
        best_model = min(results.items(), key=lambda x: x[1]['RMSE'])
        print(f"\n🏆 Best Model: {best_model[0]} (RMSE: ${best_model[1]['RMSE']:.2f})")
        
        print("\n" + "=" * 80)
        
        # Save summary to file
        summary_df.to_csv(self.output_dir / "pricing_model_comparison.csv", index=False)
        print(f"✓ Summary saved to: {self.output_dir / 'pricing_model_comparison.csv'}")


def main():
    """Main training pipeline"""
    
    # Load data
    print("\n" + "=" * 80)
    print("🚀 PRICING ALGORITHM TRAINING")
    print("=" * 80)
    
    loader = AirbnbDataLoader()
    listings, calendar, reviews = loader.load_all_cities()
    
    # Prepare pricing data
    pricing_df = loader.prepare_pricing_data(sample_size=50000)
    
    if len(pricing_df) == 0:
        print("\n⚠️  No pricing data available")
        return
    
    # Create trainer
    trainer = PricingTrainer(output_dir="./models/pricing")
    
    # Train models
    algorithms, results, X_train, X_test, y_train, y_test = trainer.train_all_models(pricing_df)
    
    # Print summary
    trainer.print_summary(results)
    
    print("\n✅ Pricing training completed!")
    print(f"Models saved to: {trainer.output_dir.absolute()}")
    
    return trainer


if __name__ == "__main__":
    trainer = main()
