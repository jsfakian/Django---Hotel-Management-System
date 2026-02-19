"""
Pricing Service - AI-Powered Dynamic Pricing

Provides intelligent pricing recommendations using trained ML models.
Per PRICING_MODULE_FE_REDESIGN_PLAN.md - Phase 1 Backend Implementation
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta
import traceback

from django.db.models import Avg, Q, Min, Max
from room.models import Room
from bookings.models import PricingHistory


class PricingPredictor:
    """
    Load and use trained pricing models from Task 3.
    Wraps task3-algorithms/predict.py PricingPredictor class.
    """
    
    def __init__(self, model_dir=None):
        """Initialize pricing predictor with trained models."""
        if model_dir is None:
            # Default path relative to Django project
            model_dir = Path(__file__).resolve().parent.parent.parent / "task3-algorithms" / "models" / "pricing"
        
        self.model_dir = Path(model_dir)
        self.models = {}
        self.feature_columns = None
        self.preprocessing_objects = None
        self.available = False
        
        try:
            self._load_models()
            self.available = True
        except Exception as e:
            print(f"⚠️  Warning: Pricing models not available: {str(e)}")
            self.available = False
    
    def _load_models(self):
        """Load all trained pricing models."""
        import joblib
        
        if not self.model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")
        
        # Load feature columns
        features_file = self.model_dir / "pricing_feature_columns.pkl"
        if features_file.exists():
            self.feature_columns = joblib.load(features_file)
        
        # Load preprocessing objects
        preprocessing_file = self.model_dir / "pricing_preprocessing.pkl"
        if preprocessing_file.exists():
            self.preprocessing_objects = joblib.load(preprocessing_file)
        
        # Load model files
        model_files = {
            'ensemble': 'pricing_ensemble.pkl',
            'gradient_boosting': 'pricing_gradient_boosting.pkl',
            'neural_network': 'pricing_neural_network.pkl',
            'linear_regression': 'pricing_linear_regression.pkl',
            'seasonal_pricing': 'pricing_seasonal_pricing.pkl',
        }
        
        for model_name, filename in model_files.items():
            model_file = self.model_dir / filename
            if model_file.exists():
                try:
                    self.models[model_name] = joblib.load(model_file)
                except Exception as e:
                    print(f"⚠️  Could not load {model_name}: {str(e)}")
    
    def predict(self, features_dict, model_name='ensemble'):
        """
        Predict price using specified model.
        
        Args:
            features_dict: Dictionary with features (occupancy, season, weekday, etc.)
            model_name: Which model to use
        
        Returns:
            Predicted price (float) or None if models not available
        """
        if not self.available or model_name not in self.models:
            return None
        
        try:
            model = self.models[model_name]
            # Simple prediction - models expect simple input
            # This is a simplified version; actual implementation depends on model format
            if hasattr(model, 'predict'):
                # Try to create feature array
                feature_values = [features_dict.get(col, 0) for col in self.feature_columns] if self.feature_columns else []
                if feature_values:
                    prediction = float(model.predict([feature_values])[0])
                    return max(prediction, 0)  # Ensure non-negative
            return None
        except Exception as e:
            print(f"Error predicting with {model_name}: {str(e)}")
            return None
    
    def get_available_models(self):
        """Return list of available models."""
        return list(self.models.keys())


class PricingAnalyzer:
    """
    Analyze room pricing and provide recommendations.
    Combines AI predictions with market analysis.
    """
    
    def __init__(self):
        """Initialize pricing analyzer."""
        self.predictor = PricingPredictor()
    
    def get_pricing_recommendation(self, room_id, date_obj, occupancy_rate=None, season=None):
        """
        Get AI pricing recommendation for a room on a specific date.
        
        Args:
            room_id: Room ID
            date_obj: Python date object
            occupancy_rate: Optional occupancy rate (0-100)
            season: Optional season string (low, medium, high, peak)
        
        Returns:
            Dictionary with:
            - ensemble_prediction: Recommended price
            - confidence: Confidence score (0-1)
            - factors: Factor analysis
            - all_predictions: Predictions from each model
            - competitor_price: Market competitor price
            - market_range: Min/max market prices
        """
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return None
        
        # Get occupancy rate if not provided
        if occupancy_rate is None:
            occupancy_rate = self._estimate_occupancy(room, date_obj)
        
        # Get season if not provided
        if season is None:
            season = self._get_season(date_obj)
        
        # Build features dictionary
        features = {
            'occupancy': occupancy_rate / 100 if occupancy_rate > 1 else occupancy_rate,
            'season': self._encode_season(season),
            'weekday': date_obj.weekday(),
            'room_type': room.room_type,
            'accommodates': room.capacity,
        }
        
        # Get predictions from all models
        all_predictions = {}
        if self.predictor.available:
            for model_name in self.predictor.get_available_models():
                pred = self.predictor.predict(features, model_name)
                if pred:
                    all_predictions[model_name] = float(pred)
        
        # Use ensemble or average if available
        ensemble_pred = all_predictions.get('ensemble')
        if not ensemble_pred and all_predictions:
            ensemble_pred = sum(all_predictions.values()) / len(all_predictions)
        
        if not ensemble_pred:
            # Fallback to base price with adjustments
            ensemble_pred = float(room.base_price) * (1 + (occupancy_rate / 100 * 0.15))
        
        # Get confidence score
        confidence = self._get_confidence_score(room, date_obj)
        
        # Calculate pricing factors
        factors = self._calculate_pricing_factors(
            room, ensemble_pred, occupancy_rate, season, date_obj
        )
        
        # Get competitor pricing
        competitor_price = self._get_competitor_price(room, date_obj)
        
        # Get market range
        market_range = self._get_market_range(room, date_obj)
        
        return {
            'ensemble_prediction': float(ensemble_pred),
            'confidence': float(confidence),
            'factors': factors,
            'all_predictions': all_predictions,
            'competitor_price': float(competitor_price) if competitor_price else None,
            'market_range': market_range,
            'room_id': room.id,
            'room_number': room.room_number,
            'date': str(date_obj),
            'season': season,
            'occupancy_rate': occupancy_rate,
        }
    
    def _estimate_occupancy(self, room, date_obj):
        """Estimate occupancy rate for a room on a given date."""
        from room.models import Booking
        
        bookings_count = Booking.objects.filter(
            room=room,
            check_in__lte=date_obj,
            check_out__gt=date_obj,
            status__in=['confirmed', 'checked_in']
        ).count()
        
        # Simple estimate - 0 bookings = 0%, 1+ = estimate based on historical
        if bookings_count > 0:
            return min(75.0, 50.0 + (bookings_count * 10))
        
        # Check historical occupancy
        avg_occupancy = PricingHistory.objects.filter(
            room=room,
            occupancy_rate__isnull=False
        ).values('occupancy_rate').aggregate(avg=Avg('occupancy_rate'))
        
        if avg_occupancy['avg']:
            return float(avg_occupancy['avg'])
        
        return 50.0  # Default estimate
    
    def _get_season(self, date_obj):
        """Determine season from date."""
        month = date_obj.month
        
        if month in [12, 1, 2]:  # Winter
            return 'peak'
        elif month in [6, 7, 8]:  # Summer
            return 'peak'
        elif month in [3, 4, 5]:  # Spring
            return 'high'
        elif month in [9, 10, 11]:  # Fall
            return 'medium'
        
        return 'medium'
    
    def _encode_season(self, season_str):
        """Encode season string to numeric value."""
        season_map = {'low': 0, 'medium': 1, 'high': 2, 'peak': 3}
        return season_map.get(season_str, 1)
    
    def _get_confidence_score(self, room, date_obj):
        """Get confidence score from recent pricing history."""
        recent = PricingHistory.objects.filter(
            room=room,
            date__gte=date_obj - timedelta(days=30),
            confidence_score__isnull=False
        ).values('confidence_score').aggregate(avg=Avg('confidence_score'))
        
        if recent['avg']:
            return float(recent['avg'])
        
        return 0.85  # Default confidence
    
    def _calculate_pricing_factors(self, room, final_price, occupancy_rate, season, date_obj):
        """
        Calculate and breakdown pricing factors.
        
        Returns:
            Dictionary with factor impacts in dollars and percentages
        """
        base_price = float(room.base_price)
        
        # Calculate each factor's impact
        occupancy_impact = (occupancy_rate / 100.0) * (base_price * 0.15)  # 15% max impact
        
        season_multiplier = {'low': 0.90, 'medium': 1.0, 'high': 1.20, 'peak': 1.35}.get(season, 1.0)
        season_impact = base_price * (season_multiplier - 1)
        
        # Demand based on bookings
        from room.models import Booking
        recent_bookings = Booking.objects.filter(
            room=room,
            created_at__gte=datetime.now() - timedelta(days=7),
            status__in=['confirmed', 'checked_in']
        ).count()
        demand_impact = min(base_price * 0.20, recent_bookings * 5)  # Max 20% demand impact
        
        # Competitor impact (simplified)
        competitor_price = self._get_competitor_price(room, date_obj)
        competitor_impact = 0
        if competitor_price:
            price_diff = float(competitor_price) - base_price
            if price_diff > 0:
                competitor_impact = price_diff * 0.3  # 30% of difference
            else:
                competitor_impact = price_diff * 0.5  # 50% discount if below
        
        return {
            'base_price': float(base_price),
            'occupancy_impact_dollars': float(occupancy_impact),
            'occupancy_impact_percent': float((occupancy_impact / base_price) * 100 if base_price > 0 else 0),
            'season_impact_dollars': float(season_impact),
            'season_impact_percent': float((season_impact / base_price) * 100 if base_price > 0 else 0),
            'demand_impact_dollars': float(demand_impact),
            'demand_impact_percent': float((demand_impact / base_price) * 100 if base_price > 0 else 0),
            'competitor_impact_dollars': float(competitor_impact),
            'competitor_impact_percent': float((competitor_impact / base_price) * 100 if base_price > 0 else 0),
            'total_impact_dollars': float(occupancy_impact + season_impact + demand_impact + competitor_impact),
        }
    
    def _get_competitor_price(self, room, date_obj):
        """Get competitor price for same room type on same date."""
        # Look for recent pricing history with competitor data
        recent = PricingHistory.objects.filter(
            room__property=room.property,
            room__room_type=room.room_type,
            date__gte=date_obj - timedelta(days=7),
            competitor_price__isnull=False
        ).values('competitor_price').aggregate(avg=Avg('competitor_price'))
        
        if recent['avg']:
            return Decimal(str(recent['avg']))
        
        return None
    
    def _get_market_range(self, room, date_obj):
        """Get market price range for room type on this date."""
        # Get min/max from recent pricing history
        history = PricingHistory.objects.filter(
            room__property=room.property,
            room__room_type=room.room_type,
            date__gte=date_obj - timedelta(days=30)
        ).aggregate(
            min_price=Min('base_price'),
            max_price=Max('dynamic_price')
        )
        
        return {
            'min': float(history.get('min_price') or 0),
            'max': float(history.get('max_price') or 0),
            'average': float(room.base_price),
        }
    
    def analyze_scenario(self, room_id, date_obj, **overrides):
        """
        Analyze a pricing scenario with overridden parameters.
        
        Args:
            room_id: Room ID
            date_obj: Date to analyze
            **overrides: Override parameters (occupancy_rate, season, competitor_price)
        
        Returns:
            Recommendation dictionary with scenario price
        """
        recommendation = self.get_pricing_recommendation(
            room_id,
            date_obj,
            occupancy_rate=overrides.get('occupancy_rate'),
            season=overrides.get('season'),
        )
        
        if overrides.get('competitor_price'):
            # Adjust for competitor price override
            competitor_price = float(overrides['competitor_price'])
            current_price = recommendation['ensemble_prediction']
            room = Room.objects.get(id=room_id)
            
            # Simple adjustment: move 30% toward competitor if higher
            if competitor_price > float(room.base_price):
                adjustment = (competitor_price - float(room.base_price)) * 0.3
                recommendation['ensemble_prediction'] = float(current_price) + adjustment
        
        return recommendation
    
    def get_historical_trend(self, room_id, days=30):
        """
        Get historical pricing trend for a room.
        
        Args:
            room_id: Room ID
            days: Number of days to retrieve
        
        Returns:
            List of pricing records with statistics
        """
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return []
        
        start_date = datetime.now().date() - timedelta(days=days)
        
        history = PricingHistory.objects.filter(
            room=room,
            date__gte=start_date
        ).values(
            'date', 'base_price', 'dynamic_price', 'competitor_price',
            'occupancy_rate', 'demand_score', 'season'
        ).order_by('date')
        
        data = list(history)
        
        # Calculate statistics
        if data:
            prices = [float(h.get('dynamic_price') or h.get('base_price') or 0) for h in data]
            from statistics import mean, stdev
            
            stats = {
                'count': len(prices),
                'min': min(prices),
                'max': max(prices),
                'average': mean(prices),
                'std_dev': stdev(prices) if len(prices) > 1 else 0,
            }
        else:
            stats = {'count': 0}
        
        return {
            'room_id': room_id,
            'room_number': room.room_number,
            'date_range': {
                'from': str(start_date),
                'to': str(datetime.now().date()),
            },
            'history': data,
            'statistics': stats,
        }


# Global instance for easy access
_analyzer = None

def get_pricing_analyzer():
    """Get or create global pricing analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = PricingAnalyzer()
    return _analyzer
