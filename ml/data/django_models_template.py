"""
NEPHELE Hotel Management System - Task 3 Django Models Template
Generated: February 19, 2026

These models represent the structure of the training datasets in task3-data/.
Copy and adapt these into your Django applications as needed.

Usage: Reference these models when creating CSV importers and ML training pipelines.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Property(models.Model):
    """Hotel property master data"""
    STAR_CHOICES = (
        (3, '3-Star'),
        (4, '4-Star'),
        (5, '5-Star'),
    )
    
    PROPERTY_TYPE_CHOICES = (
        ('luxury_resort', 'Luxury Resort'),
        ('boutique', 'Boutique Hotel'),
        ('business', 'Business Hotel'),
        ('beach_resort', 'Beach Resort'),
    )
    
    property_id = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Greece')
    star_rating = models.IntegerField(choices=STAR_CHOICES)
    total_rooms = models.IntegerField()
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPE_CHOICES)
    founded_year = models.IntegerField()
    manager_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['city', 'name']
        verbose_name_plural = 'Properties'
    
    def __str__(self):
        return f"{self.name} ({self.city})"


class Room(models.Model):
    """Room inventory with features"""
    ROOM_TYPE_CHOICES = (
        ('standard', 'Standard'),
        ('deluxe', 'Deluxe'),
        ('suite', 'Suite'),
        ('family', 'Family'),
        ('penthouse', 'Penthouse'),
    )
    
    VIEW_CHOICES = (
        ('city', 'City View'),
        ('sea', 'Sea View'),
        ('mountain', 'Mountain View'),
        ('garden', 'Garden View'),
        ('standard', 'Standard'),
    )
    
    room_id = models.CharField(max_length=30, unique=True, primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.IntegerField()
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    floor = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    capacity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    view_type = models.CharField(max_length=20, choices=VIEW_CHOICES)
    size_sqm = models.IntegerField()
    base_price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    amenities = models.TextField(help_text="Pipe-separated list of amenities")
    last_renovation = models.IntegerField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['property', 'room_number']
        indexes = [
            models.Index(fields=['property', 'room_type']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"{self.room_id} - {self.get_room_type_display()}"
    
    @property
    def amenity_list(self):
        """Parse amenities into list"""
        return self.amenities.split('|') if self.amenities else []


class Guest(models.Model):
    """Guest profiles and preferences"""
    CUSTOMER_TYPE_CHOICES = (
        ('business', 'Business'),
        ('leisure', 'Leisure'),
        ('family', 'Family'),
        ('couple', 'Couple'),
        ('solo', 'Solo Travel'),
    )
    
    guest_id = models.CharField(max_length=20, unique=True, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES)
    origin_country = models.CharField(max_length=100)
    preferred_room_type = models.CharField(max_length=20, choices=Room.ROOM_TYPE_CHOICES)
    loyalty_member = models.BooleanField(default=False)
    registered_date = models.DateField()
    total_stays = models.IntegerField(default=0)
    average_rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)], default=3.5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-registered_date']
        indexes = [
            models.Index(fields=['customer_type']),
            models.Index(fields=['origin_country']),
            models.Index(fields=['loyalty_member']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.guest_id})"


class Booking(models.Model):
    """Reservation history - CORE TRAINING DATASET"""
    STATUS_CHOICES = (
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No-Show'),
    )
    
    CHANNEL_CHOICES = (
        ('direct_web', 'Direct Website'),
        ('booking_com', 'Booking.com'),
        ('airbnb', 'Airbnb'),
        ('expedia', 'Expedia'),
        ('hotel_com', 'Hotel.com'),
        ('travel_agency', 'Travel Agency'),
        ('corporate', 'Corporate'),
    )
    
    PAYMENT_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    )
    
    booking_id = models.CharField(max_length=30, unique=True, primary_key=True)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    number_of_nights = models.IntegerField(validators=[MinValueValidator(1)])
    booking_channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    nightly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    guests_count = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['check_in_date']),
            models.Index(fields=['guest']),
            models.Index(fields=['status']),
            models.Index(fields=['booking_channel']),
        ]
    
    def __str__(self):
        return f"BK {self.booking_id} - {self.guest} ({self.check_in_date})"
    
    @property
    def lead_time(self):
        """Days between booking and check-in"""
        return (self.check_in_date - self.booking_date).days
    
    @property
    def is_completed(self):
        return self.status == 'completed'


class PricingHistory(models.Model):
    """Daily pricing & occupancy metrics"""
    SEASON_CHOICES = (
        ('winter', 'Winter'),
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall'),
    )
    
    DAY_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    )
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pricing_history')
    date = models.DateField()
    occupancy_rate = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    available_rooms = models.IntegerField()
    occupied_rooms = models.IntegerField()
    average_nightly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    day_of_week = models.CharField(max_length=20, choices=DAY_CHOICES)
    season = models.CharField(max_length=20, choices=SEASON_CHOICES)
    is_holiday = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ('property', 'date')
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['property', 'date']),
            models.Index(fields=['season']),
        ]
        verbose_name_plural = 'Pricing Histories'
    
    def __str__(self):
        return f"{self.property.name} - {self.date} ({self.occupancy_rate:.1%})"


class GuestPreference(models.Model):
    """Guest amenity preferences - TRAINING DATA FOR RECOMMENDATIONS"""
    VIEW_CHOICES = Room.VIEW_CHOICES
    ROOM_TYPE_CHOICES = Room.ROOM_TYPE_CHOICES
    
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='preferences')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='guest_preferences')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    preferred_floor = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    wants_breakfast = models.BooleanField(default=True)
    wants_parking = models.BooleanField(default=True)
    needs_accessibility = models.BooleanField(default=False)
    preferred_view = models.CharField(max_length=20, choices=VIEW_CHOICES)
    min_room_size_sqm = models.IntegerField(default=20)
    willing_to_pay_extra = models.BooleanField(default=False)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['guest']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.guest} -> {self.room} ({self.rating}★)"


class CompetitorPricing(models.Model):
    """Market intelligence - competitor pricing data"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='competitor_prices')
    date = models.DateField()
    competitor_id = models.CharField(max_length=30)
    competitor_name = models.CharField(max_length=200)
    competitor_price = models.DecimalField(max_digits=8, decimal_places=2)
    competitor_available_rooms = models.IntegerField()
    competitor_rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['property', 'date']),
            models.Index(fields=['competitor_id']),
        ]
        verbose_name_plural = 'Competitor Pricing'
    
    def __str__(self):
        return f"{self.property.name} - {self.competitor_name} ({self.date}): €{self.competitor_price}"


