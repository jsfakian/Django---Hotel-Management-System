#!/usr/bin/env python3
"""
NEPHELE Task 3 - Complete Algorithm Training & Evaluation
Master script to train all pricing and recommendation algorithms
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import AirbnbDataLoader
from train_pricing import PricingTrainer
from train_recommendations import RecommendationTrainer
from predict import PricingPredictor, RecommendationPredictor


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 90)
    print(f"  {title}")
    print("=" * 90)


def print_section(title):
    """Print formatted section"""
    print(f"\n{'─' * 90}")
    print(f"  {title}")
    print(f"{'─' * 90}\n")


class AlgorithmTrainer:
    """Master training orchestrator"""
    
    def __init__(self, output_base_dir="task3-algorithms/models"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
    
    def run_full_pipeline(self):
        """Run complete training pipeline"""
        
        print_header("🚀 NEPHELE TASK 3 - ALGORITHM TRAINING & EVALUATION")
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output directory: {self.output_base_dir.absolute()}")
        
        # Step 1: Load data
        print_section("STEP 1: LOAD REAL DATA")
        pricing_df, interactions_df, item_features_df = self._load_data()
        
        if pricing_df is None or len(pricing_df) == 0:
            print("⚠️  No pricing data available")
            return
        
        # Step 2: Train pricing algorithms
        print_section("STEP 2: TRAIN PRICING ALGORITHMS")
        pricing_results = self._train_pricing(pricing_df)
        
        # Step 3: Train recommendation algorithms
        if interactions_df is not None and len(interactions_df) > 0:
            print_section("STEP 3: TRAIN RECOMMENDATION ALGORITHMS")
            recommendation_results = self._train_recommendations(interactions_df, item_features_df)
        else:
            print("\n⚠️  No recommendation data available")
            recommendation_results = None
        
        # Step 4: Generate evaluation report
        print_section("STEP 4: EVALUATION & COMPARISON")
        self._generate_report(pricing_results, recommendation_results)
        
        # Step 5: Test predictions
        print_section("STEP 5: SAMPLE PREDICTIONS")
        self._test_predictions(pricing_df, interactions_df)
        
        print_header("✅ TRAINING COMPLETE")
        print(f"\nModels saved to: {self.output_base_dir.absolute()}")
        print("Ready for deployment and integration!")
    
    def _load_data(self):
        """Load real data from Airbnb and synthetic data for pricing"""
        
        loader = AirbnbDataLoader()
        listings, calendar, reviews = loader.load_all_cities()
        
        # Try to prepare pricing data from real data
        print("\n📈 Attempting to load pricing data...")
        pricing_df = loader.prepare_pricing_data()
        
        # If real pricing data is not available, use synthetic
        if pricing_df is None or len(pricing_df) == 0:
            print("  ⚠️  Real pricing data not available in Airbnb dataset")
            print("  📚 Loading synthetic pricing data instead...\n")
            synthetic_bookings, synthetic_prefs, synthetic_pricing = loader.get_synthetic_data()
            
            if synthetic_bookings is not None and len(synthetic_bookings) > 0:
                # Create pricing DataFrame from synthetic bookings
                pricing_df = synthetic_bookings[[
                    'price',  'lead_time', 'stays_in_weekend_nights', 'stays_in_week_nights',
                    'adults', 'children', 'babies', 'booking_changes', 'is_repeated_guest',
                    'previous_cancellations', 'adr', 'booking_status'
                ]].copy()
                
                # Rename columns to match expected features
                pricing_df.columns = ['price', 'lead_time', 'weekend_nights', 'week_nights',
                                      'adults', 'children', 'babies', 'changes', 'repeat_guest',
                                      'cancellations', 'adr', 'booking_status']
                
                # Add derived features
                pricing_df['day_of_week'] = np.random.randint(0, 7, len(pricing_df))
                pricing_df['month'] = np.random.randint(1, 13, len(pricing_df))
                pricing_df['season'] = pricing_df['month'].apply(lambda m: 'summer' if m in [6,7,8] else ('winter' if m in [12,1,2] else ('spring' if m in [3,4,5] else 'fall')))
                pricing_df['room_type'] = np.random.choice(['Entire home/apt', 'Private room', 'Shared room'], len(pricing_df))
                pricing_df['city'] = np.random.choice(['london', 'barcelona', 'new-york-city'], len(pricing_df))
                
                print(f"  ✓ Loaded {len(pricing_df):,} synthetic pricing records")
        else:
            print(f"  ✓ {len(pricing_df):,} real pricing records")
        
        # Prepare recommendation data
        print("\n🔍 Preparing recommendation data...")
        interactions_df, item_features_df = loader.prepare_recommendation_data()
        if interactions_df is not None:
            print(f"  ✓ {len(interactions_df):,} interaction records")
            print(f"  ✓ {len(item_features_df):,} item features")
        
        return pricing_df, interactions_df, item_features_df
    
    def _train_pricing(self, pricing_df):
        """Train pricing models"""
        
        print("Starting pricing model training...")
        
        trainer = PricingTrainer(output_dir=str(self.output_base_dir / "pricing"))
        algorithms, results, X_train, X_test, y_train, y_test = trainer.train_all_models(pricing_df)
        
        trainer.print_summary(results)
        
        self.results['pricing'] = {
            'trainer': trainer,
            'models': algorithms,
            'results': results,
            'train_size': len(X_train),
            'test_size': len(X_test)
        }
        
        return results
    
    def _train_recommendations(self, interactions_df, item_features_df):
        """Train recommendation models"""
        
        print("Starting recommendation model training...")
        
        trainer = RecommendationTrainer(output_dir=str(self.output_base_dir / "recommendations"))
        algorithms, results = trainer.train_all_models(interactions_df, item_features_df)
        
        trainer.print_summary(interactions_df, item_features_df)
        
        self.results['recommendations'] = {
            'trainer': trainer,
            'models': algorithms,
            'interaction_count': len(interactions_df),
            'item_count': len(item_features_df)
        }
        
        return results
    
    def _generate_report(self, pricing_results, recommendation_results):
        """Generate evaluation report"""
        
        report_lines = [
            "NEPHELE Task 3 - Algorithm Training Report",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "PRICING MODELS",
            "-" * 80,
        ]
        
        if pricing_results:
            for model_name, metrics in pricing_results.items():
                report_lines.append(f"\n{model_name}:")
                report_lines.append(f"  MAE: ${metrics['MAE']:.2f}")
                report_lines.append(f"  RMSE: ${metrics['RMSE']:.2f}")
                report_lines.append(f"  R²: {metrics['R²']:.4f}")
                report_lines.append(f"  MAPE: {metrics['MAPE']:.2f}%")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("RECOMMENDATION MODELS")
        report_lines.append("-" * 80)
        
        if recommendation_results and 'recommendations' in self.results:
            rec_data = self.results['recommendations']
            report_lines.append(f"\nModels trained: {len(rec_data['models'])}")
            report_lines.append(f"Total users: {rec_data['interaction_count']:,}")
            report_lines.append(f"Total items: {rec_data['item_count']:,}")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append("NEXT STEPS")
        report_lines.append("-" * 80)
        report_lines.append("1. Review model performance metrics")
        report_lines.append("2. Test predictions using predict.py")
        report_lines.append("3. Integrate models with Django")
        report_lines.append("4. Deploy to production")
        
        # Save report
        report_text = "\n".join(report_lines)
        report_file = self.output_base_dir / "TRAINING_REPORT.txt"
        report_file.write_text(report_text)
        
        print(report_text)
        print(f"\n✓ Report saved to: {report_file}")
    
    def _test_predictions(self, pricing_df, interactions_df):
        """Test trained models with sample predictions"""
        
        print("Testing pricing predictions...")
        try:
            pricer = PricingPredictor(model_dir=str(self.output_base_dir / "pricing"))
            
            # Test prediction
            sample = pricing_df.iloc[0].to_dict()
            for model in list(pricer.get_available_models())[:3]:
                price = pricer.predict_price(sample, model_name=model)
                if price:
                    print(f"  ✓ {model}: ${price:.2f}")
        except Exception as e:
            print(f"  ⚠️  {str(e)}")
        
        if interactions_df is not None and len(interactions_df) > 0:
            print("\nTesting recommendation predictions...")
            try:
                recommender = RecommendationPredictor(
                    model_dir=str(self.output_base_dir / "recommendations")
                )
                
                # Test recommendation
                sample_user = interactions_df['reviewer_id'].iloc[0]
                for model in list(recommender.get_available_models())[:2]:
                    recs = recommender.recommend(sample_user, n_items=3, model_name=model)
                    if recs:
                        print(f"  ✓ {model}: {len(recs)} recommendations")
            except Exception as e:
                print(f"  ⚠️  {str(e)}")


def main():
    """Main entry point"""
    
    try:
        trainer = AlgorithmTrainer()
        trainer.run_full_pipeline()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n⚠️  Training interrupted by user")
        return 1
    
    except Exception as e:
        print(f"\n❌ Training failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
