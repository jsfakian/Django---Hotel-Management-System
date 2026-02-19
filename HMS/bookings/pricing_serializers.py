"""
Serializers for Pricing API endpoints.
"""

from rest_framework import serializers


class PricingFactorsSerializer(serializers.Serializer):
    """Pricing factors breakdown."""
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    occupancy_impact_dollars = serializers.DecimalField(max_digits=10, decimal_places=2)
    occupancy_impact_percent = serializers.DecimalField(max_digits=6, decimal_places=2)
    season_impact_dollars = serializers.DecimalField(max_digits=10, decimal_places=2)
    season_impact_percent = serializers.DecimalField(max_digits=6, decimal_places=2)
    demand_impact_dollars = serializers.DecimalField(max_digits=10, decimal_places=2)
    demand_impact_percent = serializers.DecimalField(max_digits=6, decimal_places=2)
    competitor_impact_dollars = serializers.DecimalField(max_digits=10, decimal_places=2)
    competitor_impact_percent = serializers.DecimalField(max_digits=6, decimal_places=2)
    total_impact_dollars = serializers.DecimalField(max_digits=10, decimal_places=2)


class MarketRangeSerializer(serializers.Serializer):
    """Market price range."""
    min = serializers.DecimalField(max_digits=10, decimal_places=2)
    max = serializers.DecimalField(max_digits=10, decimal_places=2)
    average = serializers.DecimalField(max_digits=10, decimal_places=2)


class PricingRecommendationSerializer(serializers.Serializer):
    """AI Pricing recommendation response."""
    room_id = serializers.IntegerField()
    room_number = serializers.CharField(max_length=20)
    date = serializers.CharField()
    season = serializers.CharField(max_length=20)
    occupancy_rate = serializers.DecimalField(max_digits=6, decimal_places=2)
    
    # Predictions
    ensemble_prediction = serializers.DecimalField(max_digits=10, decimal_places=2)
    confidence = serializers.DecimalField(max_digits=5, decimal_places=4)
    all_predictions = serializers.DictField(child=serializers.DecimalField(max_digits=10, decimal_places=2))
    
    # Analysis
    factors = PricingFactorsSerializer()
    competitor_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    market_range = MarketRangeSerializer()


class PricingHistoryItemSerializer(serializers.Serializer):
    """Single pricing history item."""
    date = serializers.DateField()
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    dynamic_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    competitor_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    occupancy_rate = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    demand_score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    season = serializers.CharField(max_length=20, allow_null=True)


class PricingHistoryStatisticsSerializer(serializers.Serializer):
    """Statistics for pricing history."""
    count = serializers.IntegerField()
    min = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    average = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    std_dev = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class PricingHistoryResponseSerializer(serializers.Serializer):
    """Full pricing history response."""
    room_id = serializers.IntegerField()
    room_number = serializers.CharField(max_length=20)
    date_range = serializers.DictField()
    history = PricingHistoryItemSerializer(many=True)
    statistics = PricingHistoryStatisticsSerializer()


class ScenarioAnalysisRequestSerializer(serializers.Serializer):
    """Scenario analysis request."""
    room_id = serializers.IntegerField()
    date = serializers.DateField()
    occupancy_rate = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True)
    season = serializers.CharField(max_length=20, required=False, allow_blank=True)
    competitor_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)


class ScenarioAnalysisResponseSerializer(PricingRecommendationSerializer):
    """Scenario analysis response (extends recommendation)."""
    price_change = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    price_change_percent = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    revenue_impact_per_night = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    revenue_impact_per_3night_stay = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
