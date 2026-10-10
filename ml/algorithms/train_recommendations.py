#!/usr/bin/env python3
"""
NEPHELE Task 3 - Train All Recommendation Algorithms
Loads real Airbnb data and trains multiple recommendation models
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import AirbnbDataLoader
from recommendation_algorithms import (
    CollaborativeFiltering,
    ContentBasedFiltering,
    HybridRecommender,
    AssociationRulesRecommender,
    NeuralCollaborativeFiltering,
    compare_recommendation_algorithms
)


class RecommendationTrainer:
    """Training pipeline for recommendation algorithms"""
    
    def __init__(self, output_dir="./models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.models = {}
    
    def train_all_models(self, interactions_df, item_features_df):
        """Train all recommendation models"""
        
        print("\n" + "=" * 80)
        print("📊 RECOMMENDATION MODEL TRAINING PIPELINE")
        print("=" * 80)
        print(f"\nInteractions: {len(interactions_df):,} records")
        print(f"Users: {interactions_df['reviewer_id'].nunique()}")
        print(f"Items: {interactions_df['listing_id'].nunique()}")
        print(f"Item features: {len(item_features_df)} items")
        
        # Train models
        algorithms, results = compare_recommendation_algorithms(interactions_df, item_features_df)
        
        # Save models
        print("\n💾 Saving models...")
        for name, algo in algorithms.items():
            try:
                model_path = self.output_dir / f"recommendation_{name.lower().replace(' ', '_')}.pkl"
                algo.save(model_path)
                self.models[name] = algo
            except Exception as e:
                print(f"  ⚠️  Could not save {name}: {str(e)}")
        
        # Save supporting data
        joblib.dump(item_features_df, self.output_dir / "item_features.pkl")
        joblib.dump(interactions_df, self.output_dir / "interactions.pkl")
        print(f"  ✓ Supporting data saved")
        
        return algorithms, results
    
    def print_summary(self, interactions_df, item_features_df):
        """Print training summary"""
        print("\n" + "=" * 80)
        print("📊 RECOMMENDATION SYSTEM SUMMARY")
        print("=" * 80)
        
        print(f"\n✓ Models trained: {len(self.models)}")
        print(f"✓ Total users: {interactions_df['reviewer_id'].nunique():,}")
        print(f"✓ Total items: {interactions_df['listing_id'].nunique():,}")
        print(f"✓ Total interactions: {len(interactions_df):,}")
        print(f"✓ Average rating: {interactions_df['rating'].mean():.2f}")
        print(f"✓ Sparsity: {(1 - len(interactions_df) / (interactions_df['reviewer_id'].nunique() * interactions_df['listing_id'].nunique())) * 100:.2f}%")
        
        print(f"\n📦 Models:")
        for name in self.models.keys():
            print(f"  • {name}")
        
        print("\n" + "=" * 80)


def main():
    """Main training pipeline"""
    
    # Load data
    print("\n" + "=" * 80)
    print("🚀 RECOMMENDATION ALGORITHM TRAINING")
    print("=" * 80)
    
    loader = AirbnbDataLoader()
    listings, calendar, reviews = loader.load_all_cities()
    
    # Prepare recommendation data
    interactions_df, item_features_df = loader.prepare_recommendation_data()
    
    if len(interactions_df) == 0:
        print("\n⚠️  No interaction data available")
        return
    
    # Create trainer
    trainer = RecommendationTrainer(output_dir="./models/recommendations")
    
    # Train models
    algorithms, results = trainer.train_all_models(interactions_df, item_features_df)
    
    # Print summary
    trainer.print_summary(interactions_df, item_features_df)
    
    # Test recommendations
    print("\n" + "=" * 80)
    print("🧪 SAMPLE RECOMMENDATIONS")
    print("=" * 80)
    
    # Get sample user
    sample_users = interactions_df['reviewer_id'].unique()[:3]
    
    for user_id in sample_users:
        print(f"\n👤 User {user_id}:")
        
        # Hybrid recommender
        if 'Hybrid Recommender' in trainer.models:
            try:
                recs = trainer.models['Hybrid Recommender'].recommend(user_id, n_items=3)
                print(f"  Recommendations: {[item for item, _ in recs]}")
            except:
                pass
    
    print("\n✅ Recommendation training completed!")
    print(f"Models saved to: {trainer.output_dir.absolute()}")
    
    return trainer


if __name__ == "__main__":
    trainer = main()
