"""
Pricing and demand analysis models

Per deliverables:
- DELIVERABLES-Task3-ResearchCompletion.md
- DELIVERABLES-Task4-SystemArchitecture.md
"""

from django.db import models
from django.utils import timezone


class PricingHistory(models.Model):
    """
    Historical pricing data for ML algorithmic analysis and dynamic pricing.
    Per Task 4: PricingHistory entity
    Per Task 3: Dynamic Pricing Algorithm requirements
    """
    SEASON_CHOICES = (
        ('low', 'Low Season'),
        ('medium', 'Medium Season'),
        ('high', 'High Season'),
        ('peak', 'Peak Season'),
    )
    
    room = models.ForeignKey(
        'room.Room',
        on_delete=models.CASCADE,
        related_name='pricing_history'
    )
    
    # Date information
    date = models.DateField(db_index=True)
    weekday = models.IntegerField(
        choices=[(i, ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][i]) 
                 for i in range(7)],
        null=True
    )
    
    # Pricing data
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dynamic_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    competitor_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Demand metrics
    occupancy_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Occupancy rate (0-100%)"
    )
    demand_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Demand score (0-100)"
    )
    bookings_count = models.IntegerField(default=0)
    cancellation_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    # Season info
    season = models.CharField(
        max_length=20,
        choices=SEASON_CHOICES,
        default='medium'
    )
    
    # External factors
    external_events = models.CharField(
        max_length=255,
        blank=True,
        help_text="Description of external events affecting demand"
    )
    
    # ML Model metadata
    predicted_by_model = models.BooleanField(default=False)
    model_version = models.CharField(max_length=50, blank=True)
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Individual model predictions (Phase 1 - Pricing Module Redesign)
    ensemble_prediction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Ensemble model price prediction"
    )
    gradient_boosting_prediction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Gradient Boosting model price prediction"
    )
    neural_network_prediction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Neural Network model price prediction"
    )
    linear_regression_prediction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Linear Regression model price prediction"
    )
    
    # Pricing factors breakdown (Phase 1 - Pricing Module Redesign)
    occupancy_impact_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage impact from occupancy"
    )
    seasonal_impact_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage impact from seasonality"
    )
    demand_impact_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage impact from demand"
    )
    competitor_impact_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage impact from competitor pricing"
    )
    
    # Decision tracking (Phase 1 - Pricing Module Redesign)
    price_override_reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="Reason for manual price override"
    )
    override_by_user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='price_overrides',
        help_text="User who overrode AI recommendation"
    )
    ai_recommended_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="AI recommended price at time of creation"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Pricing Histories"
        unique_together = [('room', 'date')]
        indexes = [
            models.Index(fields=['room', '-date']),
            models.Index(fields=['date']),
            models.Index(fields=['room', 'season']),
        ]
    
    def __str__(self):
        return f"{self.room.room_number} - {self.date}"


class DemandForecast(models.Model):
    """
    AI-generated demand forecasts for driving dynamic pricing.
    Per Task 3: Demand prediction component
    """
    room = models.ForeignKey(
        'room.Room',
        on_delete=models.CASCADE,
        related_name='demand_forecasts'
    )
    forecast_date = models.DateField()
    forecast_for_date = models.DateField()  # Date being forecasted
    
    # Forecast metrics
    predicted_occupancy = models.DecimalField(max_digits=5, decimal_places=2)
    predicted_demand_score = models.DecimalField(max_digits=5, decimal_places=2)
    recommended_price = models.DecimalField(max_digits=10, decimal_places=2)
    confidence = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Model info
    model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-forecast_for_date']
        unique_together = [('room', 'forecast_date', 'forecast_for_date')]
        indexes = [
            models.Index(fields=['room', 'forecast_for_date']),
        ]
    
    def __str__(self):
        return f"Forecast {self.room.room_number} for {self.forecast_for_date}"


class CompetitorPrice(models.Model):
    """
    Competitor pricing data for market analysis.
    """
    room = models.ForeignKey(
        'room.Room',
        on_delete=models.CASCADE,
        related_name='competitor_prices'
    )
    competitor_name = models.CharField(max_length=255)
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Source
    source_url = models.URLField(blank=True)
    last_checked = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['room', '-date']),
        ]
    
    def __str__(self):
        return f"{self.competitor_name} - {self.date}: ${self.price}"
