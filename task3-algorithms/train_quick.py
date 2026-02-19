#!/usr/bin/env python3
"""
NEPHELE Task 3 - Quick Algorithm Training Demo
Fast version with sampled data for quick validation
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent))

from data_loader import AirbnbDataLoader
from train_pricing import PricingTrainer
from train_recommendations import RecommendationTrainer


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 90)
    print(f"  {title}")
    print("=" * 90)


def main():
    """Run quick demo training"""
    
    print_header("🚀 NEPHELE TASK 3 - QUICK ALGORITHM TRAINING")
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load data
    print("\n📊 Loading real data...")
    loader = AirbnbDataLoader()
    listings, calendar, reviews = loader.load_all_cities()
    
    # Small pricing dataset from real data
    print("\n💰 PRICING MODEL TRAINING")
    print("-" * 90)
    pricing_df = loader.prepare_pricing_data(sample_size=5000)
    
    if len(pricing_df) > 0:
        trainer = PricingTrainer(output_dir="./models/pricing")
        algorithms, results, _, _, _, _ = trainer.train_all_models(pricing_df)
        trainer.print_summary(results)
    else:
        print("⚠️  No pricing data available")
    
    # Recommendations with sampled interaction data
    print("\n\n🎯 RECOMMENDATION MODEL TRAINING (SAMPLED)")
    print("-" * 90)
    
    interactions_df, item_features_df = loader.prepare_recommendation_data()
    
    if len(interactions_df) > 0:
        # Sample for faster training
        print(f"Original interactions: {len(interactions_df):,}")
        interactions_df = interactions_df.sample(n=min(100000, len(interactions_df)), random_state=42)
        print(f"Sampled interactions: {len(interactions_df):,}")
        
        trainer = RecommendationTrainer(output_dir="./models/recommendations")
        algorithms, results = trainer.train_all_models(interactions_df, item_features_df)
        trainer.print_summary(interactions_df, item_features_df)
    else:
        print("⚠️  No interaction data available")
    
    print_header("✅ TRAINING COMPLETE")
    print(f"\nModels saved to: {Path('./models').absolute()}")
    print("\nModels are ready for:")
    print("  ✓ Price prediction")
    print("  ✓ Personalized recommendations")
    print("  ✓ Django integration")
    print("  ✓ Production deployment")


if __name__ == "__main__":
    main()
