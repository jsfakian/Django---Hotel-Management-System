from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Property(models.Model):
    """
    Represents a hotel property/location.
    Each hotel can have multiple properties.
    """
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True, null=True)
    
    total_rooms = models.IntegerField(default=0)
    star_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=3)
    
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="managed_properties",
        limit_choices_to={'groups__name': 'manager'}
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Properties"
    
    def __str__(self):
        return self.name
    
    def available_rooms(self):
        """Count available (not booked) rooms for today"""
        from room.models import Room, Booking
        from datetime import date
        
        today = date.today()
        total_rooms = Room.objects.filter(property=self).count()
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
