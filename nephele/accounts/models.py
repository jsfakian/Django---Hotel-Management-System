"""
User, Employee, Role, and Task models

Per deliverables:
- DELIVERABLES-Task4-SystemArchitecture.md (Data Model section)
- tasks/phase-2-development/task-5a-backend-core.md
"""

from django.db import models
from django.contrib.auth.models import User, AbstractUser


class Role(models.Model):
    """
    Custom role model for flexible permission management.
    Per Task 4: Authorization Model (RBAC)
    """
    ROLE_CHOICES = (
        ('admin', 'System Administrator'),
        ('hotel_manager', 'Hotel Manager'),
        ('receptionist', 'Receptionist'),
        ('travel_agent', 'Travel Agent'),
        ('guest', 'Guest'),
        ('employee', 'Employee'),
    )
    
    name = models.CharField(
        max_length=50, 
        unique=True, 
        choices=ROLE_CHOICES,
        help_text="Role name matching Django groups"
    )
    description = models.TextField(blank=True)
    permissions = models.JSONField(
        default=dict, 
        blank=True,
        help_text="JSON object defining role permissions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.get_name_display()


class Guest(models.Model):
    """
    Guest model for managing guest information.
    Per Task 4: Guest entity
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True,
        blank=True,
        related_name='guest_profile'
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Guest preferences for personalization
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Guest preferences for room type, floor, amenities, etc."
    )
    
    # Stats
    number_of_bookings = models.IntegerField(default=0)
    total_nights_stayed = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def num_of_booking(self):
        """Legacy method for backward compatibility"""
        return self.number_of_bookings
    
    def num_of_days(self):
        """Legacy method for backward compatibility"""
        return self.total_nights_stayed


class Employee(models.Model):
    """
    Employee model for hotel staff.
    Per Task 4: Employee entity
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    )
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True,
        blank=True,
        related_name='employee_profile'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    position = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    
    # Reference to property (if assigned to specific property)
    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__first_name']
        indexes = [
            models.Index(fields=['status', 'property']),
        ]
        verbose_name_plural = "Employees"
    
    def __str__(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name} - {self.position}"
        return f"Employee {self.id}"


class Task(models.Model):
    """
    Task model for employee task management.
    Per Task 4: Employee task tracking
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium'
    )
    
    # Optional assignment to booking or property
    booking = models.ForeignKey(
        'room.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    
    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', 'start_time']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_time']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.employee}"


class TravelAgentProfile(models.Model):
    """
    Travel agent profile for managing travel agency representatives.
    Links a User to their associated TravelAgency.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='travel_agent_profile'
    )
    
    travel_agency = models.ForeignKey(
        'properties.TravelAgency',
        on_delete=models.CASCADE,
        related_name='agents'
    )
    
    position = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['travel_agency', 'user__first_name']
        unique_together = [('user', 'travel_agency')]
        indexes = [
            models.Index(fields=['travel_agency', 'is_active']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.travel_agency.name}"
    
    def get_accessible_properties(self):
        """Get properties this agent can book for (via active contracts)"""
        from contracts.models import Contract
        from datetime import date
        
        today = date.today()
        contracts = Contract.objects.filter(
            travel_agency=self.travel_agency,
            status='active',
            start_date__lte=today,
            end_date__gte=today
        )
        return contracts.values_list('property_id', flat=True)
