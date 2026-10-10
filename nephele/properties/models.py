"""
Property, TravelAgency, and related models

Per deliverables:
- DELIVERABLES-Task4-SystemArchitecture.md
- tasks/phase-2-development/task-5a-backend-core.md
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Property(models.Model):
    """
    Represents a hotel property/location.
    Per Task 4: Property/Hotel entity
    """
    STAR_RATING_CHOICES = [(i, f"{i} Star") for i in range(1, 6)]
    
    # Basic info
    name = models.CharField(max_length=255, unique=True)
    
    # Location
    location = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Contact
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True, null=True)
    
    # Details
    total_rooms = models.IntegerField(default=0)
    star_rating = models.IntegerField(choices=STAR_RATING_CHOICES, default=3)
    
    # Management
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_properties",
        help_text="Hotel manager responsible for this property"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Properties"
        indexes = [
            models.Index(fields=['city', 'country']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def available_rooms(self):
        """Count available rooms for today"""
        from room.models import Booking
        from datetime import date
        
        today = date.today()
        occupied_rooms = Booking.objects.filter(
            room__property=self,
            check_in_date__lte=today,
            check_out_date__gt=today,
            status__in=['confirmed', 'checked_in']
        ).values_list('room_id', flat=True).distinct()
        
        total = self.rooms.count()
        available = total - len(set(occupied_rooms))
        return max(0, available)


class TravelAgency(models.Model):
    """
    Travel agency model for managing third-party bookings.
    Per Task 4: Travel Agency entity
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    )
    
    # Basic info
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    # Contact
    contact_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)
    
    # Location
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    
    # Commission
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text="Commission percentage for bookings"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return self.name

        booked_rooms = Booking.objects.filter(
            roomNumber__property=self,
            startDate__lte=today,
            endDate__gt=today
        ).count()
        return total_rooms - booked_rooms


class PropertyAmenity(models.Model):
    """
    Amenities available at a property (WiFi, Pool, Spa, etc.)
    """
    AMENITY_CHOICES = [
        ('wifi', 'WiFi'),
        ('pool', 'Swimming Pool'),
        ('gym', 'Fitness Center'),
        ('spa', 'Spa & Wellness'),
        ('restaurant', 'Restaurant'),
        ('bar', 'Bar/Lounge'),
        ('parking', 'Parking'),
        ('valet', 'Valet Service'),
        ('concierge', 'Concierge'),
        ('business', 'Business Center'),
        ('laundry', 'Laundry Service'),
        ('room_service', '24/7 Room Service'),
        ('housekeeping', 'Housekeeping'),
        ('security', '24/7 Security'),
        ('elevator', 'Elevators'),
        ('accessible', 'Wheelchair Accessible'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='amenities')
    amenity_type = models.CharField(max_length=50, choices=AMENITY_CHOICES)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('property', 'amenity_type')
    
    def __str__(self):
        return f"{self.property.name} - {self.get_amenity_type_display()}"


class PropertyPolicy(models.Model):
    """
    House rules and policies for a property
    """
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='policy')
    
    check_in_time = models.TimeField(default='14:00')
    check_out_time = models.TimeField(default='11:00')
    
    cancellation_policy = models.TextField()
    pet_policy = models.TextField(blank=True)
    smoking_policy = models.TextField(blank=True)
    children_policy = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Property Policies"
    
    def __str__(self):
        return f"Policy for {self.property.name}"
