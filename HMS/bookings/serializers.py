"""
Serializers for bookings app models (pricing, demand forecasts)

Per Task 4 & Task 3: Dynamic Pricing Algorithm
"""

from rest_framework import serializers
from bookings.models import (
    PricingHistory, DemandForecast, CompetitorPrice
)


class PricingHistorySerializer(serializers.ModelSerializer):
    """Serializer for PricingHistory model"""
    
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    
    class Meta:
        model = PricingHistory
        fields = [
            'id', 'room', 'room_number', 'date', 'weekday',
            'base_price', 'dynamic_price', 'competitor_price',
            'occupancy_rate', 'demand_score', 'bookings_count',
            'cancellation_rate', 'season', 'external_events',
            'predicted_by_model', 'model_version', 'confidence_score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DemandForecastSerializer(serializers.ModelSerializer):
    """Serializer for DemandForecast model"""
    
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    
    class Meta:
        model = DemandForecast
        fields = [
            'id', 'room', 'room_number', 'forecast_date',
            'forecast_for_date', 'predicted_occupancy',
            'predicted_demand_score', 'recommended_price',
            'confidence', 'model_name', 'model_version',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CompetitorPriceSerializer(serializers.ModelSerializer):
    """Serializer for CompetitorPrice model"""
    
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    
    class Meta:
        model = CompetitorPrice
        fields = [
            'id', 'room', 'room_number', 'competitor_name',
            'date', 'price', 'source_url', 'last_checked',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PricingInsightsSerializer(serializers.Serializer):
    """Serializer for pricing insights response"""
    
    room_id = serializers.IntegerField()
    room_number = serializers.CharField()
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    recommended_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    occupancy_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    demand_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_competitor_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    price_change_percentage = serializers.DecimalField(max_digits=6, decimal_places=2)
    season = serializers.CharField()
    model_confidence = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