# ==============================================================================
# USAGE EXAMPLES FOR ML TRAINING
# ==============================================================================

"""
# Load all training data from database
from django.db.models import F, Sum, Avg
from django.db.models.functions import TruncDate, TruncMonth

# 1. Dynamic Pricing Training Data
training_bookings = Booking.objects.filter(
    status='completed',
    check_in_date__gte='2022-01-01'
).select_related('room', 'guest').values(
    'nightly_rate',
    'occupancy__occupancy_rate',
    'guest__customer_type',
    room_type=F('room__room_type'),
    view=F('room__view_type'),
    lead_time=F('booking_id'),
)

# 2. Recommendation System Training Data
preference_matrix = GuestPreference.objects.filter(
    created_at__gte='2022-01-01'
).values('guest_id', 'room_id', 'rating')

# 3. Analytics Dashboard Setup
daily_metrics = PricingHistory.objects.filter(
    date__gte='2022-01-01'
).values('property__name', 'date').annotate(
    avg_occupancy=Avg('occupancy_rate'),
    avg_rate=Avg('average_nightly_rate'),
    total_revenue=Sum('average_nightly_rate') * Sum('occupied_rooms')
)

# 4. Competitor Analysis
competitor_avg = CompetitorPricing.objects.filter(
    date=date
).values('property').annotate(
    avg_price=Avg('competitor_price'),
    price_stdev=StdDev('competitor_price'),
)
"""
